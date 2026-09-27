# Consensus

`observe()` calls `_report()` from persisted network and proposal state. The validator rejects unless the leader returned a `gl.vm.Return` whose complete calldata equals an independently recomputed `_report()`. The report includes every decision-bearing field, not just a boolean. Therefore a validator cannot accept a payload-substituted edge or a different parent head.
