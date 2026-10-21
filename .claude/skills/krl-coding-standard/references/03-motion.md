# 動作命令と座標系（M1〜M9 / C1〜C8）

---

# 動作命令（M1〜M9）

## M1. 速度・加速度・近似はシステム変数に直接代入する。座標系は BAS に任せる `確定`

**速度・加速度・近似**: `BAS(#PTP_PARAMS, v)` / `BAS(#CP_PARAMS, v)` を使わず、
システム変数に直接代入する。したがって `PDAT_ACT` / `LDAT_ACT` と、それが指す
`PPDAT*` / `LCPDAT*` も、`$BWDSTART` も `SET_CD_PARAMS()` も使わない。

**座標系（TOOL / BASE / LOAD）**: `FDAT_ACT` を設定して `BAS(#FRAMES, 0)` を呼ぶ（C1）。
直接代入はしない。実機の `bas.src` を読んだ結果、外部キネマティクスのベースと
負荷データに、直接代入では再現できない処理があると分かったため。

**根拠**: `BAS()` が何を設定するかは `BAS.SRC` を読まないと分からない
（P1 違反）。また呼び出し元の `.dat` 構造体への暗黙依存を生む（P2 違反）。

`BAS(#INITMOV,0)` だけは INI フォールドで実行する（割り込み宣言などを含む）。

### `BAS()` 経由のメリット（再検討用に記録）

1. `BAS(#CP_PARAMS, v)` 一発で `$VEL` / `$ACC` / `$APO` などが一括設定される
2. **インラインフォームと挙動が揃う。** ティーチした行は必ず `BAS()` 経由の
   コードを生成するので、混在させるなら `BAS()` に寄せた方が一貫する
3. KSS 更新で設定すべき変数が増えても `BAS.SRC` は KUKA が更新する

**インラインフォームを今後使わない前提なら Y（直接代入）でよい。**
実機で `BAS.SRC` を読んだ後に再検討する。

### `BAS(#INITMOV,0)` とは

`.src` を新規作成すると KUKA のテンプレートが挿入する `;FOLD INI` の中身。
マニュアルの記述は一行だけ（「INI 行には内部変数とパラメータの初期化が
含まれる」）で、`BAS()` は API として文書化されていない。`BAS.SRC` は
KUKA が納入する KRL のソースファイルであり、中身を読む以外に確定手段がない。

二次資料によれば `BAS()` には `#TOOL` / `#BASE` / `#EX_BASE` / `#VEL_PTP` /
`#VEL_CP` / `#ACC_CP` などの局面もある（仮説）。

---

## M2. 使う変数は起動時に全て明示する `確定`

`BAS(#INITMOV,0)` の実装値に依存しないため、使う可能性のある変数は全て
自分で書く。**書かない変数は使わない**が対になる。

```krl
;--- coordinate systems ( through BAS, see C1 ) ------------
FDAT_ACT.TOOL_NO   = WB_toolNo
FDAT_ACT.BASE_NO   = WB_baseNo
FDAT_ACT.IPO_FRAME = #BASE
BAS (#FRAMES, 0)

;--- PTP ---------------------------------------------------
FOR axisIdx = 1 TO 6
   $VEL_AXIS[axisIdx] = WB_ptpVelPct      ; INT 1..100
   $ACC_AXIS[axisIdx] = WB_ptpAccPct      ; INT 1..100
ENDFOR

;--- CP ----------------------------------------------------
$VEL.CP   = WB_approachMPerSec
$VEL.ORI1 = WB_oriVelDegPerSec
$VEL.ORI2 = WB_oriVelDegPerSec
$ACC.CP   = WB_cpAccMPerSec2
$ACC.ORI1 = WB_oriAccDegPerSec2
$ACC.ORI2 = WB_oriAccDegPerSec2
$ORI_TYPE = #VAR

;--- approximation ( C_DIS only ) --------------------------
$APO.CDIS = WB_apoDistMm                  ; REAL, mm

;--- relative motion ---------------------------------------
$ROTSYS   = #BASE
$ADVANCE  = 3                             ; INT 1..5. controller setting, not a
                                          ; build parameter ( no WB_ variable )
```

アグリゲート1行で書けない理由は S10。

### 必要な変数の一覧（一次資料）

| いつ | 変数 | 型・単位 |
|---|---|---|
| 常に | `$TOOL` / `$BASE` / `$LOAD` | FRAME / FRAME / LOAD |
| PTP | `$VEL_AXIS[1..6]` | **INT**、%、1…100 |
| PTP | `$ACC_AXIS[1..6]` | **INT**、%、1…100 |
| PTP（外部軸） | `$VEL_EXTAX[]` / `$ACC_EXTAX[]` | INT、% |
| LIN / CIRC | `$VEL.CP` | REAL、m/s |
| LIN / CIRC | `$VEL.ORI1` / `$VEL.ORI2` | REAL、°/s |
| LIN / CIRC | `$ACC.CP` | REAL、m/s² |
| LIN / CIRC | `$ACC.ORI1` / `$ACC.ORI2` | REAL、°/s² |
| LIN | `$ORI_TYPE` | ENUM `#CONSTANT` / `#VAR` / `#JOINT` |
| CIRC | `$CIRC_TYPE` | ENUM |
| 近似 | `$APO.CDIS` / `$APO.CORI` | REAL、mm / ° |
| 近似 | `$APO.CVEL` / `$APO.CPTP` | **INT**、%、1…100 |
| `_REL` | `$ROTSYS` | ENUM |
| 先行実行 | `$ADVANCE` | INT、1…5（既定 3） |
| スプラインのみ | `$GEAR_JERK[1..6]` | INT、%。未初期化だとスプライン開始時に停止 |

`暫定`: `$VEL.ORI*` / `$ACC.*` の具体値に根拠がない。機械上限
（`$VEL_MA` / `$ACC_MA`）は `$MACHINE.DAT` にあり実機待ち。安全側の値で
流して実測してから上げる。`;@ASSUME` を付ける。

---

## M3. 速度は変わる箇所でのみ代入する `確定`

動作命令ごとに設定し直さない。一度書けば次に変えるまで残る。

```krl
$VEL.CP = WB_approachMPerSec
LIN WB_posRetract
LIN WB_posStart

$VEL.CP = WB_tsMPerSec          ; deposition speed from here
FOR cycIdx = 1 TO WB_cyclesPerPass
   ...
ENDFOR

$VEL.CP = WB_approachMPerSec    ; back to travel speed
```

S6（サブに INI フォールドを残さない）が前提。`BAS(#INITMOV,0)` が途中で
走ると全部リセットされる。

---

## M4. 動作種別の選択 `確定`

| 場面 | 種別 | 理由 |
|---|---|---|
| プログラム最初の動作 | **完全な `PTP`** | 一次資料の要件。軸配置を一意に確定させる |
| 空間内の移動、位置決め | `PTP` を優先 | 軸速度の制限内で計画されるので速度超過が起きない |
| 経路形状が必要な区間 | `LIN` / `LIN_REL` | 経路が意味を持つ場合のみ |

一次資料:

> プログラムの最初の動作命令は明確な始点を定義しなければならない。
> `POS` / `E6POS` 型または `AXIS` / `E6AXIS` 型の**完全な** PTP 命令を使う。
> 「完全」とは終点の全成分が指定されていることを意味する。
> サブプログラムとしてのみ使われるプログラムでは、この限りではない。

**`LIN` は経路形状が必要なときだけ。** CP 動作では軸速度が制約ではなく
結果なので、上限の保証がない。DryRun の A4 速度超過はこれ。

---

## M5. 絶対点は最小限にする `確定`

CP 動作（LIN / CIRC / _REL）では Status と Turn が**常に無視される**
（一次資料）。S/T が意味を持つのは PTP の目標点だけ。

詳細は C3。

---

## M6. `LIN_REL` の基準系を明示する `確定`

```krl
LIN_REL quarterRise C_DIS #BASE
```

KSS 8.7 の構文:

```
LIN_REL End point <Approximation> <#BASE|#TOOL>
```

`#BASE` は既定値だが書く（P1）。`$ROTSYS` も併せて明示する（C7）。

**絶対座標の `PTP` / `LIN` / `CIRC` には書かない。** KSS 8.7 の構文は

```
PTP     End point <Approximation>
LIN     End point <Approximation>
LIN_REL End point <Approximation> <#BASE|#TOOL>
```

で、`#BASE` / `#TOOL` を取るのは `_REL` だけ。絶対座標の動作は常に現在の
`$BASE` を基準にする。**付けた場合にコントローラが弾くかは未確認**（`C_SPL` の件と同じく、構文定義に無い＝構文エラーとは限らない）。`krlcheck` の M6 で WARN として検出する。

**`REL` = relative。** `LIN` が絶対座標の終点まで直線移動するのに対し、
`LIN_REL` は現在位置からの変位を指定する。出発点が現在の軸角度そのものに
なるため S/T が不要。

---

## M7. 近似は `C_DIS` を既定とする `暫定`

**近似（approximation）** とは、経路上の点で正確に停止せず手前から次の
動作へ滑らかに繋ぐこと。指定するのは「どこから近似を始めるか」の判定基準。

| キーワード | 判定基準 | 変数 |
|---|---|---|
| **`C_DIS`** | 終点までの**距離**が `$APO.CDIS` [mm] を下回ったら開始 | REAL, mm |
| `C_ORI` | 支配的な**姿勢角**の残りが `$APO.CORI` [°] を下回ったら開始 | REAL, ° |
| `C_VEL` | 減速中に**速度**が指令値の `$APO.CVEL` [%] まで落ちたら開始 | INT, % |
| `C_PTP` | **PTP 用**。ブロック長の 50% を過ぎた後、軸角度が規定値を下回ったら開始 | INT, % |
| `C_APX` | `C_DIS` と同じ距離基準だが**極小距離向け**。推奨 1〜3mm | REAL, mm |

### `C_SPL` は使わない `暫定`

`C_SPL` はスプライン動作（`SPLINE…ENDSPLINE` / `SLIN` / `SPTP`）専用で、
KSS 8.7 の「PTP / LIN / CIRC / _REL の近似パラメータ」一覧に含まれていない。

**ただし UEC の稼働実績コードが `LIN_REL … C_SPL` を使っている。**
一次資料と稼働実績が矛盾しているため、「構文エラー」とは断定しない。
`C_DIS` は文書化されており挙動が明確なので、そちらを使う。

実機コンパイルで「受け付けるか」を確認する（→ `91-open.md`）。

### 近似の制約

> 近似パラメータを使う場合、近似されるブロックで Base と Tool が定義されて
> いること。さもないと `BASE not programmed` / `TOOL not programmed` が出る。

加えて、2つの近似点の間に `$TOOL` 文を置いてはならない（C2）。

---

## M8. `_REL` 動作は中断すると全体が再実行される `確定`

一次資料:

> REL 命令は常にロボットの現在位置を基準とする。このため **REL 動作が中断
> された場合、ロボットは中断された位置を起点として REL 動作全体を再度実行する。**

**「停止して再開すれば元の軌道に戻る」ではない。軌道が変わる。**

相対座標で組む造形（C6）はこの性質を丸ごと引き受ける。復帰手順は
条項10（中断・復帰）で扱う。**未着手。**

---

## M9. 先行実行（Advance run） `暫定`

- `$ADVANCE` は **INT、1…5**、既定 3
- 動作命令の直前で、`TRIGGER` が参照する変数を書き換えない
- 状態変数の設定はプログラム冒頭にまとめる

**`TRIGGER` は2つの異なる時刻に評価される。**

```krl
TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#PreDefinition, WDAT1) ...
                                  ^^^ 先行実行で評価
        DO ArcMainNG(#PreDefinition, WDAT1, WP1) PRIO = -1
           ^^^ 経路到達時に実行
```

同じ `WDAT` が別の時刻に読まれるため、**動作命令の直前で書き換えると
先行実行側が旧値を読む。** 書き換えるならプログラム冒頭でまとめて行う。

`WBead` は1層あたり 186 本の `LIN_REL` を約 28 秒で流す（1本 0.15 秒）。
先行実行が追いつかない可能性があるが、**Phase 1 の実測で判断**する。
既定のまま様子を見る方が P5 に沿う。

---

## M10. アークは ARC ON / ARC OFF の展開形を `WB_ArcOn` / `WB_ArcOff` に置く `確定`

ArcTech のインラインフォーム ARCON / ARCOFF が展開するコードと同じ行（`TRIGGER` ×3 +
`ArcMainNG` ×2）を、同じファイル内のサブプログラムに置く。インラインフォームの動作
（`LIN XP…`）だけを `LIN $POS_ACT`（その場の長さゼロの動作）に置き換える。

**根拠**
- この機体の `teach\line.src` と愛知産業のプログラムで、インラインフォームの展開が ISC の
  `WeldingAct` と同じ行であることを確認した（KUKA 自身が生成するコード）
- ISC の `WVDepositionRJ` はこの形で、溶接区間をふつうの `LIN` にして溶接できていた
- WBead の `LIN_REL` のループを崩さずに済む

**書き方**
- `TRIGGER` と `ArcMainNG` の行は**手で書き換えない**。コピー元と一字一句同じにする
- データセットは溶接条件の組ごとに1つ（`WDAT1`、`WDAT2`…）。1つのデータセットに点弧・溶接・ウィービング・クレータを全部持たせ、その層の ON / OFF の両方で使う（ISC と同じ）
- **組が複数あるとき** `暫定`（2026-10-21、`WBead_20261021a`）:
  - 組を全部、起動時に一覧表から代入しておき、層ごとには**どの組を使うかを選ぶだけ**にする。層の途中で WDAT の値を書き換えて条件を変えない（S2、M9）
  - `WB_ArcOn` / `WB_ArcOff` の中に、組ごとに同じ行の組を並べ、データセット名だけを変える。インラインフォームが別のデータセットで展開する形と同じ（`teach\line.src` の `WDAT4` / `WDAT5`）。どの組を通るかは引数（`useSet2 :IN` など）の `IF` で選ぶ
  - **TRIGGER には引数を渡さない。** TRIGGER の中は `.dat` のデータセットだけを書く。サブプログラムを呼ぶ TRIGGER は割り込みとして数えられ、割り込みプログラムには `.src` の変数（引数を含むランタイム変数）を渡してはならないため（`90-facts.md`）
- ウィービングはロボットの経路で作るので `Weave.Pattern #None`
- Channel などの値は S2 の例外に従い、起動時に一覧表から代入する

**WorkVisual のエラーについて**: WorkVisual は TRIGGER 内の `ArcGetDelay` / `ArcGetPath` に
「The called function … is not hidden」を出す（ARC ON / OFF の組で7件）。誤検出で、制御盤は
受け付ける（`90-facts.md`）。これ以外のエラーが混ざっていれば本物として扱う。

**試し方**: `WB_dryRun = FALSE` で ArcOn / ArcOff が呼ばれる。点弧するかは ArcTech のステータスキー
「溶接 オン/オフ」（Configuration > Status keys > ArcTech）で決まる。AUT ではキースイッチ入力
（この機体では `$IN[400]`）が優先。**ArcTech は既定で T1 でも溶接する。**

---

# 座標系と S/T（C1〜C8）

## C1. 座標系は `BAS(#FRAMES)` で起動時に1回設定する `確定`

```krl
FDAT_ACT.TOOL_NO   = WB_toolNo
FDAT_ACT.BASE_NO   = WB_baseNo
FDAT_ACT.IPO_FRAME = #BASE
BAS (#FRAMES, 0)
```

**`$BASE = BASE_DATA[n]` と直接書かない。** 実機の `bas.src` によれば、`BAS(#FRAMES)`
の中の `FRAMES()` はベースの割り当て先（`MACHINE_FRAME_DAT[n]`）を調べ、外部
キネマティクスに割り当てられていれば `EX_BASE()` で

```krl
$BASE = EK(MACHINE_DEF[m].ROOT, MACHINE_DEF[m].MECH_TYPE, BASE_DATA[n])
```

と組み立てる。ISC のセルの Base[17] は `KP1-V1000_40`（`MACHINE_DEF[2]`、`#EASYS`）
に割り当てられており、`BASE_DATA[17]` はポジショナのフランジからのずらし量
（Z 310.8、A 75.75）にすぎない。直接代入するとロボット自身の根元から 310.8 mm 上を
基準にしてしまう。

**`$TOOL` / `$LOAD` も直接書かない。** `TOOL()` は `$LOAD` を **ツール番号と同じ番号の
`LOAD_DATA`** から入れ、負荷データが未設定のときの既定値処理も行う。`$ACT_TOOL` /
`$ACT_BASE`（smartPAD の表示）もここで更新される。負荷番号を別に持つ必要はない。

番号は `.dat` の固定データ（S2）。`krlcheck` の C1 が直接代入を検出する。

---

## C2. 近似区間で座標系を変更しない `確定`

近似を使う区間では Base と Tool が定義されている必要がある。加えて
2つの近似点の間に `$TOOL` 文を置いてはならない。

`WBead` は起動時1回なので該当しないが、将来ツールを切り替える造形では効く。

---

## C3. S/T を持つ点は2つまで `確定`

一次資料:

> CIRC 動作では終点の角度状態は常に始点と同じ。このため `POS` / `E6POS` の
> Status S と Turn T は**常に無視される**。

`LIN_REL` の節にも同じ記述がある。

| 点 | 型 | S/T |
|---|---|---|
| `WB_posHome` | `E6POS` または `E6AXIS` | **持つ** |
| `WB_posRetract` | `E6POS` | 持つが無視される（LIN で到達） |
| 造形経路上 | `FRAME` + `LIN_REL` | **持たない** |

主プログラムの最初の動作は完全な `PTP`（M4）。サブプログラムには課さない。

---

## C4. `POS_HOME` は `E6AXIS` を検討する `暫定`

ホームは「安全に退避した既知の姿勢」であって、ワーク基準の点ではない。

| | 利点 | 欠点 |
|---|---|---|
| `E6POS` + S/T | ベース変更時に位置が追従 | S/T の解釈に依存。KSS01447 の発生箇所 |
| **`E6AXIS`** | 軸角度そのもの。S/T 不要。ベース設定の影響を受けない | ベースを変えても同じ姿勢のまま |

現行は `E6POS`。変えるには実機での位置出しが必要なので、Phase 1 で
`$AXIS_ACT` を読んでから判断する。

---

## C5. `POS_HOME` の S/T は実機から取る `確定`

他プログラムからコピーしない。

DryRun の `XHOMEX`（S18 / T10）は出所不明のまま引き継がれた値。
**A が同じでも X/Y/Z が違えば軸角度が違い、T が違うのは正常**なので、
値の不一致自体は異常ではないが、根拠が失われていることが問題。

```krl
; @ASSUME POS_HOME S/T taken from live $POS_ACT on <date>
;         VERIFY: jog to home, read $POS_ACT, compare
```

---

## C6. 造形経路は相対で組む `確定`

絶対点のテーブルを持たない（ISC は 288〜290 点持っていた）。

**理由**: S/T を持つ点が増えない（C3）／ビード長・幅・ピッチをパラメータで
変えられる（点列の再生成が不要）／`.dat` を固定できる（S2）。

**代償が M8。** 中断時の軌道が保証されない。

---

## C7. `$ROTSYS` を明示する `確定`

`_REL` 動作で A/B/C の回転をどの座標系で実行するかを決める。

> 既定では、相対動作で指定した座標系で回転が実行される。`$ROTSYS` を使うと、
> 指定された基準座標系に関わらず、現在のベースまたは現在のツールの座標系で
> 回転させることができる。

A/B/C がゼロとは限らないので既定に任せない（P1）。

```krl
$ROTSYS = #BASE
```

---

## C8. ベース／ツール番号の意味を記録する `確定`

```krl
DECL INT WB_baseNo = 17    ; Base[17] : on external kinematic KP1-V1000_40
DECL INT WB_toolNo = 1     ; Tool[1]  : <describe TCP>. Load[1] follows it
```

番号だけでは、別セルに持っていったとき何が起きるか分からない（P5）。
