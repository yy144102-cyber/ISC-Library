# 変数の配置とスコープ（S1〜S13）

---

## 前提: KRL が強制するもの `確定`

選べない部分。作法の議論の外側にある。

| 事実 | 影響 |
|---|---|
| `.src` の最初の `DEF` のみ外部から呼べる。2つ目以降は同一ファイル内ローカル | サブは呼び出し元と同居させるか、別モジュールにするかの二択 |
| **主 `DEF` のローカル変数は、同じファイル内の別 `DEF` からも見えない** | 共有には `.dat` か引数しかない |
| `.dat` の変数は対になる `.src` の全 `DEF` から見える | モジュールレベル |
| `.dat` の値はプログラム終了後も保持される | 状態保持に使えるが、意図せず残る |
| `DEFDAT … PUBLIC` + `GLOBAL` 宣言で他モジュールから参照可 | モジュール分割の前提 |
| `$CONFIG.DAT` はコントローラ全体。ENUM / STRUC の宣言場所 | 触らない（S11） |
| 宣言部と実行部は分かれる。実行文より前に `DECL` を書く | 言語の強制 |

---

## S1. 置き場所の決定手順 `確定`

上から順に当てはめ、最初に該当したところに置く。

```
1. 実行中に値が変化するか              → はい: .src ローカル or 引数
2. オペレータが値を調整するか          → はい: .dat
3. ティーチした点・固定データか        → はい: .dat
4. 他モジュールから参照するか          → .dat PUBLIC + GLOBAL  (要確認)
5. それ以外                            → .src ローカル
```

**「複数の DEF が読むから `.dat`」は理由にならない。** 先に `:OUT` か
`DEFFCT` で返せないかを検討する（S9）。

---

## S2. `.dat` は実行中に変化しないものだけ `確定`

### なぜか

W3D / ISC のコードは `.dat` の `Point[]` を実行時に書き換えている。
UEC は書き換えていない（`.dat` にはティーチ由来の `FDAT` と自動生成の
`LAST_BASIS` しかない）。

**つまり「`.dat` を都度書き換える」は KUKA の作法ではなく、W3D 系に固有の
習慣。** 本来 `.dat` は「ティーチしたもの・固定データ」の置き場所。

導出値を `.dat` に置くと、初期化処理を飛ばしても**前回の値で静かに動いて
しまう**（P4 違反）。ローカルなら未初期化で止まる。

### 例外: ArcTech のデータセットへの代入 `確定`

`WDAT` の Channel などを `.dat` のパラメータから起動時に代入してよい。
宣言の `{ }` には変数を書けない（S10）ため、パラメータを一覧表にするにはこれしか方法がない。
条件は3つ。

1. **最初の動作命令より前**で行う（`TRIGGER` が先行実行で `WDAT` を読むため。M9）
2. **毎回、無条件に**代入する（前回の値に頼らない）
3. 値は **`.dat` のパラメータだけ**から取る

`WDAT` の宣言の上に「ここの値は起動時に上書きされる。編集は一覧表で」と書く。

### 区画

`.dat` は2区画だけ。**「手で編集してはいけないもの」を `.dat` に置かない。**

```
1. TUNING PARAMETERS   operator edits here
2. FIXED DATA          points, taught data
```

### 初期値を必ず書く `確定`

```krl
; NG
DECL E6POS WB_posRetract

; OK
DECL E6POS WB_posRetract = {X 0.0,Y 0.0,Z 700.0,A -90.0,B 0.0,C 0.0,S 18,T 10,E1 0.0,E2 0.0,E3 0.0,E4 0.0,E5 0.0,E6 0.0}
```

全成分を書く。部分初期化は禁止。

**補足**: 一次資料によれば、動作命令の目標位置に未定義の構造体成分が
含まれる場合、その値は 0 として扱われる（絶対値は変化しない）。つまり
部分初期化でも**動きはする**。禁止する理由は P1（読み手に対する暗黙）で
あって、動作の保証ではない。

### 処理部に数値リテラルを書かない `確定`

例外は `0.0` `1.0` `2.0` `4.0` のような**構造的な定数**（`WB_weaveStepMm / 4.0`、
`-2.0 * WB_weaveAmplitudeMm`）のみ。物理量はすべて `.dat` から来る。

根拠: `Radius = 1002.5` を `.src` に直書きし、条件違いでファイルごと
複製した（`CircD2015_10RadiusChange01`）。

---

## S3. 導出値は主 `DEF` のローカル `確定`

`.dat` の初期値はリテラルしか書けない（S10）ので、導出値は実行時計算になる。

**計算は1箇所にまとめる。** 処理部に散らさない。

```krl
DEF WBead_20260924( )
DECL FRAME fwdQuarterRise, fwdHalfFall, revQuarterRise, revHalfFall
   ...
   fwdQuarterRise = {X 0.0,Y 0.0,Z 0.0,A 0.0,B 0.0,C 0.0}
   fwdQuarterRise.Y = WB_weaveStepMm / 4.0
   fwdQuarterRise.X = WB_weaveAmplitudeMm
   ...
```

### 帰結: 途中行からのブロック選択は安全にできない `確定`

導出値がある以上、パラメータを変更して途中から流すと導出値が前回のまま残る。
技術的に回避するより**制限として明記する**。

```krl
; RESTART POLICY
;   Always start from the top.
;   Block selection from a later line skips parameter setup.
```

---

## S4. 状態を作らないで済むなら作らない `確定`

反転フラグを毎周書き換えるより、**インデックスから導出**する方がよい（P3）。

```krl
; NG : state that must be flipped and reset
WB_FlipDir( )

; OK : derived from the layer index
passPlus = WB_firstPassPlus
IF ((layerIdx / 2) * 2) == layerIdx THEN   ; even layer. MOD is not in the
   passPlus = NOT passPlus                 ; 8.7 operator list ( 90-facts )
ENDIF
```

これで「状態を書き換える関数」が不要になる。

---

## S5. 共有サブは外部状態に依存しない `暫定`

`CM_` を付けたサブプログラムは、**引数と自分のローカル変数だけで完結**させる。
呼び出し元の `.dat` 変数を読まない。

違反例（現行 `MotionPar`）:

```krl
CASE #PTPmotion
   PDAT_ACT = PPDAT1      ; <- caller's .dat
   FDAT_ACT = FP1         ; <- caller's .dat
```

暗黙の入力があるため、別モジュールへコピーすると静かに壊れる。

**分割の時期**: 動作確認前の共通化は行わない（P2）。判断は今できるが、
実行は Phase 1 後。それまで `CM_` を同一ファイル内に置き、依存をコメントで
明示する。

```krl
; DEPENDS ON : <list external state here>
;              must be resolved before extracting to a shared module
```

---

## S6. サブプログラムに INI フォールドを残さない `確定`

KUKA のテンプレートは `.src` を作るたびに `;FOLD INI` を挿入し、その中に
`BAS(#INITMOV,0)` が入る。

**サブプログラムに残すと、呼ぶたびに動作パラメータが既定値にリセットされる。**

UEC の `coordinate_ohta` / `arcon_ohta` がこれを残しており、主プログラムが
内側ループの毎周で `$VEL.CP` を設定し直しているのはその対処と読める。

`BAS(#INITMOV,0)` は**主プログラムの起動時に1回だけ**。

---

## S7. 引数で渡す `確定`

グローバルを介した暗黙の結合を避ける。

上限は5個を目安とする（`暫定`）。超えるなら分割を検討する。
`SegCalc(BL, BW, PT, LZ, OX, OY, OZ, DirY)` の8個は多すぎる。

---

## S8. 転送モードは必ず明示する `確定`

```krl
DEF CM_SetCpVel(velMPerSec:IN)
```

- `:IN` = 値渡し（call by value）
- `:OUT` = 参照渡し（call by reference）

**v4.1 は「省略時は `:OUT`」と明記していた。KSS 8.7 のマニュアルは既定を
記述していない。** どちらにせよ明示すれば影響しない。

---

## S9. 値を返す手段 `確定`

`.dat` を経由した受け渡しは禁止。使えるのは2つ。

| 手段 | 条件 |
|---|---|
| `:OUT` 参照渡し | 呼び出し時点で変数が値を持っていること。型が完全一致 |
| `DEFFCT` の戻り値 | 構造体型を返せる（一次資料に `DEFFCT TorqLimitParam …` の例あり） |

`暫定`: 配列を `:IN` で渡せるかは v4.1 では「不可」と明記、KSS 8.7 では
記述なし。配列を扱うときに再確認する。

---

## S10. アグリゲートには変数を書けない `確定`

一次資料:

> アグリゲートの値は単純な定数、またはそれ自体がアグリゲートであってよい。
> **ただし変数であってはならない。**

```krl
$VEL = {CP 0.1, ORI1 100.0, ORI2 100.0}             ; OK but literals only
$VEL = {CP WB_approachMPerSec, ORI1 100.0}          ; NG : syntax error
$VEL.CP = WB_approachMPerSec                        ; OK
```

**「処理部にリテラルを書かない」（S2）と組み合わせると、成分代入しか
選べない。** M2 の起動時設定が縦に長いのはこのため。

なお「アグリゲートで全成分を指定しなくてもよい（省略した成分は変わらない）」
とも書かれているが、P1 の観点では全成分明示が望ましい。

---

## S11. `$CONFIG.DAT` を触らない `暫定`

中身が見えないうちは、アプリケーションコードから変数を追加しない。
必要になったらコントローラ構成の変更として別に扱う。

---

## S12. `:IN` 引数を書き換えない `確定`

```krl
; NG : the identifier means mm/min before this line and m/s after it
Velocity = VelocityCalc(Velocity)
```

単位や意味が変わったら別の変数を作る（N4 の系）。

---

## S13. 引数の型は完全一致させる `確定`

一次資料の型変換表はスカラ型（`BOOL` / `INT` / `REAL` / `CHAR`）しか
扱っていない。**構造体型は変換が定義されていない = 完全一致が必要。**

そしてスカラ型の変換には罠がある。

| 元 | 先 | 効果 |
|---|---|---|
| `BOOL` ↔ `INT` / `REAL` / `CHAR` | | 転送不可、エラー |
| `INT` | `REAL` | そのまま |
| **`REAL`** | **`INT`** | **黙って四捨五入される** |

`$VEL_AXIS` / `$ACC_AXIS` / `$APO.CVEL` / `$APO.CPTP` は **INT**、
`$VEL.*` / `$ACC.*` / `$APO.CDIS` / `$APO.CORI` は **REAL**。
`.dat` の宣言型を合わせること（P4）。
