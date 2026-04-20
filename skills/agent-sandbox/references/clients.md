# Agent Sandbox — Client SDK Reference

Two first-party SDKs ship with the operator: Python (`k8s-agent-sandbox` on PyPI) and Go (`sigs.k8s.io/agent-sandbox/clients/go/sandbox`, added in v0.3.10). Both are thin wrappers over the Kubernetes API plus an HTTP/port-forward path to a runtime endpoint inside the sandbox pod. Neither SDK ships the runtime itself — you own the container image and the HTTP surface it exposes.

## Mental Model

```
             ┌── your app / agent loop ──┐
             │                           │
       SDK ──┤ 1. create claim          ──→ K8s API
             │ 2. wait for Ready         │
             │ 3. open transport        ──→ sandbox-router svc (or direct)
             │ 4. run / read / write    ──→ [sandbox pod HTTP endpoint]
             │ 5. close / terminate    ──→ K8s API (delete claim)
             └───────────────────────────┘
```

The SDK talks to Kubernetes for lifecycle and to the pod's runtime endpoint for exec / file ops. Production deployments reach the pod via a **Sandbox Router** service (SPDY-incompatible pods like gVisor need it); dev deployments use `kubectl port-forward` (tunnel mode) or a direct URL.

## Connection Modes

| Mode | When | How |
|---|---|---|
| Gateway | Production. The sandbox-router is fronted by a cloud load balancer (GKE Gateway, AWS ALB, etc.) | SDK discovers Gateway IP, routes through it |
| Tunnel | Dev / CI. No public ingress | SDK runs `kubectl port-forward` under the covers |
| Direct | In-cluster callers (agent orchestrator running inside the same cluster as the sandbox) | SDK hits a supplied URL |

### Router prerequisite

All three modes route through a `sandbox-router-svc` Service running in the cluster, backed by the `sandbox-router-deployment` Deployment. **You must deploy this once** before the SDK works. Upstream ships a reference manifest at `clients/python/agentic-sandbox-client/sandbox-router/sandbox_router.yaml` in the repo.

## Python SDK

`pip install k8s-agent-sandbox` (optional: `[tracing]` for OTLP). Python 3.10+.

### Minimal usage

```python
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import (
    SandboxGatewayConnectionConfig,
    SandboxLocalTunnelConnectionConfig,
    SandboxDirectConnectionConfig,
)

# Production — via Gateway
client = SandboxClient(connection_config=SandboxGatewayConnectionConfig(
    gateway_name="sandbox-gateway",
    gateway_namespace="agent-sandbox-system",
))

# Dev — via port-forward tunnel (the default if no connection_config is supplied)
client = SandboxClient(connection_config=SandboxLocalTunnelConnectionConfig(
    server_port=8888,
))

# In-cluster — direct URL
client = SandboxClient(connection_config=SandboxDirectConnectionConfig(
    api_url="http://sandbox-router-svc.agent-sandbox-system.svc.cluster.local:8080",
))

# Create a sandbox from a template
sbx = client.create_sandbox(
    template="code-interp",
    namespace="default",
)

# Run a command
result = sbx.commands.run("python -c 'print(2+2)'")
print(result.stdout, result.stderr, result.exit_code)

# Read / write files. Paths are plain filenames — the runtime rejects paths
# with directory separators. Put per-file paths on the server side of your
# /run workflow if you need subdirectories.
sbx.files.write("input.txt", b"hello")
data = sbx.files.read("input.txt")
listing = sbx.files.list(".")
exists = sbx.files.exists("input.txt")

# Terminate (deletes the claim)
sbx.terminate()
```

**Config classes live in `k8s_agent_sandbox.models`,** not the top-level package. The keyword argument is `connection_config=`, not `connection=`.

**Claim lifecycle and warmpool policy** aren't exposed via `create_sandbox` keyword arguments in the base client — if you need to set `shutdownTime` or pin to a specific pool, create the `SandboxClaim` yourself via `kubernetes` / `kr8s` and let the client connect to the resulting pod via `SandboxDirectConnectionConfig`.

### Context manager

```python
with client.create_sandbox(template="code-interp", namespace="default") as sbx:
    sbx.commands.run("./setup.sh")
    # auto-terminate on exit
```

### Snapshot / resume (GKE only)

GCP Pod Snapshots are supported when the cluster is GKE and the node pool has Pod Snapshot enabled. The snapshot API is **not on the base `Sandbox`** — it's a GKE-specific extension. Use the `SandboxWithSnapshotSupport` subclass from `k8s_agent_sandbox.gke_extensions.snapshots`.

```python
from k8s_agent_sandbox.gke_extensions.snapshots import SandboxWithSnapshotSupport

# SandboxWithSnapshotSupport is a drop-in replacement for Sandbox;
# construct it the same way your client returns Sandboxes and it
# exposes an additional `.snapshots` property backed by a SnapshotEngine.
sbx = SandboxWithSnapshotSupport(...)   # or obtained from a client extension

snap_uid = sbx.snapshots.create(...)
sbx.terminate()

# Later — restore into a new sandbox and verify it came from the snapshot.
new_sbx = SandboxWithSnapshotSupport(...)
result = new_sbx.is_restored_from_snapshot(snap_uid)
if not result.is_restored:
    raise RuntimeError(result.error_reason)
```

The extension is layered on top of GKE's `podsnapshot.gke.io/v1` `PodSnapshot` + `PodSnapshotManualTrigger` CRDs. Consult the extension's README under `clients/python/agentic-sandbox-client/k8s_agent_sandbox/extensions/README.md` for the authoritative API — the extension surface is still evolving.

Not portable to other clouds: the feature depends on GKE-specific pod-level CRIU integration.

### Known issues (as of April 2026)

- [#622](https://github.com/kubernetes-sigs/agent-sandbox/issues/622): `files.write("docs/foo.txt", ...)` with a non-absolute path writes to `/app/foo.txt`, ignoring the subdirectory. **Always pass absolute paths.**
- `commands.run("cd /some/dir")` does not persist the working directory between calls. Each `run()` is a fresh shell. Pass explicit working dir via `cwd=` keyword or chain commands with `&&`.
- [#574](https://github.com/kubernetes-sigs/agent-sandbox/issues/574): `k8s_helper.py` ignores explicit failure conditions on the claim and waits the full 180s timeout. Fail-fast logic requires reading conditions yourself until fixed upstream.

## Go SDK

`go get sigs.k8s.io/agent-sandbox/clients/go/sandbox`. Go 1.22+. Released in v0.3.10.

### Interface

```go
type Handle interface {
    Open(ctx context.Context) error
    Close(ctx context.Context) error
    Disconnect(ctx context.Context) error     // close transport, keep claim
    Run(ctx context.Context, cmd string, opts ...Option) (*Result, error)
    Read(ctx context.Context, path string, opts ...Option) ([]byte, error)
    Write(ctx context.Context, path string, data []byte, opts ...Option) error
    List(ctx context.Context, path string, opts ...Option) ([]Entry, error)
    Exists(ctx context.Context, path string, opts ...Option) (bool, error)
    IsReady() bool
}

type Info interface {
    ClaimName() string
    SandboxName() string
    PodName() string
    Annotations() map[string]string
}
```

Accept `Handle` in your APIs — the concrete `*Sandbox` type can be swapped for a fake in tests.

### Minimal usage

```go
import "sigs.k8s.io/agent-sandbox/clients/go/sandbox"

s, err := sandbox.New(ctx, sandbox.Options{
    RestConfig:   restConfig,              // from client-go
    TemplateName: "code-interp",
    Namespace:    "default",
})
if err != nil { return err }

if err := s.Open(ctx); err != nil { return err }
defer s.Close(ctx)

res, err := s.Run(ctx, "ls /workspace")
if err != nil { return err }
log.Printf("exit=%d stdout=%q", res.ExitCode, res.Stdout)

// Write takes a plain filename — the SDK validates the argument with
// path.Base and rejects anything that contains directory separators
// (errors like: "path" is not a plain filename (resolved to "base")).
if err := s.Write(ctx, "in.txt", []byte("hello")); err != nil {
    return err
}
data, err := s.Read(ctx, "in.txt")
```

**The Go `Options` struct does not expose SandboxClaim lifecycle or warm-pool policy fields** as of v0.3.10. If you need `shutdownTime` or a specific warm pool, create the `SandboxClaim` out-of-band with `controller-runtime` or `client-go` and point the SDK at the resulting pod via `APIURL`. Track this in the upstream release notes — the field set is likely to grow.

### Connection selection

```go
opts := sandbox.Options{...}

// Production — Gateway
opts.GatewayName = "sandbox-gateway"
opts.GatewayNamespace = "agent-sandbox-system"
opts.GatewayScheme = "https"

// Dev — port-forward tunnel (the default if nothing else is set)
// no fields needed; the SDK falls back to tunnel mode

// In-cluster — direct URL
opts.APIURL = "http://sandbox-router-svc.agent-sandbox-system.svc.cluster.local:8080"
```

### Timeouts

All configurable via `Options`. Defaults:

| Option | Default | What it covers |
|---|---|---|
| `SandboxReadyTimeout` | 180s | Claim → Pod Ready |
| `GatewayReadyTimeout` | 180s | Time to acquire Gateway IP |
| `PortForwardReadyTimeout` | 30s | SPDY tunnel establishment |
| `RequestTimeout` | 180s | Per-call (Run/Read/Write/List) |
| `PerAttemptTimeout` | 60s | Time to receive response headers per HTTP attempt (SDK retries internally) |
| `MaxUploadSize` | 256 MiB | `Write` payload cap |
| `MaxDownloadSize` | 256 MiB | `Read` payload cap |
| `MaxResponseSize` (Run) | 16 MiB | Run output cap |
| `MaxResponseSize` (List/Exists) | 8 MiB | List output cap |

### Error catalog

```go
var (
    ErrNotReady          = errors.New("sandbox transport not ready")
    ErrAlreadyOpen       = errors.New("sandbox already open")
    ErrOrphanedClaim     = errors.New("orphaned claim found from prior session")
    ErrTimeout           = errors.New("timed out waiting for sandbox")
    ErrClaimFailed       = errors.New("claim creation rejected")
    ErrPortForwardDied   = errors.New("port-forward tunnel terminated")
    ErrRetriesExhausted  = errors.New("all HTTP retries failed")
    ErrSandboxDeleted    = errors.New("sandbox deleted before becoming ready")
    ErrGatewayDeleted    = errors.New("gateway deleted during discovery")
)
```

**Critical error handling rules:**

| Error | Semantics | Recovery |
|---|---|---|
| `ErrNotReady` | Transport is dead — port-forward died or router unreachable. Returned by any Run/Read/Write after the monitor detects tunnel death | Call `s.Open(ctx)` to re-establish. Existing claim is preserved |
| `ErrAlreadyOpen` | You called `Open` twice without `Close` in between | Call `Close` or `Disconnect` first |
| `ErrOrphanedClaim` | A prior process left a claim with your configured name. The SDK refuses to adopt silently | Either use a new claim name or explicitly reclaim the old one |
| `ErrTimeout` on `Open` | Pod didn't reach Ready within `SandboxReadyTimeout` | Check template image, probe config, warm pool state |
| `ErrClaimFailed` | The API server rejected the claim (validation error, RBAC) | Error message contains details; fix manifest |
| `ErrPortForwardDied` | Tunnel mode only — the `kubectl port-forward` subprocess died | `s.Open(ctx)` to reconnect. Equivalent to `ErrNotReady` for most callers |
| `ErrSandboxDeleted` | The backing Sandbox was deleted between claim creation and Ready | Usually means someone ran `kubectl delete sandbox` manually or the template changed mid-creation |

The Go SDK runs a **background monitor on the port-forward tunnel** — it detects tunnel death and fails fast with `ErrNotReady` rather than waiting for the next RPC to time out. You don't need to poll.

### Testing — mocking

`Handle` is an interface. Concrete type `*Sandbox`. For unit tests:

```go
type fakeSandbox struct {
    sandbox.Handle
    runs []string
}

func (f *fakeSandbox) Run(ctx context.Context, cmd string, opts ...sandbox.Option) (*sandbox.Result, error) {
    f.runs = append(f.runs, cmd)
    return &sandbox.Result{ExitCode: 0, Stdout: []byte("ok")}, nil
}
```

Avoid relying on internal fields (`*Sandbox` exposes some via `Info` but unexported ones are private). If you need to assert on the claim manifest, use envtest with a real API server instead of reaching inside the type.

### Tracing

OTLP export is wired if you pass a `trace.Tracer`:

```go
import "go.opentelemetry.io/otel"

opts.Tracer = otel.Tracer("my-service")
opts.TraceServiceName = "my-service"
```

The SDK emits spans for `Open`, `Close`, each `Run`/`Read`/`Write`/`List`/`Exists`, and the lifecycle span covering the full Open→Close window.

## Router Deployment

Without the Sandbox Router, none of the SDK modes work. **Don't hand-write the manifest** — apply the upstream one that ships with the Python SDK, which matches the resource names and selector labels the SDKs discover by default.

Authoritative source: `clients/python/agentic-sandbox-client/sandbox-router/sandbox_router.yaml` in the `kubernetes-sigs/agent-sandbox` repo. Resources it creates:

| Resource | Name | Selector / label | Purpose |
|---|---|---|---|
| `Service` | `sandbox-router-svc` | `app: sandbox-router` | Stable ClusterIP on port 8080 |
| `Deployment` | `sandbox-router-deployment` | `app: sandbox-router` | Router pods, 2 replicas, zone-spread |
| `ServiceAccount` / `ClusterRole` / `ClusterRoleBinding` | — | — | Read access to sandboxes / claims / pods |

Typical install:

```sh
kubectl apply -n agent-sandbox-system \
  -f https://raw.githubusercontent.com/kubernetes-sigs/agent-sandbox/${VERSION}/clients/python/agentic-sandbox-client/sandbox-router/sandbox_router.yaml
```

A `Gateway` manifest lives next to it (`gateway.yaml`) for production Gateway mode. The Python SDK's `SandboxGatewayConnectionConfig` discovers the gateway's address; the `SandboxLocalTunnelConnectionConfig` port-forwards to `sandbox-router-svc`. Do not rename the service without also overriding the SDK's connection config defaults.

## SDK Version Compatibility

| SDK version | Works against controller |
|---|---|
| Python 0.1.x | v0.1.0 through v0.1.1 |
| Python 0.2.x | v0.2.1+ |
| Python 0.3.x | v0.3.10+ (required for `warmpool`, `DeleteForeground`) |
| Go 0.3.x | v0.3.10+ (the Go SDK didn't exist before v0.3.10) |

Cross-version operation is **unsupported**. The upstream project tracks SDK + controller together; don't mix.

## Testing Against a Real Cluster

The fastest path:

```sh
# One-time: kind cluster + operator + router
git clone https://github.com/kubernetes-sigs/agent-sandbox
cd agent-sandbox
make deploy-kind

# Your test code uses tunnel mode
# - no Gateway exists in kind
# - port-forward works against the router Service
```

For integration tests, the Go SDK's own `integration_test.go` is a reasonable reference. It uses `envtest` for the API server and a fake runtime container that implements the minimum HTTP surface (`/run`, `/files/{read,write,list,exists}`).

## What Your Runtime Image Must Implement

To be reachable by either SDK, the container in the sandbox pod must expose:

| Path | Method | Purpose |
|---|---|---|
| `/healthz` | GET | Readiness probe. Return 200 when ready to accept `/run`, etc. |
| `/run` | POST | Execute a shell command. Body: JSON with `{command, env, cwd, stdin}`. Response: `{exit_code, stdout, stderr}` |
| `/files/read` | POST | Read a file. Body: `{path}`. Response: `{content}` (base64) |
| `/files/write` | POST | Write a file. Body: `{path, content}` (base64) |
| `/files/list` | POST | Directory listing. Body: `{path}`. Response: `[{name, type, size}]` |
| `/files/exists` | POST | Existence check. Body: `{path}`. Response: `{exists: bool}` |

There is no formal OpenAPI spec yet (tracked for future beta). The Python SDK's client methods are the de facto spec — mirror their request/response shapes.

**Most real deployments write a custom runtime** that also implements application-specific endpoints (e.g., `/configure` for session bootstrap, `/snapshot`, `/restore`). The SDK's core endpoints are a baseline, not a ceiling.
