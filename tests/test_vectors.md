# Verification vectors

1. Create a network, add `zone-a` and `hub-a`, propose `ADD_CONNECTION`, apply it, and assert `APPLIED` plus version 1.
2. Reuse the same proposal ID and assert rejection.
3. Propose a connection to an unknown node and assert rejection.
4. Propose against an old parent version and assert `STALE` at application.
5. Propose `REMOVE_CONNECTION` for an absent edge and assert rejection.
