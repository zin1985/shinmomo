# Shinmomo scheduled-analysis handoff 260510Y

This package preserves the scheduled Shin Momotarou Densetsu analysis outputs discussed on 2026-05-10.

It is intended to be copied into the root of `zin1985/shinmomo` and committed as normal text/data/tool files.

## Start here

- `docs/handoff/HM_260510Y.md`
- `docs/analysis/goals.md`
- `docs/analysis/core_g13.md`
- `docs/analysis/graphics_g13.md`
- `manifest/MANIFEST.md`
- `manifest/EXCLUDED.md`
- `COMMIT_COMMANDS_260510Y.sh`

## Important exclusions

No ROM images, savestates, raw VRAM/OAM/CGRAM dumps, or nested ZIP files are included.



## Development workflow

This repository follows the shared project management flow:

```text
ChatGPT / Work
→ GitHub (single source of truth)
→ GitHub Actions (build / validation / artifact generation)
→ Google Drive (deployment / review / distribution)
```

Project-specific settings live in `project.yml`. The reusable build workflow is based on
`zin1985/project-template` and is kept separate from project-specific commands.

ROM images, savestates, raw VRAM/OAM/CGRAM dumps, and nested archives are never committed.
Local analysis may use a legally obtained ROM, but generated text/data/tool outputs are the
only materials promoted to GitHub and release artifacts.

Drive layout:

```text
Projects/shinmomo/
├─ latest/
│  ├─ shinmomo-analysis.zip
│  ├─ source.zip
│  ├─ CHANGELOG.md
│  └─ build-info.txt
└─ releases/
   └─ <version-or-build>/
```
