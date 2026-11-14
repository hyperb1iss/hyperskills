Bulk entity creation derives each id from the entity's name and category only. Importing the same entities into a second project produces the same ids, so the second import overwrites the first project's records.

Make the id depend on the project (`project_id` in the entity metadata) when one is given. The same import into the same project must still produce the same id, and different projects must produce different ids.
