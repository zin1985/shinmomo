# 新桃太郎伝説 runtime opcode 0x1B..0x1E 取得方針と candidate 0x10..0x13 ラベル整理
作成日: 2026-04-26

## 1. 重要な結論

`C4:C8AA` は C4 script VM の `opcode 0x1C` handler。  
`$195E` は `opcode 0x1B..0x1E` が共有する candidate 消費済みmask。

ただし、candidate `0x10..0x13` は「桃太郎」「銀次」などの固定NPC名ではない。  
`$80DA57` が `$1923/$1924` pair から実entity `$192A` へ解決するための **relation candidate key**。

したがって現時点のラベルは以下が安全。

| candidate key | engine label | bit in `$195E` | runtimeで確定すべきもの |
|---:|---|---:|---|
| `0x10` | `candidate_relation_0` | `0x01` | `$192A` entity ID / map / event context |
| `0x11` | `candidate_relation_1` | `0x02` | `$192A` entity ID / map / event context |
| `0x12` | `candidate_relation_2` | `0x04` | `$192A` entity ID / map / event context |
| `0x13` | `candidate_relation_3` | `0x08` | `$192A` entity ID / map / event context |

「ゲーム内ラベル確定」は、runtimeで以下の形で取る。

```text
script_pc / opcode / candidate_key / resolved_entity($192A) / $1958 / map_or_scene_marker
```

---

## 2. opcode family 確定状況

| opcode | handler | 役割 | `$195E` 関与 |
|---:|---|---|---|
| `0x18` | `C4:C85A` | `$1958` を logical object list へspawn | なし |
| `0x19` | `C4:C864` | `$1958` を logical object listからremove | なし |
| `0x1B` | `C4:C86E` | 現在candidateを消費済みにする | set |
| `0x1C` | `C4:C8AA` | 未消費candidateから次候補を探し `$1958` へ入れる | read/skip |
| `0x1D` | `C4:C8F8` | 現在candidateが未消費ならsuccess | test |
| `0x1E` | `C4:C89B` | 4候補すべて消費済みならsuccess | all done |

---

## 3. runtimeで取るべき実script列

### 3-1. dispatcher hook

C4 script VM dispatcher入口候補:

```text
C4:C2D0
```

ここで `[$0F]` から opcode を読んでいる。  
この時点で以下をログする。

| field | 内容 |
|---|---|
| `pc` | CPU PC |
| `script_ptr` | `$0F/$10/$11` |
| `opcode` | `read8([$0F])` |
| `script_bytes` | `[$0F]` から16〜32byte |
| `$1923/$1924` | candidate key pair |
| `$192A/$192B` | resolver結果 |
| `$1957/$1958/$195E/$195F` | predicate result / current candidate / consumed mask |
| `$1620` | current entity |
| `$1569[0..9]` | logical object list |
| `$180A[entity-1]` | hidden/suppressed flag candidate |

### 3-2. handler hook

少なくとも以下で前後ログを取る。

| hook | 意味 |
|---|---|
| `C4:C85A` | opcode 0x18 spawn |
| `C4:C864` | opcode 0x19 remove |
| `C4:C86E` | opcode 0x1B mark consumed |
| `C4:C8AA` | opcode 0x1C find next candidate |
| `C4:C8F8` | opcode 0x1D unconsumed predicate |
| `C4:C89B` | opcode 0x1E all consumed predicate |
| `C4:C357` | success exit, `$1957=1` |
| `C4:C366` | failure exit, `$1957=0` |

---

## 4. candidate `0x10..0x13` のゲーム内ラベル確定手順

### 4-1. 最低限必要なログ

`opcode 0x1C` の実行1回ごとに、以下を1行CSVにする。

```csv
marker,script_ptr,opcode,candidate_key,subkey,resolved_entity,current_candidate,mask_195E,flag_180A_entity,logical_list_1569
```

特に重要なのは以下。

| field | 理由 |
|---|---|
| `candidate_key=$1923` | `0x10..0x13` のどれか |
| `resolved_entity=$192A` | 実際に出るentity ID |
| `$1958` | spawn対象として渡されるID |
| `$1569` | logical listに入ったか |
| map/scene marker | どの場所の候補か |

### 4-2. ラベルの付け方

runtime結果に基づいて以下のようにラベルを決める。

| condition | ラベル例 |
|---|---|
| 同じmapで `0x10` が常に画面内NPC1に解決 | `candidate_relation_0 = nearby_npc_slot_0` |
| party/同行者に解決 | `candidate_relation_N = party_or_companion_slot_N` |
| イベントNPCにのみ出る | `candidate_relation_N = event_actor_slot_N` |
| mapにより変わる | `candidate_relation_N = relation_slot_N` のまま維持 |

現時点では、固定キャラ名を付けるのは危険。

---

## 5. 静的ラベル案

現時点での安全なラベルは以下。

| key | label | 理由 |
|---:|---|---|
| `0x10` | `relation_candidate_slot_0` | 4候補tableの0番目 |
| `0x11` | `relation_candidate_slot_1` | 4候補tableの1番目 |
| `0x12` | `relation_candidate_slot_2` | 4候補tableの2番目 |
| `0x13` | `relation_candidate_slot_3` | 4候補tableの3番目 |

`$80DA57` が `$192A` へ解決してから初めて、NPC/actor/entity IDになる。

---

## 6. Goal 13への反映

今回の静的整理で、Goal 13 は **97%据え置き**。

理由:

- opcode文脈は確定寄り
- candidate keyのエンジンラベルは確定寄り
- ただし、runtimeで具体的entity IDを取るまではゲーム内ラベルを確定できない

runtimeログが取れれば、以下まで更新可能。

| 成果 | Goal 13進捗 |
|---|---:|
| `opcode 0x1B..0x1E` 実script列取得 | 98% |
| `candidate 0x10..0x13 -> resolved_entity` 実測 | 99% |
| 実マップ/イベント名まで紐付け | 100% |

---

## 7. ROM修正観点

この段階で candidate key `0x10..0x13` の意味を固定NPC名と誤認してROM修正するのは危険。

まだ避けるべき修正:

- candidate table `10 11 12 13` の入れ替え
- `$195E` の強制初期化
- `$80DA57` の探索順変更
- `$180A bit7` 判定無効化

引き続き比較的安全なのは、`C1:9474` の通常actor cap変更のみ。
