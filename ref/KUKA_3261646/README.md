# KUKA_3261646 — WAAM セルの制御盤の写し

`snapshot/` は、WAAM 装置のPCにある WorkVisual 6.0 のフォルダの写し。**読むだけ。編集しない。**

```
出所: C:\Users\WAAM3D\Documents\WorkVisual 6.0\Repositories\3261646(PCRC-5KIJEZ4STQ)
```

## セル

| 項目 | 値 | 根拠 |
|---|---|---|
| 制御盤 | KR C4、シリアル 3261646、ホスト名 PCRC-5KIJEZ4STQ、IP 172.31.1.147 | `snapshot/Connections.xml`（ソース行確認済） |
| KSS | **V8.6.12.610** | 同上 |
| 主なオプション | ArcTech Basic 3.7.2.112 / ArcTech Advanced 3.7.1.9 / RobotSensorInterface 4.1.5.560 / KUKA.WAAM 1.0.2 / SafeOperation 3.5.4.4 / EthernetKRL 3.1.3.30 | 同上 |
| ロボット | KR 50 R2500 | 出張PCの KUKA_WS/CLAUDE.md（未確認） |
| 外部軸 | KP1-V1000_40（ポジショナ）。Base[17] に割り当て | 同上 |
| 溶接機 | Fronius iWave | 同上 |

作法の一次資料は KSS **8.7** のマニュアル（`engineering/references/KUKA/`）で、実機は **8.6**。8.7 由来の事実がそのまま当てはまるとは限らない。

## 履歴

写しは1つだけ置き、取り込むたびに上書きしてコミットする（workspace.md R2）。過去の状態は git の履歴で見る。

| 取得日 | 何のあと | コミットの件名 |
|---|---|---|
| 2026-09-23 | WBead の空走行の前 | 「Library の基盤（実機の写しは 2026-09-23 取得分）」（GitHub の最初のコミット） |
| 2026-09-25 | 116 層の造形に使った値が入っている（`WBead_20260924.dat` の最後の変更は 09-25 12:12）。取得した時刻は不明 | 「実機の写し: 2026-09-25 取得分（116 層の造形後）」※件名の「造形後」は確かめていない |

差分を見る: `git log --stat -- ref/KUKA_3261646/snapshot`

## 取り込み方

現地では、造形の日の終わりに出張PCで行う。

1. 装置のPCで、上の「出所」のフォルダを丸ごと USB にコピーする
2. 出張PCで pull してから、`snapshot/` の中身を消し、コピーしたフォルダの**中身**を入れる（フォルダ名の `3261646(PCRC-5KIJEZ4STQ)` の階層は作らない）
3. コミットする。件名は「実機の写し: <取得日> 取得分（<その日の造形 ID> のあと）」。例:「実機の写し: 2026-10-20 取得分（WAAM-2-1〜WAAM-2-3 のあと）」。上の表に1行足す
4. push する（workspace.md R4）

造形 ID から写しを探す: `git log --grep "WAAM-2-3" -- ref/KUKA_3261646`。
件名に造形 ID を書き忘れても、機械では気づけない（検査は作っていない）。

**写しは WorkVisual のフォルダなので、実行中に変わる値（`$config.dat` の `I[1]` など）が実機と同じとは限らない。** 2026-09-25 の写しの `I[1]` は 1（WBead は層ごとに `I[1] = layerIdx` を書く）。`actions.log` に `$config.dat` の変更の記録は無い。

**写しは、取り込んだ時点の状態しか残さない。** 取り込みの間に何度 `.dat` を書き換えても、残るのは最後の状態だけ。
造形ごとの値は造形記録（Notion）に書く。

`snapshot/actions.log` には、WorkVisual のフォルダでファイルが変わった時刻が残る（中身は残らない）。
2026-09-25 は `WBead_20260924.dat` が 7 回変わっている（09:48 / 10:50 / 10:55 / 11:22 / 11:42 / 12:04 / 12:12）。

## 作法の事実台帳との関係

`.claude/skills/krl-coding-standard/references/90-facts.md` の `[実機]` の出典は、`snapshot/KRC/` の下のファイル。
書き方はファイル名だけ（`ArcWovIo.dat`）のものと、途中からのパス（`TP\WAAM3D\WAAM_RSI.src`、`STEU\Mada\$machine.dat`）のものが混ざっている。
見つからないときは、ファイル名で `snapshot/` の下を探す。消えたファイルは git の履歴にある（`git log --all --name-only -- ref/KUKA_3261646`）。
