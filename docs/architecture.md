# Architecture

The contract owns the canonical graph, version roots, proposals, and terminal result records. A client may render maps or import GIS data, but those conveniences are not authoritative. `apply_change` reconstructs the exact target graph from on-chain state and proposal fields, then runs the same report in the validator path.

```text
client proposal -> parent-bound proposal -> deterministic graph simulation
                                      -> GenLayer leader/validator equality
                                      -> APPLIED / REJECTED / STALE / EXPIRED
                                      -> new version root + immutable event
```
