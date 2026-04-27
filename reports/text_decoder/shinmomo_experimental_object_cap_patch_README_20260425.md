# 新桃太郎伝説 object cap 実験用IPSパッチ

## ファイル

- `shinmomo_experimental_normal_actor_cap3_lighten.ips`
  - 通常actor capを 4 -> 3 にする処理軽減テスト用
- `shinmomo_experimental_normal_actor_cap6_expand.ips`
  - 通常actor capを 4 -> 6 にする表示増加テスト用

## 変更箇所

対象は `C1:9474` の通常actor `<0x17` のlogical list投入上限。

### cap3
- file offset `0x019493`: `04 -> 03`
- file offset `0x0194AA`: `04 -> 03`

### cap6
- file offset `0x019493`: `04 -> 06`
- file offset `0x0194AA`: `04 -> 06`

## 注意

これは実験用です。  
candidate table拡張やOAM clip変更はまだ危険なので入れていません。

処理軽減目的ならcap3、表示増加確認ならcap6を別名ROMに当てて比較してください。
