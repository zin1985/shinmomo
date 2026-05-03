# Metatile graph spec（2026-05-03）

## node

```text
canonical metatile
```

## edge

```text
from,to,direction,frequency
```

Direction:

```text
right
down
left
up
```

## Build

For each decoded map frame:

```text
for each metatile position:
  record horizontal and vertical neighbors
aggregate frequency
```

## Use

- layout reconstruction
- biome / terrain grouping
- edge tile detection
- corner / transition tile detection
