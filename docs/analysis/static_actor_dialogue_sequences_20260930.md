# Static actor dialogue sequence / page model

Updated: 2026-09-30

## Purpose

This layer exists for the HTML viewer playback path:

`actor click -> event -> conditional dialogue sequence -> page 1 -> page 2 -> ...`

It does not replace `static_actor_event_dialogue_binding_20260930.csv`. It adds the display-order/page layer keyed by actor/event/text pointer.

## Confirmed ROM/source facts

- `0x00` terminates the decoded logical text record.
- `0x01` is an explicit in-record line break.
- `0x7D` / `0x7E` decode as literal `「` / `」` glyphs.
- text source pointer and event source-selection callsite remain separate fields.

## Strong page-boundary candidate

For the recovered family-0x50 dialogue corpus, every quote-delimited `0x7D ... 0x7E` block is at most three explicit lines.

Current recovered F50 coverage:

- 10 static actors.
- 17 event-source variants.
- 16 variants have historical exact-token decode evidence.
- 32 quote-delimited display-page candidates.
- maximum recovered page height: 3 lines.
- zero recovered F50 page candidates exceed 3 lines.

Long dialogue records split naturally into multiple quote-delimited blocks instead of one long text blob. This is strong evidence that these blocks are useful game-window page units for HTML playback.

This is still intentionally labeled `strong_candidate`, not `confirmed_static`, because `0x7D/0x7E` themselves are visible quote glyphs and the exact input-wait routine between blocks has not yet been statically linked.

## Button advance

No ROM-side A/B/button wait handler has yet been closed to the quote-block boundary.

Therefore:

- page ordering is preserved;
- a possible advance between pages is represented;
- the actual input and wait semantics are `unresolved_static`.

The HTML viewer may use these page candidates for playback, but should keep the distinction between reproduced presentation and confirmed controller semantics.

## Conditions and branches

Multiple source selections in one actor event record are kept as separate sequence variants.

They are **not** concatenated.

For F50 records using the `A4 xx / B2 dd / A4 yy` form, the static evidence supports conditional selector structure, but the predicate meaning is still unresolved. The JSON therefore carries `predicate_unresolved_static` instead of inventing story/item/party semantics.

F50-L005 and F50-L007 also retain the known guarded selector subforms `0x07` and `0x0C`.

## Speaker / choices / event continuation

The actor is bound to the event record, but current evidence does not prove a human-readable speaker name for each source. Speaker identity is retained as `actor_bound_speaker_identity_unresolved`.

No choice/menu control has been proven in these recovered source records. Empty `choices` means “not identified statically”, not “the game can never branch here”.

The logical text record ends at `0x00`; what the event VM does after dialogue return remains a separate unresolved event-continuation field.

## Outputs

- `data/npc_display/static_actor_dialogue_sequences_20260930.json`
- `data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv`
- `tools/python/build_static_actor_dialogue_sequences.py`

These are machine-readable inputs for later `world.json` actor.event_refs / actor.dialogue_refs integration.
