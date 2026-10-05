# 命名規約（N1〜N10）

---

## N1. 文字と長さ `確定`

一次資料（KRL Reference v4.1 / KSS 8.7）による識別子の制約。

| 項目 | 規則 |
|---|---|
| 文字種 | `A–Z`、`0–9`、`_`、`$` のみ |
| 先頭文字 | 数字で始めない |
| 予約語 | キーワードは使えない |
| 長さ上限 | **24 文字** |
| 大文字小文字 | **区別されない。** 意味の区別に使わない |
| コメント | **ASCII のみ。英語で書く** |

**コメントを ASCII 限定にする理由**は、smartPAD / WorkVisual での日本語表示
が未確認のため。**化けようのない文字だけ使う**という安全側の判断。日本語が
通ると判明したら緩めてよい（緩める方向の変更は安全）。

ローマ字（`sekisou_kazu`）は英語でも日本語でもない中途半端な選択なので使わない。
`;layer count` の方が短くて読める。

---

## N2. 接頭辞の三層構造 `確定`

大文字小文字が区別されないため、**人間向けの視覚的手がかり**として設計する。
コンパイラは関知しない。

| 何を示すか | 何で示すか |
|---|---|
| **スコープ** | 接頭辞の**有無**（あり = `.dat` モジュールレベル、なし = DEF ローカル） |
| **領域** | 接頭辞の**中身**（`WB_` / `SB_` / `CM_`） |
| **種別** | 接頭辞直後の**大小**（小文字 = 変数、大文字 = サブプログラム） |

```
WB_weaveAmplitudeMm  weaving bead  / module var
WB_CalcSegs          weaving bead  / subprogram
SB_layerStepMm       stringer bead / module var
CM_SetCpVel          common        / subprogram
layerIdx             (no prefix)   local var
```

**共通領域にも接頭辞を付ける。** 付けないとスコープが読めなくなるため。

### 領域接頭辞の一覧

| 接頭辞 | 領域 | 状態 |
|---|---|---|
| `WB_` | ウィービングビード造形 | 確定 |
| `SB_` | ストリンガービード造形 | 暫定・予約 |
| `CM_` | 領域共通（動作設定、ホーム復帰） | 暫定 |

`ST_` は使わない。`S`/`T`（Status / Turn）と紛らわしいため。

新しい領域が出たらこの表に追加し、同時に `krlcheck.py` の許可リストも更新する。

接頭辞は日付を除いた機能名から機械的に導く（`WBead_20260924` → `WB_`）。

---

## N3. ケース `確定`

すべて camelCase。`UPPER_SNAKE` は使わない。

| 対象 | 形式 | 例 |
|---|---|---|
| モジュール変数 | 接頭辞 + lowerCamel | `WB_weaveAmplitudeMm` |
| ローカル変数 | lowerCamel | `layerIdx` |
| サブプログラム引数 | lowerCamel | `weaveAmplitudeMm` |
| サブプログラム名 | 接頭辞 + PascalCase | `WB_CalcSegs` |
| モジュール名 | PascalCase | `WBead` |

---

## N4. 単位サフィックス `確定`

物理量を持つ変数には単位を付ける。免除されるのは無次元量（カウント、
添字、フラグ）だけ。

| 量 | サフィックス | 例 |
|---|---|---|
| 長さ | `Mm` / `M` | `WB_layerStepMm` |
| 速度 | `MmPerMin` / `MmPerSec` / `MPerSec` / `MPerMin` | `WB_tsMPerSec`, `WB_hotWfsMPerMin` |
| 加速度 | `MPerSec2` / `DegPerSec2` | `WB_cpAccMPerSec2` |
| 角度 | `Deg` / `Rad` | `WB_torchAngleDeg` |
| 角速度 | `DegPerSec` | `WB_oriVelDegPerSec` |
| 時間 | `Sec` | `WB_dwellSec` |
| 割合 | `Pct` | `WB_ptpVelPct` |

**`Ms` は使わない。** ミリ秒とメートル毎秒のどちらにも読める。ミリ秒は
`WAIT SEC` に合わせて使わない方針なので秒に統一する。

### 系: 単位が変わったら名前を変える

```krl
; NG : same name, two units
Velocity = VelocityCalc(Velocity)

; OK : one name, one unit
tsMPerSec = WB_tsMmPerMin / 60000.0
```

`:IN` 引数を書き換えて単位を変える書き方は禁止（S12）。

### 系: 単位換算はプログラムで行わない `確定`

`.dat` にはコントローラが要求する単位で記入し、現場単位を規定書式の
コメントで併記する。

```krl
DECL REAL WB_tsMPerSec       = 0.0666667   ; = 4000 mm/min
DECL REAL WB_approachMPerSec = 0.1         ; = 6000 mm/min
```

書式を固定すれば `krlcheck.py` で値とコメントの一致を機械検査できる。

**パラメータ間の従属関係（幾何・比率）はプログラムで導出する。** 換算は
表現の変換で設計の意図を持たないが、幾何の導出は設計の意図そのもの。

---

## N5. サブプログラム名は動詞始まり `確定`

| 悪い | 良い |
|---|---|
| `SegCalc` | `WB_CalcSegs` |
| `SegFlip` | `WB_FlipDir` |
| `WeldingAct(#_ON)` | `WB_ArcOn` / `WB_ArcOff` |
| `MotionPar(#PTPmotion, v)` | `CM_SetPtpVelPct` |
| `MotionPar(#CPmotion, v)` | `CM_SetCpVelMPerSec` |

### 系: モードで引数の単位が変わる関数は分割する `確定`

`MotionPar` は `#PTPmotion` なら %、`#CPmotion` なら m/s だった。
**呼び出し側から単位が読めない構造は名前では救えない。** 分割が唯一の解。

---

## N6. ブール `確定`

**真のときに成り立つ命題**として読める名前にする。

```
WB_dryRun         ; TRUE = arc is not struck
WB_progAlongY     ; TRUE = progress along Y, weave along X
WB_firstPassPlus  ; TRUE = first pass runs toward + of the progress axis
WB_pauseEnabled   ; TRUE = stop after layer WB_pauseAfterLayer
```

否定形の名前（`WB_notDry`）は禁止。`IF NOT WB_notDry` が読めなくなる。

---

## N7. 禁止する形 `確定`

| 禁止 | 理由 |
|---|---|
| 末尾の `X`（`XHOMEX`） | ティーチ時の点名の一部。手書きコードでは意味がない |
| 先頭の `X` / `F` / `PPDAT` / `CPDAT`（`XP1`, `FP1`, `LCPDAT1`） | インラインフォームの自動生成形。手書きと混ざると出所が追えない |
| 1文字（`N`, `i`, `j`） | N8 参照 |
| 承認外の略語 | N9 の一覧のみ |
| 造形条件入りのファイル名（`CircD2015_10RadiusChange01`, `ISC_CladdingSquare_t15`） | 条件を振るたびにファイルが枝分かれする。条件はパラメータで振る（V1 / V4） |

補足: `XHOMEX` の構造は「先頭 `X` = インラインフォームの自動生成」+
「点名 `HOMEX`」。`$CONFIG.DAT` の `XHOME` と衝突しないよう `HOME` では
なく `HOMEX` と名付けたと推測される（`未確認`）。

---

## N8. `i` を使わない `暫定`

W3D がコントローラ側にグローバル配列 `I[]` を持っている（ISC コードの
`I[1] = i` がそれ）。**KRL は大文字小文字を区別しないので `I[]` と `i` は
同じ識別子。**

既存コードで動いていた実績はあるが、意図して踏む橋ではない。ループ変数は
`layerIdx` / `segIdx` / `cycIdx` のように用途を書く。

---

## N9. 承認する略語 `確定`

これ以外は展開して書く。

```
TS    travel speed        SEG   segment       POS   position
VEL   velocity            IDX   index         DIR   direction
ACC   acceleration        APO   approximation PER   per
WFS   wire feed speed
PTP / CP / LIN            MIN / MAX / CUR     NUM / CNT
```

---

## N10. タグ `確定`

閉じた集合。追加時は `krlcheck.py` の検出条件も同時に更新する。

| タグ | 意味 | 実機投入前 |
|---|---|---|
| `;@OFFLINE` | 実機プロジェクトが無い状態での仮対応 | **戻す** |
| `;@PHASE4` | アーク投入段階で有効化する行 | それまで触らない |
| `;@ASSUME` | 未検証の前提。次行以降に適用 | **消し込む** |
| `;@TODO` | 未実装・要改善 | 残ってよい |

`;@ASSUME` の書式:

```krl
; @ASSUME BAS(#CP_PARAMS,v) sets $VEL.CP to v in m/s
;         VERIFY: read $VEL.CP in variable monitor, or check BAS.SRC
```

`VERIFY:` 行を必ず付ける。**何をすれば消せるか**が書いていない `@ASSUME` は
消えない。

---

## N11. 触ってはいけない名前 `暫定`

改名も再利用もしない。コーパスから抽出したものなので、実機の
`$CONFIG.DAT` を見るまで完全ではない。

| 出所 | 識別子 |
|---|---|
| システム変数 | `$` で始まるすべて |
| BAS | `BAS`, `SET_CD_PARAMS`, `IR_STOPM`, `PDAT_ACT`, `LDAT_ACT`, `FDAT_ACT`, **`SUCCESS`** |
| ArcTech | `Arc*`, `stArcDat_T`, `WDAT*`, `WP*` |
| W3D | `WAAM_*`, `oLayerNum`, `oSideNum`, `oLayerType`, `oLayerIndex`, `oIsScanning`, `oLayerCompleted`, `I[]` |
| ENUM | `Motion`, `Action`, `#` で始まるすべて |

**`SUCCESS` は要注意。** 標準の EXT フォールドに `DECL INT SUCCESS` が入って
おり、`$` が付かないため普通の名前と衝突する。

`WB_` / `SB_` / `CM_` 接頭辞は、この一覧が不完全でも衝突を避けるための保険。

---

## N12. ファイルとモジュール `確定`

- **`DEF` 名・`DEFDAT` 名をファイル名と一致させる。** ファイル名を変えたら中の名前も変える
  （一次資料 v4.1 は「既定では同じ名前」。`DryRun_20260915` は一致させた形で動作実績あり。
  ユーザーによれば、ファイル名だけ変えて中身が不一致のままだとコンパイルが通らない）
- `.src` / `.dat` は同名で対
- ファイル名は `<機能名>_<YYYYMMDD>`。造形条件は入れない（V1）
- 接頭辞は日付を除いた機能名から機械的に決める（`WBead_20260924` → `WB_`）

---

## N13. 名前は中身と一致させる `確定`

名前が指すものと、実際の動作・パラメータの意味を一致させる。**引き継いだ名前は必ず点検する。**

**根拠となった実例**: UEC から引き継いだ `WB_beadLenMm` は、ビードの長さではなく1周期で進む量（4.0 mm。
ビードの長さは周期数を掛けた 248 mm）だった。`WB_beadWidthMm` は、ビードの幅ではなく片側の振幅
（7.5 mm。実際の壁幅は 16 mm）だった。どちらも名前から読むと値を取り違える。

2026-09-25 に WBead の名前を点検して直した実例（旧 → 新）:

| 旧 | 新 | 何が問題だったか |
|---|---|---|
| `WB_beadLenMm` | `WB_weaveStepMm` | 上のとおり。ビードの長さではない |
| `WB_beadWidthMm` | `WB_weaveAmplitudeMm` | 上のとおり。ビードの幅ではない |
| `WB_progDirY` | `WB_progAlongY` | 「Dir」は向き（正負）に読めるが、中身は進む**軸**の選択 |
| `WB_startDirFwd` | `WB_firstPassPlus` | 「Fwd」がどちら向きか曖昧で、**実際に Y の向きを取り違えた** |
| `WB_pitchMm` | `WB_layerStepMm` | 溶接では「ピッチ」をウィービングの1周期の進み量の意味でも使う |
| `segFwd1` / `segFwd2` | `fwdQuarterRise` / `fwdHalfFall` | 番号では役割が分からない。「1」の変位は周期の終わり（2→3）でも使うので、番号も合っていなかった。名前で動き（中心→上端、上端→下端）が分かるようにした |
| `WB_advance` | 廃止。`.src` に `$ADVANCE = 3` | `WB_` が付くと造形のパラメータに見える。オペレータが触る値ではなく制御盤の設定 |

seg 系の「rise / fall」は、`.src` の図の上下（Base[17] の X/Y 平面の中の横方向）のこと。Z ではない。

P1（読み手に対する暗黙に依存しない）の適用。
