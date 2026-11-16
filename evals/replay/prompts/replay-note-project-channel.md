A note added to a task is written with no project id and no memory scope, so nothing gates who can read it. Any member of the organization can read the note body regardless of the project the task belongs to.

A note must carry the `project_id` of its parent task in its metadata. There are two writers, the synchronous add-note path and the queued job that processes a pending add-note, and both need it.
