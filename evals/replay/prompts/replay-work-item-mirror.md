For tasks, projects, epics, teams and milestones, `content` is seeded from `description` when the entity is created. Updating the description afterwards leaves `content` at the old text, so anything reading content, including the search embedding, serves prose the author already replaced.

Make an entity update that changes the description also update content for those five types. An update that sets content explicitly keeps the content it was given, and other entity types are unaffected.
