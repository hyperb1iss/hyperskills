When the embedding provider is down, document search returns nothing for sentence-shaped queries. The embedding failure is soft, the lexical lane finds zero rows, nothing raises, and so the scan fallback that a hard search failure triggers never runs.

Make document search take that same scan fallback when the embedder is down and the direct lanes come back empty. A healthy embedder with a true no-match must still return empty without scanning.
