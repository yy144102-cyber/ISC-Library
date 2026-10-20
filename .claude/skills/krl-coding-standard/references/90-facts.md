# 事実台帳

**確認済みの事実のみ。推論は書かない。** 出典を必ず明記する。

出典区分:
- **[一次]** KUKA 公式マニュアル
- **[実績]** 実機で動いたことが確認されているコード
- **[二次]** 非公式の解説。仮説扱い

参照した一次資料:
- `KRL-Reference-Guide-v4_1.pdf`（2002年発行、KR C2 / KSS 4.x 世代）
- `KST_ArcTech_Basic_37_en`（ArcTech Basic 3.7、KSS 8.6 / 8.7 用、2023-11-02）
- `KST_RSI_50_en`（RobotSensorInterface 5.0）
- `KST_WorkVisual_60_en`（WorkVisual 6.0 V7、KSS 8.2〜8.7 用、2025-01-23）
- `KSS_87_END_ja`（KSS 8.7 エンドユーザー向け、日本語。smartPAD のメニュー名の出典）
- `KSS_87_SI_en.pdf`（KSS 8.7 SI V7、2023-07-07 発行、761頁）
- `KSS_87_System_variables_en.pdf`（KSS 8.7 System variables V1、2022-06-01、238頁）

**v4.1 は世代が離れている。** 世代で変わらない部分（スコープ、識別子、
S/T の概念）以外は KSS 8.7 側を優先する。

---

## 言語仕様

| 事実 | 出典 |
|---|---|
| 識別子は最大 **24 文字**。`A–Z` `0–9` `_` `$`。数字始まり不可。キーワード不可 | [一次] v4.1 §2.1.2 |
| 大文字小文字を区別しない | [一次] v4.1 |
| 主 `DEF` のローカル変数は同じファイル内の別 `DEF` から見えない | [一次] v4.1 |
| `.src` の最初の `DEF` のみ外部から呼べる（`GLOBAL` なしでも） | [一次] v4.1 §2.2.14.3 |
| `DEFDAT … PUBLIC` + 変数の `GLOBAL` 宣言で他モジュールから参照可 | [一次] v4.1 §2.2.15 |
| `:IN` = 値渡し、`:OUT` = 参照渡し | [一次] v4.1 / 8.7 §11.10.5 |
| v4.1 では `:OUT` が**省略時の既定値**。8.7 は既定を記述していない | [一次] 両方 |
| `:OUT` 変数は呼び出し時点で値を持っている必要がある | [一次] v4.1 |
| v4.1: 配列は `:IN` で渡せない（`:OUT` のみ、`[]` `[,]` `[,,]`）。8.7 は記述なし | [一次] v4.1 |
| 型変換はスカラ型（`BOOL`/`INT`/`REAL`/`CHAR`）の間のみ定義。**構造体は完全一致が必要** | [一次] 8.7 §11.10.6 |
| **`REAL` → `INT` は黙って四捨五入される** | [一次] 8.7 §11.10.6 |
| `BOOL` ↔ 他のスカラ型は転送不可（エラー） | [一次] 8.7 §11.10.6 |
| `DEFFCT` は構造体型を返せる（例: `DEFFCT TorqLimitParam myCalcLimits()`） | [一次] 8.7 §6.23 |
| **アグリゲートの値に変数は書けない。** 定数かアグリゲートのみ | [一次] 8.7 §11.3 |
| アグリゲートで全成分を指定しなくてよい（省略した成分は変わらない） | [一次] 8.7 §11.3 |
| 宣言部と実行部は分かれる。実行部に宣言は書けない | [一次] v4.1 |
| **既定では**、SRC ファイルの最初のプログラムはファイルと同じ名前になる（"By default"）。不一致の可否は記述なし | [一次] v4.1 §2.2.14.3 |
| モジュールは同名の SRC ファイルと DAT ファイルからなる | [一次] v4.1 §2.1.1 |
| 日付入りのファイル名で、`DEF` 名もそれに一致させた形（`DryRun_20260915`）は保存・コンパイル・実行できている | [実績] |
| ファイル名だけ変えて中身の `DEF` 名が不一致のままだと、コンパイルが通らない | ユーザーの運用知見（この件での試験記録ではない） |
| 算術演算子は `+ - * /` の4つ。`INT / INT` は小数点以下切り捨て | [一次] 8.7 §11.14.1 |
| 論理演算子は `NOT` `AND` `OR` `EXOR`。比較は `==` `<>` `>` `<` `>=` `<=` | [一次] 8.7 §11.14 |
| **`MOD` は演算子としての記述が 761 頁中に無い。受け付けられるかは未確認** | [一次] 8.7（記述の不在） |

---

## 動作命令

| 事実 | 出典 |
|---|---|
| **CP 動作（LIN / CIRC / _REL）では S と T は常に無視される** | [一次] v4.1 §2.2.6 / 8.7 §11.5.5 |
| プログラムの最初の動作命令は**完全な PTP**（`POS`/`E6POS` または `AXIS`/`E6AXIS`）でなければならない。サブプログラムは除く | [一次] 8.7 §7.6 |
| `LIN_REL` の構文は `LIN_REL End point <Approximation> <#BASE|#TOOL>`。`#BASE` が既定 | [一次] 8.7 §11.5.5 |
| 絶対座標の `PTP` / `LIN` の構文は `End point <Approximation>` のみ。**`#BASE`/`#TOOL` を付けた場合に弾かれるかは未確認** | [一次] 8.7 §11.5 |
| `WAIT SEC` は先行実行を止める | [一次] 8.7 |
| `LIN_REL` の並進は `$BASE` の軸方向 | [一次] v4.1 §2.2.30 |
| 目標位置に未定義の構造体成分があれば 0 として扱われる（絶対値は変化しない） | [一次] v4.1 / 8.7 |
| **`_REL` 動作が中断された場合、中断位置を起点に変位全体が再実行される** | [一次] 8.7 §11.5.5 |
| PTP / LIN / CIRC / _REL の近似パラメータは `C_PTP` `C_DIS` `C_ORI` `C_VEL` `C_APX` の5つ | [一次] 8.7 §11.5.7 |
| **`C_SPL` はスプライン動作専用**（`SPLINE…ENDSPLINE` の終端） | [一次] 8.7 §11.6 |
| ただし UEC の稼働コードが `LIN_REL … C_SPL` を使用 → **矛盾。未決着** | [実績] `endo_260513_weav_wall2.src` |
| 近似する区間では Base と Tool が定義されていること | [一次] 8.7 §11.5.7 |
| 2つの近似点の間に `$TOOL` 文を置いてはならない | [一次] v4.1 §2.2.32 |
| PTP は同期 PTP。全軸が同時に動き出し同時に停止する | [一次] 8.7 §11.5.6 |
| `C_PTP` は「ブロック長の 50% を過ぎるまで近似を始めない」制限がある | [一次] 8.7 §3.27 |
| 先行実行は近似の計算に必要。`$ADVANCE = 0` だと近似できない。既定 3、最大 5。実際に先読みできる数は計算機の能力による | [一次] 8.7 §8.2 |
| **LIN / CIRC / PTP は、時間が足りないか先行実行停止のために近似できないと、エラーを出さずに終点で正確停止する**（スプラインは近似の弧の始めで待ってから近似する。挙動が違う） | [一次] 8.7 §9.7.5 |
| `HALT` はプログラムを止める。実行中の最後の動作命令は最後まで動く。再開はスタートキーだけで、`HALT` の次の命令から続く。割り込みプログラムの中では、先行実行を全部処理してから止まる | [一次] 8.7 §11.8.5 |

---

## システム変数

| 変数 | 型・単位・値域 | 出典 |
|---|---|---|
| `$VEL` | STRUC `{CP REAL m/s, ORI1 REAL °/s, ORI2 REAL °/s}` | [一次] 8.7 §3.333 |
| `$ACC` | STRUC `{CP REAL m/s², ORI1 REAL °/s², ORI2 REAL °/s²}` | [一次] 8.7 §3.4 |
| `$APO` | STRUC `{CVEL INT %, CPTP INT %, CDIS REAL mm, CORI REAL °}` | [一次] 8.7 §3.27 |
| `$VEL_AXIS[1..6]` | **INT**、%、**1…100** | [一次] 8.7 §3.337 |
| `$ACC_AXIS[1..6]` | **INT**、%、1…100 | [一次] 8.7 §3.6 |
| `$VEL_EXTAX[1..6]` / `$ACC_EXTAX[1..6]` | INT、%（E1…E6） | [一次] 8.7 §3.340 / §3.13 |
| `$ORI_TYPE` | ENUM `#CONSTANT` / `#VAR` / `#JOINT` | [一次] 8.7 §3.183 |
| `$ROTSYS` | ENUM `#AS_TRA`（既定）/ `#BASE` / `#TCP`。`_REL` 動作で A/B/C の回転基準系を決める | [一次] 8.7 §3.241 |
| `$POS_ACT` | E6POS。**TCP の指令位置（setpoint）**、現在の BASE 基準。実測ではない。書込み禁止。**プログラム中で読むと先行実行が止まる** | [一次] 8.7 §3.196 |
| `$ADVANCE` | INT、**1…5**（既定 3） | [一次] 8.7 §3.22 |
| `$GEAR_JERK[1..6]` | INT、%。**スプライン動作に必要**。未初期化だと開始時に停止 | [一次] 8.7 §3.105 |
| `$VEL` の上限は `$VEL_MA`、`$ACC` の上限は `$ACC_MA`（機械データ） | [一次] 8.7 |
| 上限違反時は `Value assignment inadmissible` で実行停止 | [一次] 8.7 §3.333 |

マニュアルの記載例: `$VEL={CP 2.0,ORI1 300.0,ORI2 300.0}`。
**これは記載例であって `BAS(#INITMOV,0)` の実装値ではない。**

---

## ArcTech（Basic 3.7）

| 事実 | 出典 |
|---|---|
| 電源の設定は WorkVisual の ArcTech Editor で行う（Hardware タブで電源を選ぶ → Editors > Options packages > Open ArcTech Editor） | [一次] AT 6.2 |
| ウェルドモードの名前は自由に付けられる（`"WAAM3D CwMIG"` は統合時に付けた名前と読める） | [一次] AT 6.3.1 |
| **Channel 1〜8 は自由に設定できるパラメータで、名前も自由に付けられる。** 汎用電源では既定ですべて無効 | [一次] AT 6.3.2 |
| **有効にした Channel の値はフィールドバスで電源へ送られる**（スケーリングを設定する） | [一次] AT 6.3.4 |
| **Channel はそれぞれ $OUT の範囲に割り付ける。アドレス＋オフセットが $IN / $OUT の番号になる** | [一次] AT 6.4.1 / 6.4.2 |
| 入出力の設定では、溶接機との信号と PLC との信号が分けて表示される | [一次] AT 6.4.1 / 6.4.2 |
| ArcTech の PLC 向けの標準インタフェースは、メッセージ（状態・確認・対話）の受け渡しだけ | [一次] AT 6.4.5 |
| Process allocations タブで、点弧・溶接・クレータ・共通の各段階にどの入出力が使われるかが見られる | [一次] AT 6.4.3 |
| **Robot velocity は溶接中のロボットの速度**（電源へ送る値ではない）。単位は m/s・m/min・cm/min から選べ、既定は m/min。WorkVisual でしか変えられない | [一次] AT 6.3.2 |
| ArcTech はサブミットが動いている印としてライフビットを周期的に出している。サブミットが止まるとリセットされる | [一次] AT 6.4.2 |
| **説明書に載っている溶接のプログラミングは、インラインフォーム（ARC ON / ARC SWITCH / ARC OFF / ARC BLOCK / ARC SPLINE）だけ。`ArcMainNG`・`TRIGGER`・`WDAT` の記載は一切ない** | [一次] AT 8（記述の不在） |
| **「溶接線上の動作はすべて溶接命令でなければならない」** | [一次] AT 8.2 |
| ARC BLOCK の中には溶接命令と LIN / CIRC / SLIN / SCIRC を置ける | [一次] AT 8.6 |
| ArcTech には機械式ウィービング（ウィービングパターン・周波数・ウィービング平面）の機能がある | [一次] AT 2.6 |
| ISC の `WeldingAct` は `TRIGGER` + `ArcMainNG` を手書きし、その後の溶接区間はふつうの `LIN` で動かしていた。それで溶接できていた | [実績] `WVDepositionRJ` |
| UEC は ArcTech を使っていない。アーク ON は `$OUT[1]=TRUE`（`'Weld start'`）→ `WAIT FOR $IN[5]`、OFF は `$OUT[1]=FALSE`。どちらも標準の OUT / WAIT FOR のインラインフォーム。溶接条件はコードに無い | [実績] `arcon_ohta.src` / `arcoff_ohta.src` |
| UEC の主プログラムでインラインフォームは `PTP HOME2` の2か所だけ。ウィービングの `LIN_REL` は手書き | [実績] `endo_260513_weav_wall2.src` |

## RSI（5.0）

| 事実 | 出典 |
|---|---|
| 命令は `RSI_CREATE` / `RSI_DELETE` / `RSI_ON` / `RSI_OFF` / `RSI_CHECKID` / `RSI_MOVECORR` / `RSI_ENABLE` / `RSI_DISABLE` など | [一次] RSI 7.1 |
| `RSI_ON` の既定はセンサーモード `#IPO_FAST`、補正モード `#ABSOLUTE`。補正の座標系は RSI コンテキストの POSCORR オブジェクトで決まる | [一次] RSI 7.1.4 |
| 相対補正では、それまでの補正の総和に今回の補正を足して指令位置をずらす | [一次] RSI 2.4.2.2 |
| ETHERNET オブジェクトで外部とデータ（位置・軸角度など）を周期的にやり取りする（UDP、XML） | [一次] RSI 2.2.3 |
| RSI コンテキストの置き場所は `C:\KRC\ROBOTER\Config\User\Common\SensorInterface` | [一次] RSI 7.4 |
| `WAAM_RSI_ON` / `OFF` / `CHECK` / `DELETE` は、名前から RSI の命令を包んだものと推定 | **推察** |

## WorkVisual（6.0）

| 事実 | 出典 |
|---|---|
| 制御盤のプロジェクトを読み込める（File > Browse for project）。Download necessary options でオプションも一緒に取り込める | [一次] WV 14.7 / 6.30.10 |
| プロジェクト全体を文字列で検索できる（Ctrl+F） | [一次] WV 13.3 |
| 変数の使用箇所をファイル・行つきで一覧にできる（Find usages） | [一次] WV 13.4.9 |
| デバッグモードでは、`.src` のローカル変数も（先行実行ポインタがそのモジュールにある間）監視できる | [一次] WV 13.6.3 |
| I/O Mapping で KR C の入出力とフィールドバスの信号の対応が見られる | [一次] WV 9.4.1 |

## 実機のファイル（2026-09 のコントローラ一式）

出典: `3261646(PCRC-5KIJEZ4STQ)`（KRC 配下と RSI の丸ごとの写し）。以下 [実機] と書く。
写しは Library の `ref/KUKA_3261646/snapshot/` にある（2026-09-23 と 09-25 の取得分。古い方は git の履歴）。

### 制御盤とソフトウェアの版（`Connections.xml`）

| 事実 | 出典 |
|---|---|
| **KSS は V8.6.12.610**。制御盤は KR C4、シリアル 3261646、ホスト名 PCRC-5KIJEZ4STQ、IP 172.31.1.147 | [実機] `Connections.xml` |
| オプション: ArcTech Basic 3.7.2.112 / ArcTech Advanced 3.7.1.9 / RobotSensorInterface 4.1.5.560 / KUKA.WAAM 1.0.2 / SafeOperation 3.5.4.4 / EthernetKRL 3.1.3.30 / ExpertTech 4.0.9.1089 / PathMode 1.0.3.5 / LoadDataDetermination 7.2.6.249 / KUKA.PROFINET MS 5.0.3.40 / KUKA.EtherNetIP MS 4.1.5.3 | [実機] `Connections.xml` |
| **手元の一次資料（SI / System variables / END）は KSS 8.7 用で、実機は 8.6。** ArcTech Basic 3.7 の説明書は 8.6 / 8.7 用（8.6 で成り立つかの扱いは `91-open.md` #34） | [実機] / [一次] 各資料の表紙 |
| RSI の説明書は 5.0 用で、実機の RobotSensorInterface は 4.1.5 | [実機] / [一次] |
| 写しの KRL ファイル（`.src` / `.dat` / `.sub`）の改行: 制御盤で作られたものはすべて LF（0923 は 272 本すべて、0925 は 240 本中 238 本）。**CRLF は `WBead_20260924.src` / `.dat` の2本だけ**（出張PCの VS Code で書いたもの）。**制御盤は LF も CRLF も受け付ける**（ISC / W3D の LF のプログラムも、CRLF の WBead も動いた） | [実機]（2026-09-29 にバイト列で数えた）/ [実績] |
| 写しの元は WAAM 装置のPCの WorkVisual 6.0 のフォルダ（`C:\Users\WAAM3D\Documents\WorkVisual 6.0\Repositories\3261646(PCRC-5KIJEZ4STQ)`）。`actions.log` にファイルが変わった時刻が残る（中身は残らない） | [実機] `actions.log` |

### BAS（`KRC\R1\System\bas.src`）

| 事実 | 出典 |
|---|---|
| `BAS()` の局面は `#INITMOV` `#ACC_CP` `#ACC_PTP` `#VEL_CP` `#VEL_PTP` `#TOOL` `#BASE` `#EX_BASE` `#FRAMES` `#CP_DAT` `#PTP_DAT` `#PTP_PARAMS` `#CP_PARAMS` など | [実機] |
| `#PTP_PARAMS` = `PTP_DAT()` + `FRAMES()` + `VEL_PTP(v)`。`#CP_PARAMS` = `CP_DAT()` + `FRAMES()` + `VEL_CP(v)`。**`#FRAMES` は `FRAMES()` だけ**（速度に触らない） | [実機] |
| `FRAMES()` は `FDAT_ACT` を読み、ベースが外部キネマティクスに割り当てられていれば `EX_BASE()` で `$BASE = EK(MACHINE_DEF[m].ROOT, MACHINE_DEF[m].MECH_TYPE, BASE_DATA[n])` とする | [実機] |
| `TOOL()` は `$TOOL = TOOL_DATA[n]`、`$LOAD` を `LOAD_DATA[n]`（**ツール番号と同じ番号**）から入れ、負荷未設定時は既定値。`$ACT_TOOL` を更新 | [実機] |
| `#INITMOV` はベースを `$WORLD`、ツールを `TOOL_DATA[1]` にし、速度・加速度・近似を `$config.dat` の `DEF_` 値にする | [実機] |

### メッセージ（`KRC\R1\System\MsgLib.src`）

| 事実 | 出典 |
|---|---|
| `MsgNotify` / `MsgQuit` / `MsgState` / `MsgLoop` / `MsgDialog` は `MsgLib.src` の GLOBAL DEF。2つ目以降の引数は省略できる（`MsgQuit("text", "module")` の形） | [実機] |
| `MsgQuit` は確認メッセージ（`Set_KrlMsg(#QUIT, …)`）を出し、**確認されるまで `WHILE Exists_KrlMsg(…)` で待ってから戻る**。戻ったあとはプログラムが先へ進む。既定で先行実行を止める（`VL_Stop = TRUE`） | [実機] |

### `$config.dat` / `$machine.dat`

| 事実 | 出典 |
|---|---|
| `DEF_VEL_CP = 2.0` m/s、`DEF_VEL_ORI1/2 = 200` °/s、`DEF_ACC_ORI1/2 = 100` °/s²、`DEF_APO_CDIS = 3.0` mm、`DEF_APO_CPTP = 50`、`DEF_ADVANCE = 3` | [実機] |
| `$VEL_MA = {CP 3.0 m/s, ORI1 400, ORI2 400}`、`$ACC_MA = {CP 10 m/s², ORI1 1000, ORI2 1000}` | [実機] `STEU\Mada\$machine.dat` |
| **`$VEL_CP_T1 = 0.229` m/s**（T1 の CP 速度の上限）。`$RED_T1 = 7` %、`$RED_T1_OV_CP = FALSE` | [実機] |
| → DryRun の HOME→HOVER の LIN は、T1 では 0.229 m/s、AUTO では既定の 2.0 m/s で走った。A4 速度超過の説明がつく | [実機] |
| `MACHINE_DEF[2] = KP1-V1000_40`、`#EASYS`、ROOT = X 1757.57 / Y −0.005 / Z −1118.09 / A −74.60 / B −0.26 / C −89.65 | [実機] |
| **`MACHINE_FRAME_DAT[17]` = `MACH_DEF_INDEX 2`**（Base[17] は KP1-V1000_40 に割り当て） | [実機] |
| **`BASE_DATA[17] = {X 0, Y 0, Z 310.8, A 75.75, B 0, C 0}`**（ポジショナのフランジからのずらし量）。これまで「Base17 の値」と呼んでいた X 1757.57 等はポジショナの根元（ROOT）だった | [実機] |
| `TOOL_DATA[1] = {X −4.24, Y 1.56, Z 562.38, A 149.41, B 15.42, C −179.67}` | [実機] |
| `I[20]` は `$config.dat` の普通の INT 配列（`SIGNAL` ではない） | [実機] |

### W3D パッケージ（`TP\WAAM`、`TP\WAAM3D`）

| 事実 | 出典 |
|---|---|
| ヘッダは「Modified: KUKA UK」。W3D のパッケージは KUKA UK が作ったもの | [実機] |
| `oLayerNum` / `oSideNum` / `oLayerType` / `oLayerIndex` / `oIsScanning` / `oLayerCompleted` などは **すべて `$OUT` の `GLOBAL SIGNAL`**（`waamglobals.dat`） | [実機] |
| `$OUT[9]` = `oSystemHealthyLP`（表示灯・白）、`$OUT[10]` = `oCycleStatusLP`（表示灯・黄）。KRL のどこにも書き手がいない（PLC か I/O マッピング側） | [実機] |
| ISC の `IF ($OUT[9]==TRUE) OR ($OUT[10]==TRUE)` は、W3D の `WAAM_RSI_ON` で**既にコメントアウトされていた条件**の写し | [実機] |
| `$OUT[995]` はこのコントローラのどこにも出てこない | [実機] |
| 溶接開始などの 513 台の信号（`oStartWelding` 等）は宣言だけで未使用（EWM 向けの名残と読める）。実際の溶接は ArcTech の 2000 台 | [実機] |
| `WAAM_RSI_ON` = `RSI_CREATE("RSI_WAAMCtrlCwMIG")` + `RSI_ON()`、`OFF` = `RSI_OFF` + `RSI_DELETE`、`DELETE` は空 | [実機] |
| `WAAM_RSI_ON` はコンテナ（ID 1）が無いときだけ `RSI_CREATE` し、続けて `RSI_ON`。`WAAM_RSI_OFF` は `RSI_OFF` のあと、コンテナがあれば `RSI_DELETE`。結果は `MsgNotify` で出す | [実機] `TP\WAAM3D\WAAM_RSI.src` |
| ISC の `WVDepositionMaster` は、各層を `WAAM_RSI_ON()` → 溶接（`WVDepositionOJ` / `RJ`。アークの ON / OFF はこの中）→ `WAAM_RSI_OFF()` の順で呼ぶ。層の間は `HALT`（`WAIT SEC 30.0` はコメントアウト） | [実機] `ISC_CHECK\WVDepositionMaster.src` |
| **`RSI_WAAMCtrlCwMIG` に補正のオブジェクトは無い。** 192.168.1.200 の外部 PC（WAAMCtrl）と位置・溶接状態・層番号などを送受信するだけ。戻りは文字列と `TempAcceptable` のみ | [実機] |
| `START_UP` / `PLC_PURGE` / `PLC_RETURN` / `PLC_WIRE` などは冒頭で `$ASYNC_AXIS = 'B0011'`、最後に `'B0000'` にする | [実機] |
| `$ASYNC_AXIS` は手元の KSS 8.7 の説明書に記載が無い | [一次]（記述の不在） |
| W3D のガスの信号: `iGasFlow` = `$IN[609..624]`（`WAAMProcess.sub` が `rGasFlow` に換算）、`iGasOK` = `$IN[543]`、`oGasFlowRate` = `$IN[593..608]`。センサがつながっているかは不明 | [実機] `waamglobals.dat` / `WAAMProcess.sub` |
| `$OUT[50]` = "Main Gas"、`$OUT[51]` = "Side Gas"（W3D のプログラムの名前）。KRL でこれを TRUE にしている行は無い。`GAS_CONTROL()`（サブミットから毎周期）が、プログラムの状態が `#P_RESET` / `#P_END` / `#P_FREE` のときに両方 FALSE にする | [実機] `WAAMSPS.src` / `PLC_HOME.src` / W3D Create の `.dat` |
| サブミット（`sps.sub`）のユーザー領域から `WAAMSPS_LOOP()` を呼び、衝突検知（動作を止めるメッセージ）・ガス出力・PLC 監視・RSI への値の受け渡しを毎周期行っている | [実機] |

### ArcTech の入出力（`TP\ArcTech\ArcWoV`）

| 事実 | 出典 |
|---|---|
| ウェルドモード `"WAAM3D CwMIG"`。Channel1 = 名前なし（0〜1）、**Channel2 = Job Number**、**Channel3 = Hot Wire Feed Speed [m/min]**、**Channel4 = Cold Wire Feed Speed [m/min]**、Channel5 = Arclength Correction、Channel6 = Dynamic Correction | [実機] `ArcWovW1Modes.dat` |
| **Robot velocity の単位は m/s**。`WDAT1.Weld.Velocity = 0.025` は 1500 mm/min | [実機] |
| **Ch2 は ArcTech 上の名前は "Job Number" だが、実際は iWave（Fronius）のシナジックライン番号を送っている** | ユーザー確認 |
| Ch1 は未定義で、常に 1 にしている | ユーザー確認 |
| ガス流量は ArcTech の設定に無い（ガスはオン／オフの出力 `$OUT[2008]` だけ）。流量は調整器・溶接機側で設定 | [実機] `ArcWovIo.dat` / `ArcWovW1Modes.dat` |
| **ARCON / ARCOFF のインラインフォームが展開するコードは、ISC の `WeldingAct` と同じ行**（動作の行だけ違う） | [実機] `teach\line.src`、愛知産業 `L0001_S1_CWGMA_ISC.src` |
| ISC の `WDAT1` は点弧・溶接・ウィービング・クレータを1つに持ち、ARC ON と ARC OFF の両方で使っていた。コールドワイヤも使用（点弧 1.0 / 溶接 3.0 m/min）、クレータ 0.5 秒 | [実機] `WVDepositionRJ.dat` |
| ArcTech のステータスキー「溶接 オン/オフ」: オフなら ARC ON を通っても点弧せず、経路はそのまま走る。T1/T2 ではキーの状態だけ、AUT ではキースイッチ入力が優先 | [一次] AT 7.1 |
| ArcTech は既定で「T1 でも溶接する」設定 | [一次] AT 7.1 |
| TRIGGER の DELAY / PATH で呼ぶ関数は、それを含むプログラムが Hidden 属性であること | [一次] SI 11.12.3 |
| Hidden は先頭行 `&ACCESS` の `V` の有無で表す（`RV` = 表示、`R` = 非表示） | [一次] SI 7.4.2 |
| `ArcGetDelay` / `ArcGetPath` は `TP\ArcTech\ArcMain.src`（`&ACCESS R2` = 非表示）の GLOBAL DEFFCT | [実機] |
| **WorkVisual は、ARC ON / ARC OFF の TRIGGER 内の `ArcGetDelay` / `ArcGetPath` に「The called function … is not hidden」のエラーを出す。規則は満たされ、同じ行の ISC プログラムは制御盤で動いているので、WorkVisual の誤検出として扱う。** 最終判定は smartPAD での選択 | [実機] / ユーザー確認（古いプログラムでも同じエラー） |
| 出力: 溶接開始 `$OUT[2000]`、Robot Ready `$OUT[2001]`、ガス `$OUT[2008]`、ワイヤ送り/戻し `$OUT[2009]/[2010]`、確認 `$OUT[2011]`（以上 溶接機）。コールドワイヤ送り/戻し `$OUT[398]/[399]`（外部） | [実機] `ArcWovIo.dat` |
| 入力: 電源準備 `$IN[2001]`、プロセス中 `$IN[2003]`、電流あり `$IN[2004]`、主電流 `$IN[2006]`（溶接機）。**`$IN[400]` AB System Ready / `$IN[407]` AB Wire Available（外部。点弧の前提条件）** | [実機] |
| **ガスありの入力 `wArcIGasFlowAvailable[1..4]` は全部 `Active FALSE`。** ArcTech はガスが流れているかを見ていない（状態の一覧に `NoGasFlow` / `GasFlow` はあるので、入力を割り付ければ見る仕組みはある）。ガスの信号は出力 `$OUT[2008]`（"Gas flow"）の指令だけ | [実機] `ArcWovIo.dat` / `Arc0Global.dat` |
| ガスの前流し・後流しの時間は、ArcTech の設定で最大 2.0 秒 | [実機] `ArcWovW1Modes.dat` |
| **停止点の ARC ON / ARC OFF（オンザフライでない）では、ArcTech はロボットプログラムの中で前流し・後流しを `WAIT SEC` で待つ。** ARC ON: ガスの出力 → `WAIT SEC PreFlowTime` → 点弧。ARC OFF: クレータ → 溶接終了 → `WAIT SEC PostflowTime` → ガスを止める。どちらも `ArcMainNG(#ArcOnAfterMoveStd / #ArcOffAfterMoveStd)` の中で先行実行を止めたあとなので、**待つ間ロボットは止まっていて、プログラムの次の行は待ちが終わってから実行される** | [実機] `TP\ArcTech\ArcState.src`（`#PrepIgnition` / `#GasPostFlow`）/ `ArcMain.src` |
| 溶接 OFF（コールド）のときは、前流し・開始時間・クレータ時間・後流しを待たない（`gArcWaitWhenCold = FALSE`） | [実機] `ArcUser\UserArcCustom.src` / `ArcState.src` |
| 移動しながら前流しを始める機能（`Strike.PurgeTime`、TRIGGER の `#GasPreflow`）がある。`PurgeTime 0.0` なら働かない | [実機] `ArcMain.src` |
| ウェルドモード `"WAAM3D CwMIG"` は `StrikeParamDisable FALSE`。TRUE のモードでは点弧の条件が溶接の条件で置き換わり、`PreFlowTime` が 0 になる（`ArcCopyWeldToStrike`） | [実機] `ArcWovW1Modes.dat` / `ArcMain.src` |
| 溶接機（iWave）は、ガスが流れないと止まる | ユーザー確認 |
| Channel の出力先: Ch2 → `$OUT[2064..2079]`、Ch3 → `$OUT[2080..2095]`、Ch4 → `$OUT[480..495]`、Ch5 → `$OUT[2096..2111]`、Ch6 → `$OUT[2112..2120]` | [実機] |

### UEC

（上の「ArcTech」節の UEC の行を参照）

## オペレーティングモード

| 事実 | 出典 |
|---|---|
| T1 では TCP 速度がクランプされる（AUTO では外れる） | [一次] 8.7 §3 安全機能 |
| **したがって T1 での検証は AUTO の検証にならない。** 速度起因と特異点起因の両方をマスクする | [実績] DryRun の A4 速度超過 |
| `$OV_JOG`（HOV）は手動ジョグ用。AUTO では無関係 | [一次] 8.7 |
| `$OV_PRO`（POV）は全モードでプログラム動作に効く | [一次] 8.7 |

---

## コントローラ構成（未読・推測を含む）

| 事実 | 出典 |
|---|---|
| `BAS.SRC` は `KRC\R1\System\bas.src`。KUKA 納入の KRL ソース。**API として文書化されていない** | [一次] 記述が一行のみ / [二次] |
| INI 行には「内部変数とパラメータの初期化」が含まれる（マニュアルの記述はこれだけ） | [一次] 8.7 §7.6 |
| `BAS()` の局面には `#TOOL` / `#BASE` / `#EX_BASE` / `#VEL_PTP` / `#VEL_CP` / `#ACC_CP` もある | [二次] **仮説** |
| ベースは WORLD 座標系または外部キネマティクスに割り当てられる（管理画面にアイコンあり） | [一次] 8.7 §5.18.8 |
| `FDAT` にはベース番号しか入らない（`BASE_NO 17`）。それで Base17 が解決できている | [実績] `DryRun_20260915.dat` |

---

## 既存コードの構成（比較材料）

| 事実 | 出典 |
|---|---|
| W3D 系・ISC 系は `.dat` の `Point[]` を実行時に書き換える | [実績] `ISC_500_t5`, `WVDepositionRJ` |
| **UEC は `.dat` を実行時に書き換えない**（`.dat` はティーチ由来の `FDAT` と自動生成の `LAST_BASIS` のみ） | [実績] `endo_260513_weav_wall2.dat` |
| → **`.dat` 書き換えは KUKA の作法ではなく W3D 系の習慣** | 上記2件から |
| UEC のサブプログラム（`coordinate_ohta`, `arcon_ohta`）にも INI フォールドが残っており、呼ぶたびに `BAS(#INITMOV,0)` が走る | [実績] |
| `XHOMEX` の構造 = 先頭 `X`（インラインフォーム自動生成）+ 点名 `HOMEX` | [実績] `LAST_TP_PARAMS` の `Kuka.PointName` |
| 旧 W3D コードは `BASE_DATA[17]` を実行時に上書きし、終了時に戻さない | [実績] `ISC_500_t5.src`, `ISC_CladdingSquare_t15.src` |
