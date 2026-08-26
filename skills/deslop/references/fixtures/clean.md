# Cache keys

The resolver hashes every declared input and stores output under that hash. On the next run, a matching hash means the task is skipped and its cached output is restored.

A task that does not declare an input will not invalidate when that input changes. This is the most common cause of a stale build, and it is the first thing to check when a build returns output you did not expect from source you know you edited.

Editing a task's command invalidates the entry, because the key covers the resolved definition as well as the inputs. Version v1.2.3 changed that; e.g. before it, an edited command reused the old output. See skills/deslop/SKILL.md for the surface rules.

Two flags matter. `--no-cache` skips the lookup entirely, and `--force` was its old name.
