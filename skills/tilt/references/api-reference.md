# Tiltfile API Contracts

Use the [official API reference](https://docs.tilt.dev/api.html) for complete signatures. This file retains the contracts that commonly cause plausible-looking Tiltfiles to behave incorrectly.

## Build and Watch Boundaries

| Function                                  | Contract to verify                                                                                                     |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `docker_build(ref, context, ...)`         | The image ref must match deployed YAML; watched inputs, build context, and sync paths must agree                       |
| `custom_build(ref, command, deps, ...)`   | Tag the output as `$EXPECTED_REF`, or deliberately use `outputs_image_ref_to`; declaring `deps` is part of correctness |
| `local(command, ...)`                     | Executes during Tiltfile evaluation; does not infer the files read by the command                                      |
| `local_resource(name, cmd=..., deps=...)` | Runs as a tracked resource; specify dependencies for rebuilds and independent parallelism                              |
| `k8s_yaml(helm(...))`                     | Renders chart YAML locally; does not create a Helm-managed release                                                     |
| `filter_yaml(...)`                        | Returns matching and remaining YAML; unpack both values                                                                |

```python
matching, remaining = filter_yaml('all.yaml', kind='Deployment')
k8s_yaml(matching)
```

Relative paths resolve in the context of the Tiltfile defining the resource. Loaded helper files should receive explicit paths resolved by their caller; a helper in `lib/` must not silently reinterpret a repository-root-relative service path.

## Live Update

Current documentation permits one optional `initial_sync()` before fallbacks, then syncs, then commands. Check the installed Tilt version before adding that step. Keep commands after their required syncs. Each conditional `run` trigger must be covered by sync. Putting a dependency file in `fall_back_on` means its change rebuilds the image instead of running a dependency-install live step.

The built-in `restart_container()` supports Docker Compose, not Kubernetes. For Kubernetes, use application hot reload or the `restart_process` extension after checking its runtime prerequisites. A distroless image does not acquire a shell or file-watching utility because a Tiltfile command mentions one.

## Resource and Readiness Contracts

The `resource_deps` relationship establishes startup ordering after the dependency has become ready; it is not a general rebuild DAG. Code generation and consumers need explicit file watches or a build arrangement that guarantees the consumed output is current.

Use `pod_readiness='ignore'` for resources whose readiness is not represented by pods, not to conceal scheduling or controller failure. Inspect discovery selectors and status first.

A local `serve_cmd` becomes a long-running process. Give it a readiness probe that checks the service behavior needed by dependents, and handle process replacement when watched files change.

## CI Settings

```python
ci_settings(
    timeout='30m',
    readiness_timeout='5m',
    k8s_grace_period='10s',
)
```

The Kubernetes grace period allows recovery after a resource starts failing; it is not a pod-deletion timeout. Choose durations from the actual startup/recovery behavior and retain the failing resource's logs.

## Ignore Mechanisms

| Mechanism                    | Watch effects                | Docker context effects        |
| ---------------------------- | ---------------------------- | ----------------------------- |
| `.dockerignore`              | Excludes build inputs        | Excludes sent files           |
| `docker_build(ignore=...)`   | Excludes build inputs        | Excludes sent files           |
| `docker_build(only=...)`     | Limits inputs to named paths | Limits context                |
| `.tiltignore`                | Global watch exclusion       | Does not remove context files |
| `watch_settings(ignore=...)` | Global watch exclusion       | Does not remove context files |

Exclude tests per image build if they are not runtime inputs. A global test-file exclusion can also stop the test resource from rerunning.

## Starlark Boundaries

Use `load()` for helper modules. Python syntax resemblance does not imply Python imports, classes, exception handling, generators, or unrestricted recursion. Keep shell work that can fail or mutate state in an explicit resource when it needs tracked execution. Do not assume a Python builtin or string method exists; verify through the installed Tilt evaluator or supported API.

## Primary Sources

Checked 2026-09-04: [Tiltfile API](https://docs.tilt.dev/api.html), [live-update contract](https://docs.tilt.dev/live_update_reference.html), and [resource dependencies](https://docs.tilt.dev/resource_dependencies.html). Local CLI checked: Tilt 0.37.7. Signature examples are deliberately partial; look up optional parameters when using them.
