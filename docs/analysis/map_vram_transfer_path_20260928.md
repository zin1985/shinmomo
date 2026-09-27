# Map VRAM transfer path checkpoint

Updated: 2026-09-28

## Confirmed

Static disassembly identifies `C0:A0BA..C0:A150` as a queued VRAM-to-VRAM copy path.

- `C0:A0BA` iterates 6-byte entries beginning at `$7E:2040`.
- Entry words are loaded into DP `$3D`, `$3F`, and `$41`.
- A zero value in the count field terminates the queue.
- `C0:A137` sets DMA source to `$7E:2000` and transfer length from the count with bit0 cleared.
- `C0:A0F0` sets source VMADD from `$3D`, reads VRAM through B-bus register `$39` into the staging buffer, then switches B-bus target to `$18`, sets destination VMADD from `$41`, and writes the staged bytes back to VRAM.

This path moves existing VRAM content and must not be mislabeled as the ROM-side map loader.

## Strong evidence

The queue is a plausible map-transition or scrolling support layer because it performs arbitrary VRAM relocation, but its producers are not yet tied to the stable interior sample.

## Unresolved

1. Writers/producers of the `$7E:2040` queue.
2. Whether entries during the stable interior transition touch VRAM `0x1000` or `0x1800`.
3. The earlier path that initially populates those pages from WRAM or ROM.
4. ROM-side map pointer/table and compression/decoder.

## Next experiment

Trace queue construction and direct `$2118` DMA/write paths outside this copier. If static evidence leaves multiple candidates, use the stable interior transition and retain only derived VMADD/source/caller metadata.
