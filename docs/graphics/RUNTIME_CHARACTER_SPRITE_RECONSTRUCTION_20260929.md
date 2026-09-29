# Runtime character sprite reconstruction 2026-09-29

Dynamic capture establishes the active OBJ state from the running game rather than selecting a CHR base by visual guess.

At the sampled frame, WRAM $03A6 = $03. Disassembly shows $03A6 is the OBSEL shadow written to PPU $2101 at 80:A092 and 80:C694. This selects OBJ VRAM base $C000 bytes and size pair 8x8 / 16x16.

The emulator OAM domain did not match the game's DMA source layout. The game-side OAM mirror at WRAM $0EE9 is therefore used as the authoritative pre-DMA object list. Its first visible pieces decode as x/y/tile/attr: (113,112,$08,$12), (112,110,$06,$52), (176,78,$26,$52).

Slots 0 and 1 spatially overlap and reconstruct into a 16x16 runtime cluster. Slot 2 is a separate 16x16 visible object. CHR pixels are decoded from the dynamically captured VRAM and colors from OBJ CGRAM palettes selected by the OAM attr byte.

Raw ROM, VRAM, CGRAM and OAM captures are not committed. Only reconstruction code, documentation, and derived PNGs are stored.
