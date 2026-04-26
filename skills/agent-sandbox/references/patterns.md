# Agent Sandbox — Production Patterns

Hard-won patterns for running agent-sandbox under real multi-tenant load. Distilled from upstream examples and the Gradial v2 deployment (which has been running the operator at non-trivial scale since v0.2.x). Refer back when designing new installs, tuning warm pools, or debugging mysterious behavior.

## Warm Pool — Sizing and HPA

The warm pool exists for one reason: make a `SandboxClaim` resolve to a ready Pod in milliseconds instead of the ~1s it takes to schedule and start a fresh pod. Two variables to tune: **baseline size** (what the pool always has) and **burst response** (how the pool grows when demand spikes).

### Baseline sizing

```
baseline_replicas = p50_concurrent_sessions × 1.5
```

1.5× because the adoption window — time between the claim landing and the pod being warm-replacement — needs headroom. If your p50 is 10 concurrent sessions and you set baseline to 10, every claim during a new session spawn will briefly bring the pool to 9 and trigger HPA. Overshoot to 15.

### HPA metric — derive cold-claim rate from the claim-creation counter

The intuitive metric is "free warm pods." It is the wrong metric. When demand rises, free-warm-pods **falls**, which looks like scale-down signal to a naive HPA. The correct signal is the rate of claims forced to cold path because no warm pod was available.

The controller does not expose a ready-made rate metric. It exposes `agent_sandbox_claim_creation_total`, a counter labeled with `launch_type` (`warm | cold | unknown`) and `warmpool_name`. Derive the rate yourself in prometheus-adapter and feed it to the HPA as an **external** metric so the rule doesn't need per-pod scoping.

**Prometheus-adapter rule:**

```yaml
rules:
  external:
    - seriesQuery: 'agent_sandbox_claim_creation_total{namespace!=""}'
      resources:
        overrides:
          namespace: { resource: namespace }
      name:
        matches: "^agent_sandbox_claim_creation_total$"
        as: "agent_sandbox_cold_claims_per_second"
      metricsQuery: |
        sum(rate(<<.Series>>{<<.LabelMatchers>>,launch_type="cold"}[2m])) by (namespace, warmpool_name)
```

HPA targeting the derived rate:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: code-interp-pool
spec:
  scaleTargetRef:
    apiVersion: extensions.agents.x-k8s.io/v1alpha1
    kind: SandboxWarmPool
    name: code-interp-pool
  minReplicas: 3
  maxReplicas: 200
  metrics:
    - type: External
      external:
        metric:
          name: agent_sandbox_cold_claims_per_second
          selector:
            matchLabels:
              warmpool_name: code-interp-pool
        target:
          type: Value
          value: "0.5" # cold claims/sec above this triggers scale-up
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 30
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 10
          periodSeconds: 60
```

The scale-up policy is aggressive (30 pods per 60s) and scale-down is conservative (10 pods per 60s, 5-minute stabilization) because wrong-way scaling during a burst is expensive — cold claims add latency to user-visible requests. Wrong-way scale-up is cheap.

Tune the `value` target against observed cold rates in your own traffic. A target of `0.5` means "scale up when we're doing more than half a cold claim per second against this pool"; set it lower if your p95 tolerance is tighter.

### Spread across availability zones

Warm pool has no built-in topology spread. Pods land wherever the scheduler puts them — often all on one node. Fix via `topologySpreadConstraints` on the `SandboxTemplate`:

```yaml
podTemplate:
  spec:
    topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: agent-sandbox
```

## PodDisruptionBudget — Scope Tightly

The biggest operational footgun. **Do not put a single PDB over both warm-pool and claim-backed pods.** The controller hits a sync race during image rollouts, and ArgoCD's PostSync hooks (e.g., your warm-pool refresh job) block indefinitely on `SyncFailed`.

### Wrong

```yaml
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: agent-sandbox
  maxUnavailable: 1
```

### Right — claim-backed only

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: sandbox-claim-pdb
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: agent-sandbox
    matchExpressions:
      - key: agents.x-k8s.io/claim-uid
        operator: Exists
```

The `agents.x-k8s.io/claim-uid` label is only present on pods adopted by a `SandboxClaim`. Warm pool pods don't have it — and they don't need PDB protection anyway because they're fungible (deleting and re-warming is cheap).

## Warm Pool Refresh — Image Rollouts

When you update a `SandboxTemplate` (new image, new env, changed probe), the controller **does not** delete existing warm pool pods. They stay stuck on the old spec until naturally rotated out via claim adoption. For a busy pool this can take hours.

Solution: an ArgoCD PostSync Job that discovers warm-pool Sandboxes via owner references, then compares each one's pod template against the current `SandboxTemplate` and deletes drifted entries. The controller refills the pool from the updated template on the next reconcile.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: warm-pool-refresh
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      serviceAccountName: warm-pool-refresh
      restartPolicy: OnFailure
      containers:
        - name: refresh
          image: alpine/k8s:1.35.2
          command: [/bin/sh, -c]
          args:
            - |
              set -eu
              POOL=code-interp-pool
              TEMPLATE_NAME=code-interp
              NS=default

              # Pull the template we want every pool Sandbox to match.
              TEMPLATE=$(kubectl -n "$NS" get sandboxtemplate "$TEMPLATE_NAME" -o json | jq -c '.spec.podTemplate')

              # Discover pool Sandboxes by owner reference — the warm pool CR owns every
              # Sandbox it creates. Don't match on the warm-pool-sandbox label value
              # because it's a hash of the pool name, not the literal pool name.
              POOL_UID=$(kubectl -n "$NS" get sandboxwarmpool "$POOL" -o jsonpath='{.metadata.uid}')
              for sbx in $(kubectl -n "$NS" get sandboxes.agents.x-k8s.io -o json \
                            | jq -r --arg uid "$POOL_UID" '.items[] | select(.metadata.ownerReferences[]?.uid == $uid) | .metadata.name'); do

                CURRENT=$(kubectl -n "$NS" get sandbox "$sbx" -o json | jq -c '.spec.podTemplate')

                # Normalize both sides before comparison:
                #   1. Sort lists whose ordering is semantic-free (env, volumes, containers).
                #   2. Strip fields the controller injects on secure-by-default (DNSPolicy=None,
                #      DNSConfig nameservers, automountServiceAccountToken=false) so we don't
                #      flag every pool pod as drifted the moment those land.
                NORMALIZE='
                  (.spec.containers |= sort_by(.name))
                  | (.spec.volumes //= [] | .spec.volumes |= sort_by(.name))
                  | (.spec.containers[].env //= [] | .spec.containers[].env |= sort_by(.name))
                  | del(.spec.dnsPolicy, .spec.dnsConfig, .spec.automountServiceAccountToken)
                '
                NORM_T=$(echo "$TEMPLATE" | jq -S "$NORMALIZE")
                NORM_C=$(echo "$CURRENT"  | jq -S "$NORMALIZE")

                if [ "$NORM_T" != "$NORM_C" ]; then
                  echo "drift: $sbx"
                  kubectl -n "$NS" delete sandbox "$sbx"
                fi
              done
```

**Why owner-reference discovery:** the warm-pool label (`agents.x-k8s.io/warm-pool-sandbox`) stores a DNS-label hash of the pool name, not the pool name itself. Matching on a literal value will miss every pod in the pool. Owner references are stable and don't depend on naming conventions.

**Why normalize injected fields:** the claim controller and warm-pool controller inject `dnsPolicy: None`, `dnsConfig.nameservers: [8.8.8.8, 1.1.1.1]`, and `automountServiceAccountToken: false` when the template isn't opted out of secure-by-default. The source `SandboxTemplate.spec.podTemplate` doesn't carry them. Raw string-compare flags this as drift on every reconcile. Strip them both sides.

**Why compare full `podTemplate`:** an earlier version of this script only diffed the image tag. Missed env var changes (e.g., OTEL endpoint flip), probe tuning, security-context updates. Always compare the full template — after normalization.

## Karpenter Integration

Warm pool pods don't drive CPU or memory metrics enough to trigger Karpenter's standard scale-on-utilization logic. The path that actually works:

1. HPA scales the `SandboxWarmPool` up in response to a rule-derived cold-claim rate (see HPA metric section above)
2. New pods become unschedulable (no room on existing nodes)
3. Karpenter sees unschedulable pods → launches nodes

A NodePool reserved for sandboxes:

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: sandbox
spec:
  template:
    spec:
      nodeClassRef:
        name: sandbox
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: [arm64]
        - key: karpenter.sh/capacity-type
          operator: In
          values: [on-demand] # NOT spot — active tool execution mid-flight
        - key: node.kubernetes.io/instance-type
          operator: In
          values: [m8g.2xlarge, m8g.4xlarge, m8g.8xlarge]
      taints:
        - key: workload-type
          value: sandbox
          effect: NoSchedule
  limits:
    cpu: "2000"
    memory: 4000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 60s
    budgets:
      - nodes: "30%"
  weight: 15
  expireAfter: 2h # force AMI refresh
```

SandboxTemplate sidebar that matches:

```yaml
podTemplate:
  spec:
    tolerations:
      - key: workload-type
        operator: Equal
        value: sandbox
        effect: NoSchedule
    affinity:
      nodeAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
                - key: workload-type
                  operator: In
                  values: [sandbox]
```

**Prefer on-demand capacity.** Sandboxes execute user-visible tool calls — spot interruption mid-tool-call is a failed request that's expensive to retry. The ~30% spot discount doesn't cover the cost of one lost session.

**`expireAfter: 2h` isn't strict recycling.** It's an AMI-rotation hedge. Pair it with a sandbox session TTL roughly equal or shorter, so node expiry never interrupts a live session.

## Network Policy — Worked Examples

### The "egress only to these places" template

```yaml
networkPolicy:
  egress:
    # DNS — always
    - ports: [{ protocol: UDP, port: 53 }, { protocol: TCP, port: 53 }]
    # Platform API callback
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: platform } }
          podSelector: { matchLabels: { app.kubernetes.io/name: api } }
      ports: [{ protocol: TCP, port: 10191 }]
    # Observability (OTLP)
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: o11y } }
          podSelector: { matchLabels: { app.kubernetes.io/name: alloy-edge } }
      ports: [{ protocol: TCP, port: 4317 }]
    # Public internet HTTPS only (no internal cluster IPs)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
              - 169.254.0.0/16 # link-local + metadata
      ports: [{ protocol: TCP, port: 443 }]
  ingress:
    # Platform frontend reaches the sandbox's runtime API
    - from:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: platform } }
      ports: [{ protocol: TCP, port: 8080 }]
```

The `ipBlock` egress rule with an `except:` list is the canonical way to allow public internet while blocking internal cluster IPs. It mirrors the default-deny policy the controller would install if `networkPolicy` were omitted.

### Istio / Datadog / Alloy sidecar rules

If pods run with a sidecar, the sidecar's health-check port needs explicit ingress. Otherwise the sidecar's liveness check fails and the pod goes NotReady with no obvious signal.

```yaml
networkPolicy:
  ingress:
    # Istio sidecar health port
    - from:
        - podSelector: {} # allow from same namespace
      ports: [{ protocol: TCP, port: 15020 }]
    # Datadog APM
    - from:
        - podSelector: {}
      ports: [{ protocol: TCP, port: 8126 }]
```

### CNI compatibility

Standard `NetworkPolicy` is supported by most CNIs but enforcement varies. Before trusting the policy in production, verify:

| CNI              | Default enforcement                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| Calico           | Enforced out of the box                                                                                |
| Cilium           | Enforced; prefer `CiliumNetworkPolicy` for more expressiveness                                         |
| EKS VPC CNI      | **Not enforced unless you enable the Network Policy Agent add-on** and set `enableNetworkPolicy: true` |
| AKS Azure CNI    | Requires `--network-policy azure` or `cilium` at cluster create                                        |
| AKS kubenet      | **Never enforced.** Migrate to Azure CNI Overlay                                                       |
| GKE Dataplane V2 | Enforced                                                                                               |

If the CNI does not enforce NetworkPolicy, set `networkPolicyManagement: Unmanaged` on the template so the controller doesn't create a policy that gives you a false sense of security.

## Hydration — Getting State Into a Fresh Sandbox

A fresh warm pool pod is blank. The application needs to prime it with session state (files, credentials, skill patterns) before the agent runs.

### Pattern: signed bundle URL

1. Claim becomes Ready. Pod is running the runtime (listening on, say, `/configure`).
2. Application backend assembles a bundle (tarball of files + credentials), uploads to object storage (S3 / Supabase / GCS), generates a short-lived signed URL.
3. Backend POSTs the signed URL + a scoped JWT to `/configure` on the sandbox pod via its service FQDN.
4. Runtime fetches, extracts to `/workspace`, reports `phase: ready` on its healthz endpoint.

Why not bake state into the image: image-bake cycle is minutes, hydration cycle is seconds. You want a generic image that gets specialized at claim time.

Why not inject via env vars or ConfigMaps: they can't carry secrets safely, and updating them requires pod restart.

Why a signed URL instead of direct push: decouples bundle size from network policy / pod connectivity. The pod pulls from the storage backend using its normal egress policy.

### Credential bridge

Sandboxes should not have cluster credentials. If the agent needs to call integration APIs (Linear, GitHub, etc.), mint a short-lived JWT at the app layer, bake the integration-specific tokens into that JWT's claims (encrypted), and have a thin bridge service inside the cluster that accepts sandbox JWTs and proxies calls.

```
[sandbox pod] --(sandbox-scoped JWT)--> [bridge svc] --(integration token)--> [external API]
```

This keeps integration tokens out of the sandbox's env, workspace, and network reach.

## Observability

OTLP endpoint is the standard target. Sandbox pods usually emit traces for tool-call execution and logs for runtime events.

```yaml
containers:
  - name: runtime
    env:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://alloy-edge.o11y.svc.cluster.local:4317
      - name: OTEL_SERVICE_NAME
        value: sandbox-runtime
      - name: OTEL_RESOURCE_ATTRIBUTES
        value: $(POD_NAME),$(POD_NAMESPACE)
      - name: POD_NAME
        valueFrom: { fieldRef: { fieldPath: metadata.name } }
      - name: POD_NAMESPACE
        valueFrom: { fieldRef: { fieldPath: metadata.namespace } }
```

Sidecar option — run Alloy or OTel Collector as a sidecar if you need to buffer logs when egress is flaky, but remember sidecar ports need explicit ingress rules in the NetworkPolicy.

## Load Testing

The operator's own `make test-e2e --suite=benchmarks` is the start. For realistic multi-tenant load, drive from outside the cluster:

1. Pre-create N `SandboxTemplate` resources across multiple namespaces to simulate tenants.
2. Fan out from a load-generator pod: create M `SandboxClaim`s per tenant, wait for Ready, POST a `/configure` payload, execute a representative tool call, delete the claim.
3. Measure: p50/p90/p99 time-to-Ready, cold-claim rate, HPA response curve.

Target numbers reported upstream at BURST=1, WARMPOOL=2:

| Percentile | Claim → Ready (warm) |
| ---------- | -------------------- |
| p50        | 654 ms               |
| p90        | 1150 ms              |
| p99        | 2365 ms              |

Above p99 is dominated by kube-apiserver contention. If your numbers are materially worse, check 409 conflicts in the controller logs — that's the symptom of pod-watch amplification ([#527](https://github.com/kubernetes-sigs/agent-sandbox/issues/527)).

## Multi-Tenant Isolation Checklist

A template that's actually safe for untrusted code:

- [ ] `runtimeClassName: gvisor` (or `kata-qemu`)
- [ ] `automountServiceAccountToken: false` (default, but verify)
- [ ] `securityContext.runAsNonRoot: true`, `runAsUser: <nonzero>`
- [ ] Container `securityContext.allowPrivilegeEscalation: false`
- [ ] Container `securityContext.capabilities.drop: [ALL]`
- [ ] Container `securityContext.readOnlyRootFilesystem: true` with emptyDir for writable paths
- [ ] `securityContext.seccompProfile.type: RuntimeDefault`
- [ ] `networkPolicyManagement: Managed` with explicit egress-only-to-required-destinations
- [ ] Resource requests **and limits** set (avoid noisy-neighbor starvation)
- [ ] Namespace with `ResourceQuota` and `LimitRange`
- [ ] Per-tenant namespace if you can afford the control-plane cost, else per-tenant label + NetworkPolicy

Per-tenant namespace is the strong answer. Per-tenant label is the practical answer if you have thousands of tenants.

## Debugging Cheat Sheet

| Symptom                                       | First check                                                                                                                                                                                                                                                                                                                                   |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claim stuck `Ready=False`                     | `kubectl describe sandboxclaim` for conditions; `kubectl logs -n agent-sandbox-system deploy/agent-sandbox-controller` for reconcile errors                                                                                                                                                                                                   |
| Pod keeps restarting                          | Container logs, then probe definitions — startupProbe too aggressive is the #1 cause                                                                                                                                                                                                                                                          |
| Warm pool not scaling                         | Is `prometheus-adapter` exposing your derived cold-rate metric? Check `kubectl get --raw /apis/external.metrics.k8s.io/v1beta1` (external, not custom, because this skill routes through the `type: External` HPA path). Also confirm the controller is emitting `agent_sandbox_claim_creation_total` with `launch_type="cold"` for your pool |
| Pool pods all on one node                     | Missing `topologySpreadConstraints` in the template                                                                                                                                                                                                                                                                                           |
| Sandbox can't reach external service          | `kubectl exec -it <pod> -- nslookup <host>`; then `kubectl get networkpolicy`; then check CNI actually enforces it                                                                                                                                                                                                                            |
| ArgoCD PostSync hook never runs               | PDB blocking with `SyncFailed` — check PDB selector scope                                                                                                                                                                                                                                                                                     |
| Old image keeps running after template update | Run the warm pool refresh Job manually                                                                                                                                                                                                                                                                                                        |
| `409 Conflict` storm in controller logs       | Bump `--kube-api-burst`; if that doesn't help, you're hitting [#527](https://github.com/kubernetes-sigs/agent-sandbox/issues/527)                                                                                                                                                                                                             |
| Claim works locally, fails on one cluster     | Most likely CNI difference — policy enforced in dev, not in prod (or vice versa)                                                                                                                                                                                                                                                              |
