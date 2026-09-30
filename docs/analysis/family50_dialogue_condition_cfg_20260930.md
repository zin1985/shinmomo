# Family 0x50 dialogue condition CFG

Updated: 2026-09-30

The ten static actors in `cfg_t04_l008_v2` resolve to 19 dialogue source variants.

Seven records share the conditional prefix:

`A3 65 21 90 80 E1 E7 B3 06`

Existing compact-VM analysis proves that `A3 65` tests WRAM `$1252 bit5`,
`E1` is a boolean zero-test, `E7` is boolean conjunction, `B3` branches
on zero, `B2` is an unconditional relative branch, and `B4` branches on
nonzero.

Opcode `21` uses the `$1923/$1924` relation-key path and `80:DA57`.
Its exact gameplay label remains unresolved and is not guessed.

F50-L005 and F50-L007 add `A3 0B B4 06`, where `A3 0B` tests WRAM
`$1247 bit3`.

Resolved source paths:

- L005: common true -> 0x07; common false + bit3 clear -> 0x08; common false + bit3 set -> 0x09.
- L007: common true -> 0x0C; common false + bit3 clear -> 0x0D; common false + bit3 set -> 0x0E.

The two formerly omitted source selections are:

- `CC:1D80 -> A4 07 -> C8:AD3D`, 55 tokens, SHA-256 `26e507f80bb956f7ec56677e512a8e505b2f64f753524e0d6d1d9000e627e635`.
- `CC:1DC4 -> A4 0C -> C8:AED1`, 93 tokens, SHA-256 `f40b93bc97bd43b9d984c2671ad3da940916aac6648b2da70fee001cd5dd5c13`.

The source-pair catalog, event-source crosslink, actor binding, condition table,
and HTML sequence model now all represent the same 19 family-0x50 variants.
