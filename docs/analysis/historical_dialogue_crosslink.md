# Historical dialogue crosslink

## Purpose

Reuse retained historical decoder results without reviving the obsolete family-boundary corpus model. The canonical unit remains an evidence-backed `(family, subindex)` usage pair.

## Method

`tools/python/crosslink_historical_dialogue.py` joins `data/dialogue/source_pair_usage_catalog.csv` to three retained v33 decoder CSVs by exact SHA-256 of the logical token sequence.

A historical row is accepted only when:

- the token sequence is non-empty;
- the first token is `0x7D`;
- the final token is `0x00`;
- retained decoder output contains non-empty decoded text;
- SHA-256 exactly equals the current usage-catalog `token_sha256`.

The crosswalk stores metadata only. It does not copy decoded dialogue bodies into a new corpus.

## Result

- 76 historical evidence rows matched.
- 21 unique current usage pairs matched.
- 21 unique token hashes matched.
- matched families: `0x4E`, `0x4F`, `0x50`.
- `0x4F:00` and `0x4F:01` were already known dialogue.
- 19 additional pairs were visibility-unknown in the base catalog and now have strong historical dialogue evidence.
- base unknown visibility remains 2,225 in the immutable usage catalog; applying the overlay reduces the unresolved set to 2,206.

## Interpretation

Exact token-stream identity is stronger than a text-shape heuristic, but it is not fresh runtime visibility proof. Therefore the 19 recovered pairs are classified as `strong_dialogue_historical`, not `confirmed_dialogue`.

This also validates the corrected overlapping-entry source model: useful historical dialogue evidence can be reattached without restoring the discarded 7,877-record family-boundary interpretation.

## Outputs

- `tools/python/crosslink_historical_dialogue.py`
- `data/dialogue/historical_decode_crosswalk.csv`
- `data/dialogue/historical_decode_crosswalk_summary.json`

## Next use

Classify the remaining 2,206 pairs by display/event/runtime provenance, then join runtime observations back to `(family, subindex, token_sha256)`.
