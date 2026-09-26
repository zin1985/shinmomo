# E07-E11 event-seed spacing review

Confirmed from committed A4 callsites: E07 first callsite CC:1DA6, E08 CC:1DCC, E09 CC:1DEA, E10 CC:1DFF, E11 CC:1E10. First-callsite gaps are 38, 30, 21, and 17 bytes. By contrast, paired members inside E07, E08, and E09 are exactly 4 bytes apart. Therefore E07-E11 must remain separate structural seeds; current evidence does not support merging them into one event record.

Strong hypothesis: intervening bytes contain VM condition/branch/action structure.

Unconfirmed: exact record boundaries, opcode ownership, speaker, and runtime reachability.

The specified attachment ROM was not accessible in this runtime; no substitute ROM was used.
