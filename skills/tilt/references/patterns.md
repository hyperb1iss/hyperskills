# Tilt Power Patterns

Advanced configuration and operational patterns for real-world Tiltfiles.

## Multi-Service Architecture

### Tiltfile Organization

For projects with 10+ services, split configuration across files and compose with `load()`:

```python
# Root Tiltfile
load('./services/frontend/Tiltfile', 'frontend_resources')
load('./services/backend/Tiltfile', 'backend_resources')
load('./services/infra/Tiltfile', 'infra_resources')

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
standard_service('users', './services/users', 8001)
standard_service('orders', './services/orders', 8002, deps=['users'])
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
for svc in all_services:
    lu = [sync('./' + svc + '/src', '/app/src')] if svc in editable else []
    docker_build('myco/' + svc, './' + svc, live_update=lu)

# Conditional monitoring stack
if cfg.get('with-monitoring', False):
    k8s_yaml('./monitoring/prometheus.yaml')
    k8s_yaml('./monitoring/grafana.yaml')
```

**Runtime changes:** `tilt args frontend api -- --to-edit frontend` reconfigures without restart.

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
    # No restart_container() — framework watches files internally
])
```

### Conditional Dependency Install

```python
docker_build('myco/api', './api', live_update=[
    fall_back_on(['Dockerfile']),
    sync('./api', '/app'),
    run('pip install -r requirements.txt', trigger=['./api/requirements.txt']),
    run('npm install', trigger=['./api/package.json']),
])
```

### Process Restart via entr

For containers without shell-based restart support (distroless, scratch):

```python
# In Dockerfile: CMD echo /tmp/restart | entr -rz /app/server
docker_build('myco/api', './api', live_update=[
    sync('./api/src', '/app/src'),
    run('date > /tmp/restart'),  # Touch trigger file, entr restarts process
])
```

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
# COPY package.json .
# RUN npm install
# COPY . .

# Tilt: use only= to limit context
docker_build('myco/app', '.', only=['src', 'package.json', 'tsconfig.json'])
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
# Global: skip test files, docs, CI config from triggering rebuilds
watch_settings(ignore=[
    '**/*_test.go',
    '**/testdata/**',
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

```
# .tiltignore
*.md
docs/
.github/
**/*_test.go
```

## CI Integration

### tilt ci Mode

`tilt ci` runs Tilt in batch mode: builds all resources, waits for readiness, exits 0 on success.

```python
# Tiltfile CI settings
ci_settings(
    timeout='30m',            # Overall timeout (default 30m, 0 = no timeout)
    readiness_timeout='5m',   # Per-resource readiness timeout
    k8s_grace_period='10s',   # Grace period for pod termination
)
```

### GitHub Actions

```yaml
- name: Setup cluster
  uses: helm/kind-action@v1
- name: Install Tilt
  uses: yokawasa/action-setup-tools@v0.9.0
  with:
    tilt: '0.36.3'
- name: Run Tilt CI
  run: tilt ci -- --profile ci
```

### Conditional CI Behavior

```python
if config.tilt_subcommand == 'ci':
    # Skip dev-only resources in CI
    config.set_enabled_resources(['api', 'worker', 'integration-tests'])
    update_settings(max_parallel_updates=1)  # Conserve CI resources
else:
    # Dev mode: everything enabled
    pass
```

## Programmatic Tilt Interaction

### Scripting with tilt get

```bash
# Check if all resources are ready
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

Load extensions from the community repository:

```python
# v1alpha1 API (recommended)
v1alpha1.extension_repo(name='default', url='https://github.com/tilt-dev/tilt-extensions')
v1alpha1.extension(name='restart_process', repo_name='default', repo_path='restart_process')

# Shorthand (auto-discovers from default repo)
load('ext://restart_process', 'docker_build_with_restart')
```

### Key Extensions

| Extension | Purpose | Import |
|-----------|---------|--------|
| `restart_process` | Restart container process on live update | `load('ext://restart_process', 'docker_build_with_restart')` |
| `helm_remote` | Deploy Helm charts from remote repos | `load('ext://helm_remote', 'helm_remote')` |
| `namespace` | Create namespace if it doesn't exist | `load('ext://namespace', 'namespace_create')` |
| `secret` | Create k8s secrets from local values | `load('ext://secret', 'secret_create_generic')` |
| `configmap` | Create ConfigMaps from files/literals | `load('ext://configmap', 'configmap_create')` |
| `git_resource` | Deploy from a git repo | `load('ext://git_resource', 'git_checkout')` |
| `uibutton` | Add custom buttons to Tilt UI | `load('ext://uibutton', 'cmd_button')` |
| `ko` | Build Go images with ko | `load('ext://ko', 'ko_build')` |
| `pack` | Build with Cloud Native Buildpacks | `load('ext://pack', 'pack')` |
| `dotenv` | Load .env files | `load('ext://dotenv', 'dotenv')` |
| `cancel` | Add cancel buttons to resources | `load('ext://cancel', 'register')` |
| `local_output` | Capture local command output | `load('ext://local_output', 'local_output')` |

### Custom UI Buttons

```python
load('ext://uibutton', 'cmd_button', 'location')

# Add a button to a resource
cmd_button('seed-db',
    argv=['make', 'seed'],
    resource='database',
    icon_name='database',
    text='Seed Database',
)

# Add a global nav button
cmd_button('run-all-tests',
    argv=['make', 'test'],
    location=location.NAV,
    icon_name='check_circle',
    text='Run Tests',
)
```

## Custom Build Patterns

### ko (Go images)

```python
load('ext://ko', 'ko_build')
ko_build('myco/api', './cmd/api', deps=['./cmd/api', './pkg'])
```

### Buildpacks

```python
load('ext://pack', 'pack')
pack('myco/api', path='./api', builder='paketobuildpacks/builder:base')
```

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
