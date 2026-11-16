The graph API's subgraph endpoint walks relationships outward from an entity. It hides nodes the reader may not see, but it still returns the edge that leads to a hidden node, so the response discloses a private row's id on a dangling edge.

Drop an edge when the neighbour on its far end is not visible to the reader, and do not traverse further through that neighbour.
