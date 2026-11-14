Loading an entity from storage strips leading and trailing whitespace from its content, so content such as "  verbatim body\n" does not round-trip. Embedding backfill then treats a hydrated entity as different from the stored one.

Preserve content exactly when hydrating an entity and when building the text behind the stored embedding. Names and descriptions keep their current normalization.
