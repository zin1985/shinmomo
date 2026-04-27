# 新桃太郎伝説 candidate scan 4->2 実験用IPS

## 内容

C4:C8AA 系の candidate 0x10..0x13 の4本走査を、0x10..0x11 の2本走査に縮小する実験用。

## 変更箇所

| file offset | 旧 | 新 | 意味 |
|---:|---:|---:|---|
| 0x04C894 | 04 | 02 | C4:C880 candidate match loop |
| 0x04C8A1 | 0F | 03 | C4:C89B all-done mask |
| 0x04C8EA | 04 | 02 | C4:C8AA feeder loop |
| 0x04C91B | 04 | 02 | C4:C8F8 unconsumed check loop |

## 注意

これは安全パッチではなく、処理軽減の挙動確認用です。  
candidate 0x12/0x13 が必要なイベント/NPC表示を壊す可能性があります。

まずはcap3パッチ単体の方が安全です。
