# shinmomo dialogue mode02/display compact tracer v22

## v21の問題

v21は `src_ptr=C7:02DB` のplain sourceを読み、`桃太郎` や借金台詞を拾いました。  
しかし、画面に出ていたのは「北西のおむすびころりんの穴…」で、別の台詞です。

これは、現在の画面台詞が `$12AA=02` の特殊source側から出ており、v21がそれをskipしたあと、古い/別系統のplain sourceを拾ったためです。

## v22の方針

- `$12AA=02` を現在台詞のsourceとして優先
- `$12AA=02` 直後は plain source を混ぜない
- mode02 raw は「特殊/圧縮source」として短く記録
- 実際に画面へ出ている `$12B2/$12B3/$12C4/$12C5` の表示tokenを低ログ量で蓄積

## 出力

```text
TRACE_DIALOGUE_V22_MODE02_SOURCE
TRACE_DIALOGUE_V22_DISPLAY_LINE
TRACE_DIALOGUE_V22_SKIP
```

見るところ:

```text
raw=
display_decode=
source_state=
```

## 注意

mode02の完全デコードはまだ未対応です。  
v22は「無関係なplain sourceを混ぜない」「表示作業窓から現在画面に近い断片を拾う」ための版です。
