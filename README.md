# Library

複数のプロジェクトで使うもの（workspace.md §1）。**Project に依存しない。単独で clone して動く**（R1）。
GitHub: `yy144102-cyber/isc-library`（private。workspace.md R3）。

| フォルダ | 中身 | 扱い |
|---|---|---|
| `conventions/` | ワークスペース規約。ワークスペース直下の `CLAUDE.md` から読み込まれる | 編集する |
| `.claude/skills/krl-coding-standard/` | KUKA KRL のコーディング作法（スキル）。`krlcheck.py` もこの中の `scripts/` にある。ワークスペース直下からジャンクションで読み込む | 編集する |
| `ref/KUKA_3261646/` | WAAM セルの制御盤の写し | 読むだけ。取り込み方は中の README |
| `ref/UEC/` | UEC の WAAM プログラム（`endo_260513_weav_wall2` とサブルーチン） | 読むだけ |
| `ref/PicoGK/` | PicoGK のクローン（別リポジトリ。git の管理外） | 読むだけ |
| `engineering/correlations/` | ロケット設計の相関式。書式は `FORMAT.md`、検査は `tools/check_correlations.py`（pre-commit） | 編集する |
| `engineering/sources/` | 相関式の根拠のファイル（ハッシュで検査される） | 変えない |
| `engineering/references/` | 参考文献。**git に入っていない**（下記） | 読むだけ |
| `tools/` | プロジェクトに属さないスクリプト | |

## スキル（krl-coding-standard）の読み込み

**正本は `.claude/skills/krl-coding-standard/`（この Library）。写しは作らない。**
ワークスペース直下の `.claude/skills/krl-coding-standard` を、ここへのジャンクションにして読み込ませる（workspace.md R12、作り方は §4）。

読み込まれ方（2026-09-29 実測）:

- ジャンクションがあれば、起動したときから `krl-coding-standard`（接頭辞なし）として読み込まれる。どのフォルダで作業していても使える
- Library の下のファイルを触ると、同じ正本が `Library:krl-coding-standard` としても一覧に出る。中身は同じファイル
- ジャンクションが無いと、Library の下のファイルに Read / Edit で触るまで読み込まれない（シェルで読むだけでは読み込まれなかった）

**claude.ai には上げない。** 以前上げた写し（2026-09-24 版、ガスの事実が抜けていた）は、2026-09-29 に claude.ai から削除した。
手元の同期フォルダ（`~/.claude/skills/synced/`）からも消えたことを確かめた。

## git に入っていないもの（別のPCでは手でコピーする）

| もの | 置き場所 | 入手先 |
|---|---|---|
| KUKA のマニュアル（PDF 7冊） | `engineering/references/KUKA/*.pdf` | このPCの同じ場所から USB / Drive でコピー（元は KUKA の配布資料） |
| KUKA のマニュアルのテキスト版（6本） | `engineering/references/KUKA/text/*.txt` | 同上。**テキスト化した手順は残っていない**ので作り直せない。失わないこと |
| PicoGK のクローン | `ref/PicoGK/` | 必要になったら clone し直す |

テキスト版は文字の部分だけで、図・画面写真・画像で入っている注意書きは含まない。
**安全の判断にテキストの検索結果を使わない。** 図が要るときは、各ページ末尾のページ番号（`www.kuka.com | 33/761` の形）から PDF を開く。

## pre-commit hook

`tools/pre-commit` が正本。`.git/hooks/` は git の管理外なので、clone したら入れ直す:

```
cp tools/pre-commit .git/hooks/pre-commit
```
