# Accept Osprey webhooks and support signing secret rotation

Adds Osprey as a second webhook provider at `/hooks/osprey`, handling `transfer.completed` and `transfer.reversed`. Osprey signs with the same `t=...,v1=...` scheme as Kestrel but allows a 600 second clock window and sends its header name in lowercase, so header lookup is now case-insensitive.

Both sides can now rotate secrets without dropped webhooks. `*_SIGNING_SECRET` accepts a comma-separated list, and a request passes if it was signed with any listed secret. A sender in the middle of its own rotation repeats `v1` once per secret, and the parser now keeps every value instead of the last one; a header with more than eight is rejected, which bounds the hashing work an unauthenticated request can cause. `OSPREY_SIGNING_SECRET` is already provisioned in every environment.
