# Agent Sandbox — CRD Field Reference

Complete field surface for all four agent-sandbox CRDs as of `v1alpha1` / release **v0.3.10**. Source of truth: `api/v1alpha1/*.go` and `extensions/api/v1alpha1/*.go` in `kubernetes-sigs/agent-sandbox`.

## API Groups

| Kind | Group | Short name |
|---|---|---|
| `Sandbox` | `agents.x-k8s.io` | — |
| `SandboxTemplate` | `extensions.agents.x-k8s.io` | — |
| `SandboxClaim` | `extensions.agents.x-k8s.io` | — |
| `SandboxWarmPool` | `extensions.agents.x-k8s.io` | `swp` |

All use version `v1alpha1`. **No stable API yet.** Expect field renames across minor releases.

## `Sandbox`

Core CRD. One `Sandbox` → one (or zero) `Pod` + one headless `Service` + zero or more `PersistentVolumeClaim`s.

### Spec

```yaml
spec:
  replicas: 0 | 1                           # default 1
  podTemplate:
    metadata:                               # labels/annotations propagated to Pod
      labels: {}
      annotations: {}
    spec:                                   # full Kubernetes PodSpec
      # runtimeClassName, securityContext, containers[], volumes[],
      # tolerations, affinity, topologySpreadConstraints, etc.
  volumeClaimTemplates:                     # optional; each creates a PVC
    - metadata:
        name: workspace
        labels: {}
        annotations: {}                     # propagated to PVC (KEP-174)
      spec:                                 # standard PersistentVolumeClaimSpec
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 10Gi
        storageClassName: standard
  lifecycle:
    shutdownTime: "2026-04-20T18:00:00Z"    # RFC3339 absolute
    shutdownPolicy: Delete | Retain         # pointer, omitempty. If unset, controller marks status Expired but does NOT delete the Sandbox.
```

**Validation rules:**

- `replicas` must be `0` or `1` (kubebuilder: `minimum=0, maximum=1`). Higher values are rejected by the API server.
- `podTemplate.spec.containers[]` requires at least one container.
- `volumeClaimTemplates[].metadata.name` must be unique within the Sandbox.
- `shutdownPolicy` omitted is **not** equivalent to `Delete`. The controller only cascades deletion when the field is explicitly set to `Delete`. Otherwise the Sandbox persists in `Expired` state until something else deletes it (manual cleanup, owning Claim, etc.).

### Status

```yaml
status:
  replicas: 0 | 1                           # actual
  serviceFQDN: "my-sandbox.default.svc.cluster.local"
  service: "my-sandbox"                     # service name
  labelSelector: "agents.x-k8s.io/sandbox-name-hash=abc123"
  podIPs:                                   # new in v0.3.10; dual-stack-aware
    - "10.0.0.42"
    - "fd00::42"
  conditions:
    - type: Ready
      status: "True" | "False"
      reason: "PodRunning" | "PodPending" | "Suspended"
      lastTransitionTime: ...
      message: ...
```

**Known limitation:** `serviceFQDN` is hardcoded to the `.cluster.local` suffix. Clusters using a custom domain hit [issue #566](https://github.com/kubernetes-sigs/agent-sandbox/issues/566).

### Annotations

| Key | Set by | Meaning |
|---|---|---|
| `agents.x-k8s.io/pod-name` | Sandbox controller | Tracks the adopted pod name (used by claim-adoption flow). Source of regression #611 in v0.3.10 — if the referenced pod is externally deleted, the controller does not fall through to recreation. Workaround: delete the Sandbox CR |
| `agents.x-k8s.io/sandbox-template-ref` | Claim controller | Name of the SandboxTemplate this Sandbox was materialized from |
| `agents.x-k8s.io/controller-first-observed-at` | Claim controller | Observability timestamp |

### Labels

| Key | Meaning |
|---|---|
| `agents.x-k8s.io/sandbox-name-hash` | Hash of Sandbox name (used for stable label selector) |
| `agents.x-k8s.io/claim-uid` | UID of the owning `SandboxClaim` — only present on claim-backed pods |
| `agents.x-k8s.io/warm-pool-sandbox` | Present on warm-pool Sandboxes. **Value is a DNS-label hash of the pool name**, not the literal string `true`. Use this key for existence checks (`Exists`/`DoesNotExist`); match exact values only if you know the pool-name hash. The `SandboxWarmPool.status.selector` is built from this same hashed key/value pair |
| `agents.x-k8s.io/sandbox-template-ref-hash` | Hash of the SandboxTemplate name, used by the managed NetworkPolicy selector |

## `SandboxTemplate`

A reusable blueprint for Sandboxes. The template defines the `podTemplate` and optionally an associated `NetworkPolicy`.

### Spec

```yaml
spec:
  podTemplate:
    metadata: {}
    spec:
      runtimeClassName: gvisor
      automountServiceAccountToken: false          # defaults false here (Kubernetes default is true)
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: runtime
          image: ghcr.io/org/runtime:v1
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: [ALL]

  networkPolicyManagement: Managed | Unmanaged     # default Managed

  networkPolicy:                                   # subset of NetworkPolicySpec
    ingress:                                       # standard NetworkPolicy ingress rules
      - from:
          - podSelector:
              matchLabels:
                app: gateway
    egress:                                        # egress rules; default-deny if Managed and no rules
      - ports:
          - protocol: UDP
            port: 53
          - protocol: TCP
            port: 53
```

**The networkPolicy block is a restricted subset** of `networking.k8s.io/v1 NetworkPolicySpec`. You may only set `ingress` and `egress`. `podSelector` and `policyTypes` are derived by the controller — do not set them.

**`networkPolicyManagement: Unmanaged`** means the controller does not create a NetworkPolicy for this template. You're responsible (e.g., via Cilium CNPs or cluster-wide default-deny). Required for CNIs that don't implement standard NetworkPolicy.

**Per-template sharing:** One NetworkPolicy per SandboxTemplate. Changes propagate to all existing Sandboxes created from it. Cross-sandbox isolation inside a single template is enforced by the `agents.x-k8s.io/claim-uid` label.

### Status

SandboxTemplate has no interesting status — just standard `observedGeneration` and owner references.

## `SandboxClaim`

Declarative request for a Sandbox from a template. Handles warm pool adoption and expiry.

### Spec

```yaml
spec:
  sandboxTemplateRef:
    name: code-interp

  warmpool: none | default | <poolName>            # default "default"

  lifecycle:
    shutdownTime: "2026-04-20T18:00:00Z"
    shutdownPolicy: Delete | DeleteForeground | Retain  # default Delete
```

**`warmpool` values:**

| Value | Behavior |
|---|---|
| `"none"` | Always create a fresh Sandbox (ignore all pools) |
| `"default"` | Match any `SandboxWarmPool` targeting this template; pick ready-first then oldest |
| `"<pool-name>"` | Adopt only from the named pool |

**Shutdown policy deltas between Sandbox and Claim:**

| Policy | On `Sandbox` | On `SandboxClaim` |
|---|---|---|
| `Delete` | Sandbox + children deleted | Claim + Sandbox + children deleted |
| `DeleteForeground` | _(not supported on Sandbox itself)_ | Foreground-cascade delete — finalizers keep the Claim visible during shutdown. v0.3.10+ |
| `Retain` | Child Pod deleted, Sandbox CR kept | Sandbox deleted, Claim kept |

Using `Retain` on a Claim is how you preserve audit/observation state after a session has ended.

### Status

```yaml
status:
  conditions:
    - type: Ready                          # the gate — True means pod answered readiness probe
      status: "True"
      message: ...
  sandbox:
    name: "code-interp-session-abc123"     # lowercase in v0.3.10+; was .Name before
  podIPs:                                  # v0.3.10+; mirrors Sandbox.status.podIPs
    - "10.0.0.42"
```

**Case-sensitive field rename:** v0.2.x used `status.sandbox.Name` (capital N). v0.3.10 changed to `.name`. If you're mid-upgrade, check both. Go client reads `.name` only.

### Labels commonly used

Set by the user on claim metadata, mostly for filtering. Sanitized to valid Kubernetes label values (63 chars, alphanumeric + `-._`).

| Key | Why |
|---|---|
| `<org>/organization-id` | Multi-tenant filtering |
| `<org>/thread-id` | Session correlation |
| `<org>/user-id` | Audit / quota |

## `SandboxWarmPool`

Pre-warmed pool of Sandboxes. Supports the Kubernetes scale subresource, which means HPAs can target it directly.

### Spec

```yaml
spec:
  replicas: 5
  sandboxTemplateRef:
    name: code-interp
```

That is the entire spec as of v0.3.10. Selection strategy for adoption is not pluggable — currently "ready first, then by creation time." Tracked in [issue #491](https://github.com/kubernetes-sigs/agent-sandbox/issues/491) for enhancement.

### Status

```yaml
status:
  replicas: 5                              # total Sandboxes in pool
  readyReplicas: 4                         # ready & adoptable
  selector: "agents.x-k8s.io/warm-pool-sandbox=<hash-of-pool-name>"  # required for HPA scale subresource
```

**Don't hand-craft the selector string.** It uses the DNS-label hash of the pool name as the value, not the pool name itself. Read `SandboxWarmPool.status.selector` at runtime if you need the exact string.

### HPA targeting

Because of the scale subresource and `status.selector`, a `HorizontalPodAutoscaler` can target the pool directly:

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
          value: "0.5"
```

The `agent_sandbox_cold_claims_per_second` name is a rule-derived external metric — the controller itself does not emit it. Create a `prometheus-adapter` rule that computes `sum(rate(agent_sandbox_claim_creation_total{launch_type="cold"}[2m])) by (namespace, warmpool_name)` and exposes it under that name. Without that rule the HPA is inert.

See `references/patterns.md` for the complete prometheus-adapter rule and `behavior` block.

## Controller Flags

Set on the controller Deployment via kustomize patch.

| Flag | Default | Purpose |
|---|---|---|
| `--metrics-bind-address` | `:8080` | Prometheus metrics endpoint |
| `--health-probe-bind-address` | `:8081` | Liveness / readiness probes |
| `--leader-elect` | `true` | Required for Deployment-mode HA (default since v0.2.1) |
| `--leader-election-namespace` | _(auto-detect)_ | Override for leases |
| `--extensions` | `false` | Enable Template / Claim / WarmPool controllers. The `extensions.yaml` release sets this |
| `--enable-tracing` | `false` | Enable OTLP trace export |
| `--enable-pprof` | `false` | Expose CPU profile endpoint (low-sensitivity) |
| `--enable-pprof-debug` | `false` | Expose all pprof endpoints (sensitive — don't enable in prod) |
| `--kube-api-qps` | `-1` (unlimited) | QPS to kube-apiserver |
| `--kube-api-burst` | `10` | Burst QPS |
| `--sandbox-concurrent-workers` | `1` | Sandbox reconciler parallelism |
| `--sandbox-claim-concurrent-workers` | `1` | Claim reconciler parallelism |
| `--sandbox-warm-pool-concurrent-workers` | `1` | WarmPool reconciler parallelism |
| `--sandbox-template-concurrent-workers` | `1` | Template reconciler parallelism |

**Sizing rule of thumb:** total concurrent-workers across all four controllers should not exceed `--kube-api-burst`. Exceeding it causes client-side throttling warnings without improving throughput.

## Metrics

Exposed on the controller's `--metrics-bind-address` (default `:8080/metrics`):

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `agent_sandbox_creation_latency_ms` | Histogram | `namespace`, `launch_type` (`warm\|cold\|unknown`), `sandbox_template` | Sandbox creation → Pod Ready. For warm launches this captures controller-sync overhead only |
| `agent_sandbox_claim_creation_total` | Counter | `namespace`, `sandbox_template`, `launch_type`, `warmpool_name`, `pod_condition` (`ready\|not_ready`) | Total SandboxClaims created. **Rate of this with `launch_type="cold"` is the primary HPA signal** — a rising cold rate means the warm pool is underprovisioned |
| `agent_sandbox_claim_startup_latency_ms` | Histogram | `namespace`, `sandbox_template`, `launch_type` | Time from Claim created to backing Pod Ready |
| `agent_sandbox_claim_controller_startup_latency_ms` | Histogram | `namespace`, `sandbox_template` | Time spent inside the claim reconciler for a fresh claim |
| `agent_sandboxes` | Gauge (custom collector) | `namespace`, `ready_condition`, `expired`, `launch_type`, `sandbox_template` | Point-in-time Sandbox counts by dimension |
| `controller_runtime_reconcile_total` | Counter | _standard_ | Controller-runtime reconcile count |
| `controller_runtime_reconcile_errors_total` | Counter | _standard_ | Controller-runtime reconcile errors |
| `workqueue_depth` | Gauge | _standard_ | Pending reconciles per controller |

Scrape with a `ServiceMonitor` targeting the controller service:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agent-sandbox-controller
  namespace: agent-sandbox-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: agent-sandbox-controller
  endpoints:
    - port: metrics
      interval: 30s
```

## RBAC Surface

The controller's ClusterRole (generated, lives in the `manifest.yaml` release):

| API group | Resources | Verbs |
|---|---|---|
| `agents.x-k8s.io` | `sandboxes`, `sandboxes/status`, `sandboxes/finalizers` | full |
| `extensions.agents.x-k8s.io` | `sandboxclaims`, `sandboxtemplates`, `sandboxwarmpools` (+ `/status`, `/finalizers`) | full |
| _core_ | `pods`, `services`, `persistentvolumeclaims` | full |
| `networking.k8s.io` | `networkpolicies` | full (only used when `networkPolicyManagement: Managed`) |
| `coordination.k8s.io` | `leases` | full (leader election) |
| _core_ | `events` | `create`, `patch` |

**Cluster-scoped RBAC is the only mode supported today.** Namespace-scoped deployment is [#484](https://github.com/kubernetes-sigs/agent-sandbox/issues/484).

## Finalizers

| Finalizer | Owner | Removed when |
|---|---|---|
| `agents.x-k8s.io/sandbox` | Sandbox controller | Children (Pod, Service, PVCs) confirmed deleted |
| `extensions.agents.x-k8s.io/sandboxclaim` | Claim controller | Backing Sandbox cleaned per shutdownPolicy |

If a finalizer is stuck, the usual cause is a child resource whose deletion is blocked (PVC waiting on a volume plugin, pod stuck in terminating with a gVisor runtime bug, etc.). Check the child object before editing finalizers directly.

## Webhooks

**None yet.** There is no mutating or validating webhook shipped with v0.3.10. All validation is at the CRD schema layer (OpenAPI v3 + kubebuilder markers). Issue tracker has requests for validating webhooks to enforce `automountServiceAccountToken: false` — not merged.

## Open Issues That Affect CRD Usage

As of April 2026:

| Issue | CRDs affected | Effect |
|---|---|---|
| [#611](https://github.com/kubernetes-sigs/agent-sandbox/issues/611) | Sandbox | Managed pod deleted externally → controller loops forever. Workaround: delete the Sandbox CR |
| [#587](https://github.com/kubernetes-sigs/agent-sandbox/issues/587) | SandboxClaim | `reconcileExpired` can't find the adopted sandbox, leaks resources on expiry |
| [#566](https://github.com/kubernetes-sigs/agent-sandbox/issues/566) | Sandbox | `status.serviceFQDN` hardcoded `.cluster.local` |
| [#525](https://github.com/kubernetes-sigs/agent-sandbox/issues/525) | Sandbox | Can't distinguish `Suspended` (paused) from `Failed` in status |
| [#527](https://github.com/kubernetes-sigs/agent-sandbox/issues/527) | all | Pod watch amplification causes 409 conflict storms at high concurrency |
| [#594](https://github.com/kubernetes-sigs/agent-sandbox/issues/594) | SandboxClaim | NetworkPolicy DELETE+CREATE on every reconcile, even when unchanged |
| [#612](https://github.com/kubernetes-sigs/agent-sandbox/issues/612) | SandboxTemplate | Auto-recreate pods on template podTemplate drift (currently manual) |

Check the upstream issue tracker before planning work that depends on edge-case behavior.
