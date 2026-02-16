# Tiltfile API Reference

Complete catalog of Tiltfile built-in functions organized by category.

## Build Functions

### docker_build()

Build a Docker image and auto-inject into Kubernetes resources.

```python
docker_build(
    ref,                     # Image reference (e.g., 'myapp' or 'gcr.io/proj/myapp')
    context,                 # Build context directory
    build_args={},           # Docker build arguments dict
    dockerfile='Dockerfile', # Path to Dockerfile (relative to context)
    dockerfile_contents='',  # Inline Dockerfile string (alternative to file)
    live_update=[],          # List of live update steps
    match_in_env_vars=False, # Also match image ref in env vars
    ignore=[],               # Exclude patterns (dockerignore syntax)
    only=[],                 # Include only these paths (not globs)
    entrypoint=[],           # Override container entrypoint
    target='',               # Multi-stage build target
    ssh='',                  # SSH agent forwarding for builds
    network='',              # Docker build network mode
    secret=[],               # Build secrets
    extra_tag=[],            # Additional image tags
    container_args=[],       # Additional container arguments
    cache_from=[],           # External cache sources
    pull=False,              # Always pull base image
    platform='',             # Target platform (e.g., 'linux/amd64')
    extra_hosts=[],          # Extra /etc/hosts entries
)
```

### custom_build()

Build an image using any external tool. The build command MUST tag the image with `$EXPECTED_REF`.

```python
custom_build(
    ref,                      # Image reference
    command,                  # Build command (shell string)
    deps,                     # List of paths to watch
    tag='',                   # Hardcoded tag override
    disable_push=False,       # Skip pushing to registry
    skips_local_docker=False, # True for non-Docker builders (Buildah, kaniko)
    live_update=[],           # Live update steps
    match_in_env_vars=False,  # Match in env vars
    ignore=[],                # Exclude patterns
    entrypoint=[],            # Override entrypoint
    command_bat='',           # Windows-specific command
    outputs_image_ref_to='',  # File where script writes image ref
    image_deps=[],            # Other image refs this depends on
    env={},                   # Environment variables for build command
    dir='',                   # Working directory for build command
)
```

### docker_compose()

Run services via Docker Compose.

```python
docker_compose(
    configPaths,       # Path(s) to docker-compose.yml
    env_file='',       # Env file path
    project_name='',   # Compose project name
    profiles=[],       # Compose profiles to activate
    wait=False,        # Wait for services to be healthy
)
```

### default_registry()

Configure a default image registry for all builds.

```python
default_registry(
    host,                # Registry host (e.g., 'gcr.io/my-project')
    host_from_cluster='',# Registry host as seen from inside cluster
    single_name='',      # Use single image name with different tags
)
```

## Kubernetes Functions

### k8s_yaml()

Load Kubernetes manifests into Tilt.

```python
k8s_yaml(yaml, allow_duplicates=False)
# yaml can be: file path, list of paths, Blob from helm()/kustomize()/local()
```

### k8s_resource()

Configure how Tilt manages a Kubernetes resource.

```python
k8s_resource(
    workload,                # Resource name (matches workload from k8s_yaml)
    new_name='',             # Rename the resource in Tilt UI
    port_forwards=[],        # List of port forwards (str or port_forward())
    extra_pod_selectors=[],  # Additional label selectors for pod matching
    trigger_mode=None,       # TRIGGER_MODE_AUTO or TRIGGER_MODE_MANUAL
    resource_deps=[],        # Resources that must be ready first
    objects=[],              # Non-workload objects to attach (e.g., ConfigMaps)
    auto_init=True,          # Start automatically on tilt up
    pod_readiness='',        # 'wait' (default), 'ignore', or 'connection'
    links=[],                # URLs shown in Tilt UI
    labels=[],               # UI grouping labels
    discovery_strategy='',   # How Tilt discovers pods for this resource
)
```

### k8s_custom_deploy()

Custom deploy command (not YAML-based).

```python
k8s_custom_deploy(
    name,                    # Resource name
    apply_cmd,               # Shell command to apply (must output YAML to stdout)
    delete_cmd,              # Shell command to delete
    deps=[],                 # File dependencies
    image_selector='',       # Image ref to inject
    live_update=[],          # Live update steps
    apply_dir='',            # Working dir for apply
    apply_env={},            # Env vars for apply
    container_selector='',   # Container name to target
    image_deps=[],           # Image dependencies
)
```

### helm()

Render a Helm chart to YAML. Returns a Blob for use with `k8s_yaml()`.

```python
helm(
    pathToChartDir,    # Path to Helm chart
    name='',           # Release name
    namespace='',      # Target namespace
    values=[],         # Values file paths
    set=[],            # Individual value overrides ('key=value')
    kube_version='',   # Kubernetes version for template rendering
    skip_crds=False,   # Skip CRD installation
)
```

### kustomize()

Render Kustomize overlays. Returns a Blob.

```python
kustomize(pathToDir, kustomize_bin='', flags=[])
```

### filter_yaml()

Filter YAML by labels, name, namespace, kind, or api_version. Returns matching objects.

```python
filter_yaml(yaml, labels=None, name='', namespace='', kind='', api_version='')
```

### k8s_kind()

Register a custom Kubernetes resource type.

```python
k8s_kind(kind, api_version='', image_json_path=[], image_object=None, pod_readiness='')
```

### Context Functions

```python
k8s_context()                        # Returns current k8s context name
k8s_namespace()                      # Returns current k8s namespace
allow_k8s_contexts(contexts)         # Whitelist allowed contexts (safety check)
```

## Local Functions

### local_resource()

Define a local command or server as a Tilt resource.

```python
local_resource(
    name,                     # Resource name
    cmd='',                   # Build/task command (runs to completion)
    deps=[],                  # File paths that trigger re-execution
    trigger_mode=None,        # TRIGGER_MODE_AUTO or TRIGGER_MODE_MANUAL
    resource_deps=[],         # Resources that must be ready first
    ignore=[],                # Exclude patterns
    auto_init=True,           # Start automatically
    serve_cmd='',             # Server command (runs continuously)
    cmd_bat='',               # Windows-specific command
    serve_cmd_bat='',         # Windows-specific serve command
    allow_parallel=False,     # Allow parallel execution with other local resources
    links=[],                 # URLs shown in Tilt UI
    labels=[],                # UI grouping labels
    env={},                   # Env vars for cmd
    serve_env={},             # Env vars for serve_cmd
    readiness_probe=None,     # Probe for serve_cmd readiness
    dir='',                   # Working directory for cmd
    serve_dir='',             # Working directory for serve_cmd
)
```

### local()

Execute a shell command during Tiltfile evaluation. Returns a Blob.

```python
local(command, quiet=False, command_bat='', echo_off=False, env={}, dir='', stdin='')
```

**Gotcha:** `local()` does NOT automatically watch the files it reads. Pair with `watch_file()` or `read_file()` to establish file dependencies.

## Live Update Steps

Steps are ordered: fall_back_on first, then sync, then run, then restart_container.

```python
fall_back_on(files)                   # Force full rebuild when these files change
sync(local_path, remote_path)         # Copy files to container
run(cmd, trigger=None)                # Run command in container (trigger=files for conditional)
restart_container()                   # Restart the container process
```

**Constraint:** `run()` trigger paths must also be covered by a preceding `sync()` step.

## Configuration Functions

```python
config.define_string('key')           # Define string setting
config.define_string_list('key')      # Define string list setting
config.define_bool('key')             # Define boolean setting
config.define_string('key', args=True)# Positional argument
cfg = config.parse()                  # Parse and return config dict
config.set_enabled_resources(list)    # Set initially enabled resources
config.clear_enabled_resources()      # Disable all resources initially
```

Settings come from `tilt_config.json` (overridden by CLI args `tilt up -- --key value`). Update at runtime with `tilt args -- --key value`.

## File I/O Functions

```python
read_file(path, default=None)         # Read file, return Blob (also establishes watch)
read_json(path, default=None)         # Read and parse JSON file
read_yaml(path, default=None)         # Read and parse YAML file
read_yaml_stream(path, default=None)  # Read multi-document YAML
watch_file(path)                      # Watch file for changes (no read)
listdir(directory, recursive=False)   # List directory contents
```

## Encoding Functions

```python
encode_json(obj)                      # Dict/list -> JSON string
decode_json(json_str)                 # JSON string -> dict/list
encode_yaml(obj)                      # Dict/list -> YAML string
decode_yaml(yaml_str)                 # YAML string -> dict/list
encode_yaml_stream(objs)             # List of dicts -> multi-doc YAML
decode_yaml_stream(yaml_str)         # Multi-doc YAML -> list of dicts
blob(string)                          # Wrap string as Blob type
```

## Settings Functions

```python
update_settings(
    max_parallel_updates=3,           # Concurrent image builds (default 3)
    k8s_upsert_timeout_secs=30,       # Timeout for k8s apply
    suppress_unused_image_warnings=[], # Image refs to suppress warnings for
)

ci_settings(
    k8s_grace_period='',              # Grace period for k8s resource deletion
    timeout='30m',                    # CI timeout (default 30 minutes)
    readiness_timeout='5m',           # Readiness check timeout
)

version_settings(check_updates=True, constraint='') # Version checking
trigger_mode(TRIGGER_MODE_AUTO)       # Default trigger mode for all resources
watch_settings(ignore=[])             # Global file watch ignore patterns
secret_settings(disable_scrub=False)  # Disable secret scrubbing in logs
docker_prune_settings(disable=False, max_age_mins=360, num_builds=0, interval_hrs=1, keep_recent=2)
```

## Control Flow

```python
load(path, *symbols)                  # Import symbols from another Tiltfile
load_dynamic(path)                    # Import and return all globals as dict
fail(msg)                             # Stop execution with error
warn(msg)                             # Emit warning (continues execution)
exit(code=0)                          # Stop execution without error
enable_feature(name)                  # Enable experimental feature
```

## OS Module

```python
os.getcwd()                           # Current working directory
os.getenv(key, default='')            # Get environment variable
os.putenv(key, value)                 # Set environment variable
os.path.abspath(path)                 # Absolute path
os.path.basename(path)                # Base name
os.path.dirname(path)                 # Directory name
os.path.exists(path)                  # Path exists check
os.path.join(path, *paths)            # Join paths
os.path.realpath(path)                # Canonical path
os.path.relpath(targpath, basepath)   # Relative path
os.name                               # OS name ('posix' or 'nt')
os.environ                            # Environment variables dict
```

## Global Variables

```python
config.main_dir          # Directory containing the main Tiltfile
config.main_path         # Full path to the main Tiltfile
config.tilt_subcommand   # 'up', 'ci', or 'down'
sys.argv                 # Tiltfile arguments
sys.executable           # Path to Tilt binary
```

## Ignore Mechanism Comparison

| Mechanism | Scope | Prevents rebuild? | Affects Docker context? |
|-----------|-------|-------------------|------------------------|
| `.dockerignore` | docker_build only | Yes | Yes |
| `.tiltignore` | All resources | Yes | No |
| `ignore=` param | Per-build/resource | Yes | For docker_build: Yes |
| `only=` param | docker_build only | Yes (inverse) | Yes |
| `watch_settings(ignore=)` | Global | Yes | No |

## Starlark Language Notes

**Available:** for loops, if/elif/else, list comprehensions, string formatting (`%` and `.format()`), `*args`/`**kwargs`, nested functions, lambda (limited).

**NOT available:** while loops, try/except, class definitions, recursion, import (use `load()`), set literals (use `set()` function), generators/yield, async/await, with statements.

**Frozen values:** Variables from loaded files are frozen (immutable). Modify by creating new values, not mutating in place.

**Built-in functions:** `abs`, `all`, `any`, `bool`, `dict`, `dir`, `enumerate`, `fail`, `float`, `getattr`, `hasattr`, `hash`, `int`, `len`, `list`, `max`, `min`, `print`, `range`, `repr`, `reversed`, `sorted`, `str`, `tuple`, `type`, `zip`.

**String methods:** `capitalize`, `count`, `endswith`, `find`, `format`, `index`, `isalnum`, `isalpha`, `isdigit`, `islower`, `isspace`, `istitle`, `isupper`, `join`, `lower`, `lstrip`, `partition`, `removeprefix`, `removesuffix`, `replace`, `rfind`, `rindex`, `rpartition`, `rsplit`, `rstrip`, `split`, `splitlines`, `startswith`, `strip`, `title`, `upper`.

**Dict methods:** `clear`, `get`, `items`, `keys`, `pop`, `popitem`, `setdefault`, `update`, `values`.

**List methods:** `append`, `clear`, `extend`, `index`, `insert`, `pop`, `remove`.
