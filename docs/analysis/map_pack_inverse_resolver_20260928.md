# Map pack inverse resolver — 2026-09-28

Canonical Drive ROM was fetched and revalidated: 2,097,152 bytes, SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98.

## Confirmed

C4:8554 is an inverse resolver from the current 24-bit script pointer in $98/$99/$9A to the CA:C000 master-pack index. It compares those three bytes against consecutive 24-bit CA:C000 entries and, for real pack ids at/after 0x14, stores the resolved pack id to both $126E and $12B4.

This establishes the runtime bridge:

current script pointer -> CA:C000 master entry -> pack id -> $126E/$12B4.

Known local callers include C4:8545, C4:8786 and C4:9BEA. The normal interpreter path around C4:87A2 reaches this resolver through C4:8786.

The common mode-entry path at C0:C9E7 snapshots old $1398 to $139A, copies $1399 to $1398, and dispatches through the documented C0:CA69 state table. Several direct state writers tail-jump to this common path.

## Interpretation

The pack-identity side of the reachability join is now concrete. The remaining blocker is temporal/control-flow linkage: determine which $1399 seed reaches C0:C9E7 before each pack/record-0 execution, then join that state to the $126E/$12B4 pack id.

## Strong hypothesis

Observing or statically tracing $126E/$12B4 together with $1398/$1399 at pack entry should classify most of the 118 unresolved record-0 selectors without per-pack heuristics.

## Unresolved

- caller-to-seed relation for each pack entry;
- multiple reachable states for a pack;
- final 137 primary, 52 immediate secondary and 79 standalone secondary candidates.
