# Map mode-state dispatch and $1399 transition catalog — 2026-09-28

## Confirmed

Canonical Drive ROM was re-read this cycle: 2,097,152 bytes, SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98.

C0:CA04 copies $1399 to $1398. C0:CA1A..CA33 indexes the 24-bit table at C0:CA69 by 3 * $1398 and dispatches through 80:ACB4.

| state | routine |
|---:|---|
| 0 | 81:964E |
| 1 | 82:8F1B |
| 2 | 83:B7CD |
| 3 | 86:82E2 |
| 4 | null |
| 5 | 85:CAA3 |
| 6 | 81:E331 |

ROM-wide direct stores to $1399 seed only states 0,1,2,3,5,6. State 4 has no direct writer and exactly corresponds to the null dispatch slot.

Direct writer sites: C0:C9E2=2; C1:9A03=6; C1:E320=2; C1:E327=5; C1:E483=5; C2:9043=1; C3:B7D6=5; C3:E48A=1; C5:CB74=3; C5:CB97=0; C2:8FEE=0; C2:9089=0; C6:8308=0.

The dispatch routines themselves expose transitions: state 1 contains state-0 clears; state 2 seeds state 5; state 3 clears to state 0; state 5 contains state-3/state-0 writes. Therefore $1398/$1399 is a finite mode/state machine, not a boolean normal/special flag.

## Strong hypothesis

Per-record reachability can be solved by tracing callers into these six non-null state entries and propagating direct transition edges, rather than treating all 135 unresolved 0x50 rows as one special-mode bucket.

## Unresolved

- Exact game-facing meaning of states 0,1,2,3,5,6.
- Pack/record reachable-state sets.
- Possible indirect/computed $1399 writers beyond direct absolute stores.
- Final classification of 135 primary 0x50 rows, 50 immediate 0x51 pairs and 77 standalone 0x51 shapes.
