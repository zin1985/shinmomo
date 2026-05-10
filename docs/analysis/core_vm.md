# Core VM / script / event / NPC behavior pointer notes

## Current scheduled-analysis separation

The Goal13 visibility path is separated from VM/script/event semantics.

### VM/script/event responsibilities

```text
entity setup
behavior pointer assignment
script progression
class/macro assignment
configuration updates at frame boundaries
```

### Not observed in Goal13 path

```text
shared_state mutation by VM
append edits by script/event
visibility override by behavior pointer
normalization edits by VM
mid-append reinjection
runtime append regeneration
```

## NPC behavior pointer model

Behavior pointers are treated as downstream execution selectors:

```text
VM/script
→ behavior pointer selection
→ slot loop
→ append formation
→ append traversal
→ JSR($0759)
```

They are not currently considered append eligibility inputs.

## Relation to older handoffs

Earlier March work established major script/VM, selector, ledger, field-extractor, and descriptor lines. The scheduled May Goal13 work does not replace those findings; it isolates a separate runtime visibility/append/OAM line.

Useful older anchors retained:

- `82:FD67` generic field extractor
- `89:9A44` opcode `0x4F` selector field extraction
- `0x41A10..` 8-byte condition table hypothesis
- `0x39850 / 0x39993` target-side blob anchors
- `19D5` as choice layer rather than facility kind
- bank82 local rule / membership engine separation from `398xx/399xx`

## Practical implication

For Goal13 patch work, avoid patching high-level VM/script logic first. The safer search zone is the bank87 slot loop around:

```text
normalize → STA $0799 → LDA $0799 → AND #imm → branch
```

