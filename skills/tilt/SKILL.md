---
name: tilt
description: Use this skill when the user asks to "write a Tiltfile", "configure Tilt", "set up live update", "debug Tilt", "add a resource to Tilt", "optimize Tilt builds", "view Tilt logs", "restart a Tilt resource", or mentions Tiltfile, tilt up, tilt ci, tilt down, live_update, docker_build, custom_build, k8s_resource, local_resource, or Kubernetes local development with Tilt.
---

# Tilt: Kubernetes Dev Toolkit

Tilt automates the local Kubernetes development loop: watch files, build images, deploy to cluster. Configuration lives in a `Tiltfile` (Starlark, a Python dialect). A **resource** bundles an image build + k8s deploy (or a local command) into a single manageable unit.

## CLI Operations

Check `tilt version`, the selected Kubernetes context, and any existing Tilt instance before operations. Explicit requests to start, restart, or stop the intended environment authorize that operation. A read-only diagnosis does not authorize teardown. Editing a Tiltfile can immediately reconfigure a running session, so inspect its watchers and affected resources first.

### Lifecycle

| Task                                            | Command                        |
| ----------------------------------------------- | ------------------------------ |
| Start dev environment                           | `tilt up [-- <Tiltfile args>]` |
| Start with terminal log streaming               | `tilt up --stream`             |
| Start specific resources only                   | `tilt up frontend backend`     |
| Run in CI/batch mode (exits on success/failure) | `tilt ci --timeout 30m`        |
| Stop and delete deployed resources              | `tilt down`                    |
| Change runtime Tiltfile args                    | `tilt args -- --flag value`    |
| Change runtime args (clear all)                 | `tilt args --clear`            |

On Ctrl+C from `tilt up`: K8s and Docker Compose resources **keep running**. Local `serve_cmd` processes stop. Use `tilt down` to clean up.

### Viewing Logs

| Task                         | Command                      |
| ---------------------------- | ---------------------------- |
| Stream all logs              | `tilt logs -f`               |
| Stream logs for one resource | `tilt logs -f <resource>`    |
| Show only errors             | `tilt logs --level error`    |
| Show build logs only         | `tilt logs --source build`   |
| Show runtime logs only       | `tilt logs --source runtime` |
| Logs since 5 minutes ago     | `tilt logs --since 5m`       |
| Last 100 lines               | `tilt logs --tail 100`       |
| JSON output (for parsing)    | `tilt logs --json`           |

### Resource Management

| Task                          | Command                                             |
| ----------------------------- | --------------------------------------------------- |
| List all resources            | `tilt get uiresources`                              |
| Resource status as JSON       | `tilt get uiresources -o json`                      |
| Describe a resource in detail | `tilt describe uiresource <name>`                   |
| Trigger a resource update     | `tilt trigger <resource>`                           |
| Enable a disabled resource    | `tilt enable <resource>`                            |
| Disable a resource            | `tilt disable <resource>`                           |
| Wait for resource readiness   | `tilt wait --for=condition=Ready uiresource/<name>` |

### Inspection & Debugging

| Task                            | Command                          |
| ------------------------------- | -------------------------------- |
| Diagnostics (versions, cluster) | `tilt doctor`                    |
| Inspect file watches            | `tilt get filewatches`           |
| Describe a specific file watch  | `tilt describe filewatch <name>` |
| Full engine state dump (JSON)   | `tilt dump engine`               |
| Full UI state dump              | `tilt dump webview`              |
| Test Docker build as Tilt would | `tilt docker -- build <args>`    |
| List API resource types         | `tilt api-resources`             |

The Tilt API server runs on `localhost:10350` by default. All `tilt get/describe/trigger` commands talk to it.

## Build Strategy Selector

| Situation                                | Function                                     | Key detail                                 |
| ---------------------------------------- | -------------------------------------------- | ------------------------------------------ |
| Standard Dockerfile                      | `docker_build(ref, context)`                 | Watches context dir, auto-injects into k8s |
| Custom toolchain (Bazel, ko, Buildpacks) | `custom_build(ref, cmd, deps)`               | Must tag with `$EXPECTED_REF` env var      |
| Non-Docker builder (Buildah, kaniko)     | `custom_build(..., skips_local_docker=True)` | Builder handles push independently         |
| Docker Compose services                  | `docker_compose(configPaths)`                | Manages compose lifecycle                  |
| Helm charts                              | `k8s_yaml(helm('./chart'))`                  | Renders locally, deploys to cluster        |
| Kustomize overlays                       | `k8s_yaml(kustomize('./overlay'))`           | Renders locally, deploys to cluster        |

## Live Update Decision Tree

Live update replaces full image rebuilds with in-place container file syncs, seconds instead of minutes.

| Step                      | Purpose                                                           | Ordering                                                                          |
| ------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `initial_sync()`          | Optional full sync when a container is first observed or restarts | First, when supported and requested                                               |
| `fall_back_on(files)`     | Force full rebuild when these files change                        | After optional initial_sync, before sync                                          |
| `sync(local, remote)`     | Copy changed files into running container                         | After fall_back_on                                                                |
| `run(cmd, trigger=files)` | Execute command in container (e.g., install deps)                 | After sync                                                                        |
| `restart_container()`     | Docker Compose container restart only                             | Last step; use application reload or the restart_process extension for Kubernetes |

```python
docker_build('myapp', '.', live_update=[
    fall_back_on(['requirements.txt']),
    sync('./src', '/app/src'),
])
```

**Coverage matters:** Unwatched files do nothing. Watched build inputs outside the sync set require a rebuild; fallback paths deliberately choose that rebuild. A live update needs an existing container. Verify one sync change and one fallback change rather than assuming every source edit follows the same route.

## Resource Configuration

```python
# Kubernetes resource with port forwarding and dependencies
k8s_resource('frontend',
    port_forwards=['3000:3000'],
    resource_deps=['api', 'database'],
    labels=['web'],
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Local resource (build tool, test runner, code generator)
local_resource('codegen',
    cmd='make generate',
    deps=['./proto'],
    labels=['tools'],
)

# Local server (runs continuously)
local_resource('storybook',
    serve_cmd='npm run storybook',
    deps=['./src/components'],
    allow_parallel=True,
    readiness_probe=probe(http_get=http_get_action(port=6006)),
)
```

**Parallelism:** Local resources run serially by default. Set `allow_parallel=True` for independent resources. Image builds default to 3 concurrent, adjust with `update_settings(max_parallel_updates=N)`.

**Dependencies:** `resource_deps` gates on first-ever readiness only, once a dependency is ready once, dependents unlock permanently for that session.

## Debugging Flow

```text
Service crashing?     → tilt logs -f <resource> --source runtime
Build failing?        → tilt logs -f <resource> --source build
                        tilt docker -- build <args>  (uses Tilt's Docker environment; supply the build flags)
Wrong files rebuild?  → tilt get filewatches
                        tilt describe filewatch <name>
                        Check .tiltignore, watch_settings(ignore=), ignore= param
Force a rebuild?      → tilt trigger <resource>
Resource stuck?       → tilt describe uiresource <name>
                        Check resource_deps chain
                        For CRDs: inspect controller status and pod discovery first
General diagnostics?  → tilt doctor
Full state dump?      → tilt dump engine | jq .
```

## Top 10 Pitfalls

| Pitfall                                           | Fix                                                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `local()` calls don't track file deps             | Wrap with `read_file()` or add `watch_file()`                                                                                           |
| Live update paths outside docker_build context    | Ensure sync local paths fall within context dir                                                                                         |
| Local resources block each other                  | Set `allow_parallel=True` on independent resources                                                                                      |
| `resource_deps` doesn't re-gate on updates        | It only checks first-ever readiness, not current version                                                                                |
| Starlark has no while/try-except/class/recursion  | Use for loops, `fail()` for errors, dicts for state                                                                                     |
| `.tiltignore` doesn't affect Docker build context | Use `.dockerignore` to exclude from both rebuild triggers AND context                                                                   |
| Custom image output cannot be located             | Tag with `$EXPECTED_REF`, or deliberately configure `outputs_image_ref_to`                                                              |
| `run()` trigger files not in a `sync()` step      | Trigger paths must also be covered by a sync step                                                                                       |
| First launch has no running container             | Live update requires a container; verify startup/build separately                                                                       |
| CRD resource never ready                          | Inspect scheduling/controller conditions and pod discovery; ignore pod readiness only when pods are not the resource's readiness signal |

## Additional Resources

### Reference Files

For detailed API signatures and advanced patterns, consult:

- **`references/api-reference.md`**: Focused Tiltfile API contracts organized by failure mode, Starlark language notes, ignore mechanism comparison
- **`references/patterns.md`**: Multi-service architectures, environment config, CI integration, performance optimization, programmatic Tilt interaction, extension ecosystem

## Anti-Patterns

| Anti-Pattern                                  | Fix                                                                                                       |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Re-asking after an explicit lifecycle request | Use existing authorization for the named environment; confirm only an unresolved destructive target       |
| Treating `tilt ci` as read-only validation    | CI mode executes commands and deploys resources; use the intended test environment                        |
| An invalid live-update partition              | Choose rebuild or synchronized install for each dependency file; do not put the same change on both paths |
| Debugging from Kubernetes YAML only           | Inspect `uiresources`, file watches, and logs                                                             |
| Using `local()` for watched shell work        | Use `local_resource` with explicit `deps`                                                                 |

## Verification

Inspect the active resource graph and file watches before changing live-update paths. Exercise a source edit, a dependency change, and a failure/recovery case in the intended environment. Preserve evidence of which route ran (sync, command, image rebuild, or deploy), not only the final ready state. A successful Tiltfile evaluation cannot establish that a live update reaches the container.

Documentation and CLI checked 2026-09-04 (Tilt 0.37.7). Source contracts live in [api-reference.md](references/api-reference.md).

## What This Skill is NOT

- Not a Kubernetes primer.
- Not an expansion of the user's requested environment or lifecycle scope.
- Not a substitute for reading `tilt doctor` and resource logs.
