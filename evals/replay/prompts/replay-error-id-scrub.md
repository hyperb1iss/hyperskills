API error details that contain a record id reach the caller as the generic "Invalid request data." A message like "Task not found: <uuid>" never arrives, so a 400 or 404 cannot be diagnosed.

Record ids are not secrets: clients send them and mutation receipts return them. Stop the error sanitizer from scrubbing a message only because it contains a UUID. Messages with sensitive content (SQL fragments, filesystem paths, secret words such as token or password) must still be scrubbed, including when they also contain a UUID.
