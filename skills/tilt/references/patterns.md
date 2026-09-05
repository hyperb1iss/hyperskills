# Tilt Power Patterns

Advanced configuration and operational patterns for real-world Tiltfiles.

## Multi-Service Architecture

### Tiltfile Organization

Split configuration when service ownership or repeated patterns justify it; compose with `load()`:

```python
# Root Tiltfile
load('./services/frontend/Tiltfile', 'frontend_resources')
load('./services/backend/Tiltfile', 'backend_resources')
load('./services/infra/Tiltfile', 'infra_resources')
frontend_resources()
backend_resources()
infra_resources()

# Group in UI with labels
k8s_resource('frontend', labels=['web'])
k8s_resource('api', labels=['backend'])
k8s_resource('postgres', labels=['infra'])
k8s_resource('redis', labels=['infra'])
```

### Shared Tiltfile Libraries

```python
# lib/helpers.Tiltfile
def standard_service(name, path, port, deps=[]):
    docker_build('myco/' + name, path, live_update=[
        sync(path + '/src', '/app/src'),
    ])
    k8s_yaml(path + '/k8s.yaml')
    k8s_resource(name,
        port_forwards=[str(port) + ':' + str(port)],
        resource_deps=deps,
        labels=['services'],
    )

# Root Tiltfile
load('./lib/helpers.Tiltfile', 'standard_service')
standard_service('users', os.path.join(config.main_dir, 'services/users'), 8001)
standard_service('orders', os.path.join(config.main_dir, 'services/orders'), 8002, deps=['users'])
```

## Environment-Based Configuration

### User-Configurable Tiltfiles

```python
# Define settings
config.define_string_list('to-run', args=True)
config.define_string_list('to-edit')
config.define_bool('with-monitoring')
cfg = config.parse()

# tilt_config.json (checked into repo as defaults)
# {"to-run": ["frontend", "api"], "to-edit": ["frontend"]}

# Select resources
resources = cfg.get('to-run', ['frontend', 'api', 'worker'])
config.set_enabled_resources(resources)

# Conditional live update only for services being edited
editable = cfg.get('to-edit', [])
all_services = ['frontend', 'api', 'worker']
for svc in all_services:
    lu = [sync('./' + svc + '/src', '/app/src')] if svc in editable else []
    docker_build('myco/' + svc, './' + svc, live_update=lu)

# Conditional monitoring stack
if cfg.get('with-monitoring', False):
    k8s_yaml('./monitoring/prometheus.yaml')
    k8s_yaml('./monitoring/grafana.yaml')
```

**Runtime changes:** `tilt args -- frontend api --to-edit frontend` reconfigures without restart (match the arguments defined by this Tiltfile).

### Preset Service Groups

```python
config.define_string('profile')
cfg = config.parse()

profiles = {
    'minimal': ['api', 'postgres'],
    'frontend': ['api', 'frontend', 'postgres'],
    'full': ['api', 'frontend', 'worker', 'postgres', 'redis', 'monitoring'],
}

profile = cfg.get('profile', 'minimal')
config.set_enabled_resources(profiles.get(profile, profiles['minimal']))
```

## Advanced Live Update Patterns

### Hot Reload (No Restart Needed)

For frameworks with built-in hot reload (React, Next.js, Flask debug mode):

```python
docker_build('myco/frontend', './frontend', live_update=[
    sync('./frontend/src', '/app/src'),
    sync('./frontend/public', '/app/public'),
    # The framework watches files internally
])
```

### Conditional Dependency Install

```python
docker_build('myco/api', './api', live_update=[
    fall_back_on(['./api/Dockerfile']),
    sync('./api', '/app'),
    run('cd /app && pip install -r requirements.txt', trigger=['./api/requirements.txt']),
    run('cd /app && npm ci', trigger=['./api/package.json', './api/package-lock.json']),
])
```

### Kubernetes Process Restart

Use the application's file watcher when available. Otherwise, inspect and load the maintained `restart_process` extension. Verify its wrapper and runtime requirements against the image before copying an example. A shell pipeline using `entr` cannot run in a distroless image without explicitly supplying those programs.

A process restart must preserve signal delivery and shutdown behavior. Test a source edit, a failed reload, and a subsequent correction; a one-time startup success does not prove the update loop works.

### Monorepo with Selective Context

```python
docker_build('myco/api', '.', dockerfile='services/api/Dockerfile',
    only=['services/api', 'packages/shared', 'packages/types'],
    live_update=[
        sync('./services/api/src', '/app/src'),
        sync('./packages/shared/src', '/app/node_modules/@myco/shared/src'),
    ],
)
```

## Performance Optimization

### Build Caching

```python
# Layer ordering: deps first, code last
# Dockerfile:
# COPY package.json package-lock.json .
# RUN npm ci
# COPY . .

# Tilt: use only= to limit context
docker_build('myco/app', '.', only=['src', 'package.json', 'package-lock.json', 'tsconfig.json'])
```

### Parallel Updates

```python
# Increase concurrent builds (default 3)
update_settings(max_parallel_updates=10)

# Allow independent local resources to run in parallel
local_resource('lint', cmd='npm run lint', deps=['./src'], allow_parallel=True)
local_resource('typecheck', cmd='tsc --noEmit', deps=['./src'], allow_parallel=True)
```

### Ignore Patterns

```python
# Global: ignore only files irrelevant to every watched resource
watch_settings(ignore=[
    'docs/**',
    '.github/**',
])

# Per-build: skip non-essential files from Docker context
docker_build('myco/api', '.', ignore=[
    '**/*_test.go',
    '**/testdata',
    'README.md',
    '.git',
])
```

### .tiltignore

Place in the same directory as the Tiltfile. Uses `.dockerignore` syntax. Prevents rebuilds but does NOT affect Docker build context.

```text
# .tiltignore
*.md
docs/
.github/
```

## CI Integration

### tilt ci Mode

`tilt ci` runs Tilt in batch mode: builds all resources, waits for readiness, exits 0 on success.

```python
# Tiltfile CI settings
ci_settings(
    timeout='30m',            # Overall timeout (default 30m, 0 = no timeout)
    readiness_timeout='5m',   # Per-resource readiness timeout
    k8s_grace_period='10s',   # Recovery window after resource failure
)
```

### CI Environment

Install the repository's pinned Tilt version and create the intended disposable Kubernetes context before `tilt ci`. Preserve logs and snapshots on failure. CI mode executes Tiltfile commands and deploys workloads, so it is not a safe parser-only check of an unfamiliar Tiltfile.

Keep independent builds parallel. Investigate shared CPU, memory, registry, or filesystem contention before changing concurrency; a fixed serial setting is not a general CI optimization.

### Conditional CI Behavior

```python
if config.tilt_subcommand == 'ci':
    # Skip dev-only resources in CI
    config.set_enabled_resources(['api', 'worker', 'integration-tests'])
else:
    # Dev mode: everything enabled
    pass
```

## Programmatic Tilt Interaction

### Scripting with tilt get

```bash
# Inspect resource runtime status (task completion also needs update status)
tilt get uiresources -o json | jq '.items[] | {name: .metadata.name, status: .status.runtimeStatus}'

# Wait for a specific resource
tilt wait --for=condition=Ready --timeout=120s uiresource/api

# Get resource names
tilt get uiresources -o name

# Watch for status changes
tilt get uiresources -w -o json
```

### Log Monitoring

```bash
# Stream JSON logs for parsing
tilt logs --json -f | jq 'select(.level == "error")'

# Filter by resource and source
tilt logs -f api --source runtime --since 5m
```

### Dynamic Resource Management

```bash
# Disable expensive resources when not needed
tilt disable monitoring grafana prometheus

# Re-enable when debugging
tilt enable monitoring

# Trigger rebuild after external change
tilt trigger api
```

## Port Forwarding Patterns

```python
# Simple
k8s_resource('api', port_forwards='8080')

# Explicit mapping
k8s_resource('api', port_forwards=['8080:8080', '9090:9090'])

# Named with UI links
k8s_resource('api', port_forwards=[
    port_forward(8080, 8080, name='API'),
    port_forward(9090, 9090, name='Metrics'),
])

# Custom links (no port forward, just UI link)
k8s_resource('api', links=[
    link('http://localhost:8080/docs', 'API Docs'),
    link('http://localhost:8080/health', 'Health'),
])
```

## Extension Ecosystem

Load a maintained extension only for a required capability:

```python
load('ext://restart_process', 'docker_build_with_restart')
```

Inspect the extension's Tiltfile and README at the revision the project resolves. Pin the extension repository when reproducibility matters. Extension loads execute code, so an API-name catalog is not evidence that a symbol, its arguments, or its shell prerequisites still match.

The [extension repository](https://github.com/tilt-dev/tilt-extensions) supplies process restart, remote Helm, custom buttons, configuration helpers, and builder integrations. Keep the required example with the project rather than copying unrelated extension setup.

## Custom Build Patterns

Use the maintained builder extension when it supplies the required image contract; otherwise make the custom builder's output explicit.

### Bazel

```python
custom_build(
    'myco/api',
    'bazel run //api:image -- --norun && docker tag bazel/api:image $EXPECTED_REF',
    deps=['./api', './proto'],
)
```

### Skipping local Docker (remote builders)

```python
custom_build(
    'myco/api',
    'buildah bud -t $EXPECTED_REF ./api && buildah push $EXPECTED_REF',
    deps=['./api'],
    skips_local_docker=True,
)
```

## Readiness Probes

### Local Resource Readiness

```python
local_resource('dev-server',
    serve_cmd='npm start',
    readiness_probe=probe(
        http_get=http_get_action(port=3000, path='/health'),
        initial_delay_secs=5,
        period_secs=2,
    ),
)
```

### Custom TCP Probe

```python
local_resource('grpc-server',
    serve_cmd='./server',
    readiness_probe=probe(
        tcp_socket=tcp_socket_action(port=50051),
        period_secs=3,
    ),
)
```

### Exec Probe

```python
local_resource('worker',
    serve_cmd='celery -A app worker',
    readiness_probe=probe(
        exec=exec_action(['celery', '-A', 'app', 'inspect', 'ping']),
        period_secs=10,
        failure_threshold=5,
    ),
)
```

## Migration from Docker Compose

```python
# Simplest migration: pass docker-compose.yml to Tilt
docker_compose('./docker-compose.yml')

# Configure individual services
dc_resource('api',
    trigger_mode=TRIGGER_MODE_AUTO,
    resource_deps=['postgres'],
    labels=['backend'],
)

# Add live update to a compose service
docker_build('myco/api', './api',
    live_update=[sync('./api/src', '/app/src')],
)
```

## Workload-to-Resource Naming

When Tilt auto-detects resources from k8s YAML, customize naming:

```python
def resource_name(id):
    # id.name = workload name from k8s metadata
    # Strip common prefixes
    return id.name.removeprefix('myco-')

workload_to_resource_function(resource_name)
```

## Primary Sources

Checked 2026-09-04: [live update](https://docs.tilt.dev/live_update_reference.html), [CI](https://docs.tilt.dev/ci.html), and [maintained extensions](https://github.com/tilt-dev/tilt-extensions). Extension APIs can evolve independently of Tilt; inspect the loaded revision before using a symbol or argument.
