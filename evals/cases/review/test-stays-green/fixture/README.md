# teamdir

The team directory API: profiles, search, and the service layer behind the HTTP handlers.

## Deployment

Each region runs exactly one teamdir process, and that process serves one request at a time; there are no worker pools or replicas. Regions have separate profile stores and never read each other's profiles.

Every write to the profile store goes through `DirectoryService.update_profile`. There are no background jobs, imports, or admin tools that write to the store directly.

## Development

Run the tests from this directory with `python -m unittest discover -s tests -t .`.
