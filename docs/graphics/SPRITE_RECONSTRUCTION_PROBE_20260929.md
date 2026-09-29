# Character sprite reconstruction probe (2026-09-29)

## Runtime target

Current runtime observation cfg_t01_l001_v1 contains visible slot 02 with raw sprite group 0 and animation state 4.
shinmomo_B2C1_animation_state_scripts_20260425.csv proves group 0 state 4 is a fixed animation selecting frame 5 (05:FF).
The frame-piece catalog identifies frame 5 at C5:1C30 with six pieces.

## Probe

graphics/sprite_reconstruction_probe/group0_state4_frame5_chrbase_probe.png reconstructs the six pieces using the captured VRAM and candidate OBJ CHR bases.
This is a CHR-base discrimination probe, not a final canonical sprite atlas.
No ROM or raw VRAM/CGRAM capture is committed.

## Remaining exactness

The frame selection and piece geometry are structurally proven.
OBJ CHR base/name-select and final OBJ palette still require runtime register/OAM attribution before one candidate can be promoted to canonical.
