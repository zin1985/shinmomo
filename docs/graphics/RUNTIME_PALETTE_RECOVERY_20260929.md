# Runtime palette recovery correction 2026-09-29

The prior black reconstruction used the emulator CGRAM domain, which was not a valid CGRAM image in this remote capture path.

Static execution tracing identifies the game's actual full-CGRAM DMA routine at 80:B3DC. DMA channel 0 is configured with BBAD=$22, source $7E:21C2, length $0200, CGADD=$00, then MDMAEN=$01. Therefore WRAM $7E:21C2..$23C1 is the authoritative game-side 512-byte CGRAM staging buffer immediately before upload.

Runtime capture of WRAM $21C2 produced nonzero OBJ palettes. Recoloring the already-confirmed OAM/VRAM pieces from this buffer produces multicolor sprite output. The first reconstructed pieces use OBJ palette 1 and contain skin, white, blue, brown, gray and other nonzero colors.

This corrects the palette source without changing the observed OAM geometry. Raw WRAM/VRAM captures remain local-only.
