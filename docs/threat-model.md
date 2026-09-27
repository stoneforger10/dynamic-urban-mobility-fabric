# Threat model

Handled: unauthorized network mutation, cross-network proposal reuse, replay, stale parent updates, self-loops, unknown endpoints, duplicate pairs, illegal operation values, and terminal proposal rewrites.

Not handled by design: physical truth, GPS, traffic, capacity measurement, or route quality. Those require external observations and a separate oracle boundary.
