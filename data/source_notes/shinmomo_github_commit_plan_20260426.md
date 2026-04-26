# 新桃太郎伝説 GitHubコミット指示（2026-04-26）

## 前提

GitHubの現行構成は、リポジトリ直下に `data/` と `handover/` があり、`handover/current_master.md` が現在の引継ぎ本体として存在する。今回の成果はこの構成に合わせて入れる。

## 1. コミット方針

### handover

```text
handover/current_master.md
handover/archive/shinmomo_thread_handover_20260426.md
```

`current_master.md` は最新版として上書き。  
同内容を `archive/` にも置き、履歴として残す。

### data

新規ディレクトリを作る。

```text
data/npc_display/
data/weapon_special/
data/runtime_hooks/
data/experimental_patches/
```

理由:

- NPC表示軽減系はCSVとLuaとIPSが多いため `data/` 直下に置くと散らかる
- 武器特殊能力系はGoal 7で独立して伸びるため分離
- runtime hookは今後増える
- IPSは実験用なので明確に隔離する

## 2. コミットするファイル

詳細は `data/thread_20260426_manifest.csv` を参照。

最低限コミット推奨:

```text
handover/current_master.md
handover/archive/shinmomo_thread_handover_20260426.md
data/thread_20260426_manifest.csv

data/npc_display/*.csv
data/weapon_special/*.csv
data/runtime_hooks/*.lua
data/experimental_patches/*.ips
data/experimental_patches/*.md
```

Markdown詳細メモも残すなら、以下も推奨。

```text
data/npc_display/notes/*.md
data/weapon_special/notes/*.md
```

ただし既存リポジトリに `notes/` がないため、まずは `handover/current_master.md` とCSVを優先し、詳細Markdownはarchiveかdata下に置く。

## 3. コミットしないファイル

```text
*.smc
Shin Momotarou Densetsu (J).smc
Shin Momotarou Densetsu (J) (1).smc
```

ROM本体は著作物なのでコミットしない。  
IPSパッチ、CSV、解析メモ、Lua hookだけを置く。

## 4. コマンド例

```bash
git pull

mkdir -p handover/archive
mkdir -p data/npc_display
mkdir -p data/weapon_special
mkdir -p data/runtime_hooks
mkdir -p data/experimental_patches

# handover
cp /path/to/shinmomo_thread_handover_current_master_20260426.md handover/current_master.md
cp /path/to/shinmomo_thread_handover_current_master_20260426.md handover/archive/shinmomo_thread_handover_20260426.md

# manifest
cp /path/to/shinmomo_thread_20260426_data_manifest.csv data/thread_20260426_manifest.csv

# CSV/Lua/IPSはmanifestに従ってコピー

git add handover/current_master.md
git add handover/archive/shinmomo_thread_handover_20260426.md
git add data/thread_20260426_manifest.csv
git add data/npc_display data/weapon_special data/runtime_hooks data/experimental_patches

git commit -m "Update Shinmomo analysis handover and NPC display datasets"
git push
```

## 5. 推奨コミット分割

一括でもよいが、履歴を見やすくするなら2コミット推奨。

### commit 1

```text
Update handover current master
```

対象:

```text
handover/current_master.md
handover/archive/shinmomo_thread_handover_20260426.md
```

### commit 2

```text
Add NPC display and weapon special analysis data
```

対象:

```text
data/thread_20260426_manifest.csv
data/npc_display/
data/weapon_special/
data/runtime_hooks/
data/experimental_patches/
```

## 6. 注意

`experimental_patches` は実験用。  
READMEを必ず同梱し、ROM改造の本線成果として扱わない。
