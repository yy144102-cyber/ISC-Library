# ワークスペース規約

> 2026-09-28 に白紙から作り直した。旧規約（W- / VR- / UH- / PN- / OF- の各番号）は廃止。
> 旧版は Library の git 履歴（2026-09-28 以前）にだけ残る。

規則には必ず理由を書く。**理由の無い規則は、見直すときに判断できない。**
（旧 W-3「git remote を設定しない」は理由が書かれておらず、同期の要否を判断できなかった）

---

## 1. 構成

```
Claude Workspace/
├─ CLAUDE.md                          この規約を読み込む入口。git の外。各PCで1回作る（§4）
├─ .claude/settings.json              Web 検索・取得の禁止（R10）。git の外。各PCで1回作る（§4）
├─ Project/<分類>/<YYMMDD>_<名前>/    作ったもの
├─ Library/                           プロジェクトをまたいで使うもの
└─ Scratch/                           使い捨て
```

| 置き場所 | 入れるもの |
|---|---|
| `Project` | 作ったもの。**1つのテーマ（何を作る・確かめるか）で1フォルダ** |
| `Library` | 複数のプロジェクトで使うもの、または使う前提で作った基盤。他人のソースや資料（読むだけ）。装置の状態の記録 |
| `Scratch` | 消えて困らないもの。削除は運用者が手で行う（自動では消えない） |

**Project の分類**は、主な成果物の分野で決める（例: `WAAM` / `Rocket` / `Agent`）。
WAAM で作るロケットの部品は `WAAM`。分類のフォルダは、最初のプロジェクトを入れるときに作る。

**Project の名前**は `<テーマを始めた日 YYMMDD>_<テーマ>`。英数字にする
（git の表示やスクリプトで日本語のパスが扱いにくいため）。

**R1. 依存は Project → Library の一方向。Library は単独で clone して動くこと。**
理由: 別のPCに Library だけを持っていっても壊れないようにするため。
（2026-09 に、Library の相関式が Project 内のファイルを根拠にしていて、Library 単独では検査が落ちる状態だった）

**R2. 同じものを2か所に置かない。**
プログラムは、その版を作ったプロジェクトに1つだけ置く。後のプロジェクトからは名前（版）で参照する。
理由: 出張PCとこのPCで同じフォルダが別々に育ち、どれが最新か分からなくなった（2026-09）。
例外: 装置の状態の記録（実機の写し）は、記録として同じファイルを含んでよい。

---

## 2. 同期（git / GitHub）

**R3. git で管理するのは Library と各 Project（1プロジェクト1リポジトリ）。このPCと出張PCで使うもの（Library と WAAM の Project）は、GitHub の private リポジトリで同期する。**
当面は個人アカウント（`yy144102-cyber`）。コミットの著者も個人の設定のまま。

| ローカル | GitHub |
|---|---|
| `Library` | `yy144102-cyber/isc-library` |
| `Project/WAAM/260922_WeaveTest-UECRepro` | `yy144102-cyber/isc-260922_WeaveTest-UECRepro` |

- GitHub のリポジトリ名は頭に `isc-` を付ける。個人アカウントにある、仕事と関係のないリポジトリと区別するため。ローカルのフォルダ名は §1 のまま（clone のときにフォルダ名を指定する）
- ほかの Project（Rocket、Agent）は、このPCのローカルの git だけで持つ
- GitHub の履歴は 2026-10-05 に新しく始めた。それより前の履歴は、このPCのタグ `local-history-20261005`（と枝 `master`）にだけある

理由: USB でフォルダをコピーする運用では、どちらかが古くなっても気づけなかった。

**R4. 作業の始めに pull、終わりに push する。** VS Code では「ソース管理」の「変更を同期」が pull と push を続けて行う。
理由: 2台で同じファイルを直すと衝突する。

**R5. 次のものは GitHub に上げない。`.gitignore` で機械的に除外する。**

| 上げないもの | 理由 |
|---|---|
| 著作物の資料（メーカーのマニュアルの PDF とテキスト） | 社外サーバへの複製になる |
| 秘密情報（`.env` など） | 漏れたら取り消せない |
| 生成物（`bin/` `obj/` など、作り直せるもの） | 容量ではなく、作り直せるから |

上げないもので別のPCでも要るものは、手でコピーする。何をどこから持ってくるかは `Library/README.md` に書く。

**R6. 次のファイルは改行コードを変換しない（`.gitattributes` で `-text`）。**
- KRL（`.src` / `.dat` / `.sub`）: 実機から来たバイト列のまま持つ
- ハッシュで検査するファイル（`Library/engineering/sources/`）

理由: このPCの git は改行を自動で変換する設定になっている。変換されると、ハッシュ検査が落ち、実機の写しとも差分が出る。
実機の写しの KRL ファイルは LF と CRLF が混ざっている。制御盤で作られたものは LF、出張PCの VS Code で書いた `WBead_20260924` の2本は CRLF で、**どちらも実機で動いている**（2026-09-29 にバイト列で数えた）。
（当初は「KRL は CRLF に固定」、次に「すべて LF」と書いたが、どちらも誤り。2回目は測り方を誤った。R13）

---

## 3. 環境の注意

**R7. UTF-8 のファイルを読み書きするスクリプトでは、エンコーディングを明示する。スクリプト自体に日本語を含めない。**
理由: PowerShell 5.1 は BOM なしの UTF-8 を Shift-JIS として読む。7 では既定が UTF-8 だが、5.1 も併存している。

**R8. `pwsh.exe` を絶対パスで呼ばない。`pwsh` とコマンド名で呼ぶ。**
理由: Store 版はパスにバージョン番号が入り、更新のたびに変わる。

**R13. 改行コードは、ファイルのバイト列で数えて確かめる（Python で `b'\r\n'` を数える、など）。Git Bash の `grep` で `\r` を探さない。**
理由: Git Bash の `grep` は CR を読み飛ばし、CRLF のファイルでも `\r` が 0 件になる。これで CRLF のファイルを LF と誤認し、規約（R6）と事実台帳に誤った事実を書いた（2026-09-29。CRLF の試験ファイルで 0 件になることを確かめた）。

**R14. 2台の開発環境を揃える。VS Code は「設定の同期」で同期し、ソフト本体は `Library/tools/pc-setup/winget-packages.json` で同じものを入れる。**
- VS Code: 2台とも GitHub アカウント（`yy144102-cyber`）で「設定の同期」をオンにする。拡張機能・設定・キー割り当ても同期する
- ソフト本体（VS Code、git、Python、PowerShell 7、Claude デスクトップアプリ）: `winget import` で入れる（§4）。Python だけ版を 3.11.9 に固定する。ほかは自動で更新される
- Python の追加パッケージは使っていない。krlcheck と相関式の検査は、標準の機能だけで動く（2026-10-17、import の行で確認）
- 道具を足したら一覧に足して push し、もう1台で `winget import` し直す。**ここは手順に頼る。足し忘れても機械では気づけない**
- 版は `Library/tools/pc-setup/check-env.ps1` で測り、下の表に書く

理由: 2台で環境が食い違い、作業の仕方を変える羽目になった（2026-09-29: このPCに VS Code の Python の拡張機能が無く、krlcheck のタスクが動かなかった。タスクを python の直接呼び出しに書き換えた）。

### 実測値

`pwsh -File Library/tools/pc-setup/check-env.ps1` の結果。

| 項目 | このPC（2026-10-17） | 出張PC |
|---|---|---|
| OS | Windows 11 Pro 10.0.26200 | 未測定 |
| PowerShell | 7.6.5（5.1 も併存） | 未測定 |
| git | 2.53.0.windows.1 | 未測定 |
| Python | 3.11.9 | 未測定 |
| VS Code | 1.140.0（拡張機能 25） | 未測定 |
| winget | 1.29.380 | 未測定 |
| .NET SDK | 9.0.317 / 10.0.102 | 未測定（WAAM では使わない） |

---

## 4. 新しいPCでの準備

1. git を入れる（PowerShell で `winget install --id Git.Git -e`）。clone に要るので、ほかより先に入れる
2. GitHub から clone し、§1 の構成に置く（R3 の表。リポジトリ名とフォルダ名が違うので、フォルダ名を指定する）。ワークスペース直下の Git Bash で:

   ```
   git clone https://github.com/yy144102-cyber/isc-library.git Library
   git clone https://github.com/yy144102-cyber/isc-260922_WeaveTest-UECRepro.git Project/WAAM/260922_WeaveTest-UECRepro
   cp Library/tools/pre-commit Library/.git/hooks/pre-commit
   ```

   3行目は Library のコミット前の検査（相関式）を入れる。`.git/hooks/` は git に入らないので、clone のたびに入れ直す
3. 残りのソフトを入れる（R14）。ワークスペース直下の PowerShell で:

   ```
   winget import -i Library/tools/pc-setup/winget-packages.json --accept-package-agreements --accept-source-agreements
   ```

4. VS Code で「設定の同期」をオンにする（R14）。左下の歯車 →「設定の同期をオンにする」→ すべての項目を選んだまま、GitHub（`yy144102-cyber`）でサインインする
5. ワークスペース直下に `CLAUDE.md` を作り、次の3行を書く

   ```
   @Library/conventions/workspace.md
   @Library/conventions/claims_labeling.md
   @Library/conventions/operator.md
   ```

6. ワークスペース直下に `.claude/settings.json` を作り、`{"permissions":{"deny":["WebSearch","WebFetch"]}}` と書く（R10）
7. Library のスキルごとに、ワークスペース直下の `.claude/skills/` にジャンクションを作る（R12）。ワークスペース直下の PowerShell で:

   ```
   New-Item -ItemType Directory -Force .claude\skills
   New-Item -ItemType Junction -Path .claude\skills\krl-coding-standard -Target "$PWD\Library\.claude\skills\krl-coding-standard"
   ```

   **外すときは `cmd /c rmdir <リンクのパス>` を使う。** フォルダごと消す操作（エクスプローラーでの削除、`Remove-Item -Recurse`、`rm -rf`）で消すと、リンク先の正本の中身まで消えることがある
8. `Library/README.md` に従い、git に入っていないもの（マニュアルなど）をコピーする
9. `pwsh -File Library/tools/pc-setup/check-env.ps1` で版を測り、§3 の表の列を埋める

5 の `@` による読み込みが効くことは、2026-09-29 にこのPCで確認した（新しいセッションで3ファイルの中身が指示として読み込まれた）。

---

## 5. Web の情報

**R10. Claude Code では Web 検索と Web 取得をしない。設定（`.claude/settings.json` の `deny`）で機械的に止める。**
理由: Web の文章に仕込まれた指示が、ローカルのファイルを読み書きできる Claude Code に届かないようにするため。Web の調査は Claude デスクトップアプリ（チャット）で行う。チャットはローカルのファイルを読めないので、仕込まれた指示を読んでも手元に被害が出ない。
（2026-09-29 実測: このPCの Claude Code のツール一覧に WebSearch / WebFetch が出ない。
Claude Code が作るサブエージェントにも効く。公式ドキュメントを調べさせたサブエージェントは WebFetch を使えなかった）

**R11. Web の情報が要ると判断したら、Claude Code はその場で「デスクトップアプリへの依頼」を出す。** 推測で埋めない。

依頼には次を書く。運用者はこれをそのままデスクトップアプリに貼る。

- 知りたいこと（1つの問いに絞る）
- 何の判断に使うか
- 手元で分かっている前提（版、型番、エラー文など）
- 返してほしい形（要点の要約と出典の URL。コードは丸ごと貼らず、必要な行だけ）

戻ってきた情報は、出典つきの二次情報として扱う。コードや安全の判断に直接使う前に、一次資料か実機で確かめる。
運用者は、返ってきた文章を Claude Code に貼る前に自分で読む。

理由: 情報が足りないまま推測で進めると、もっともらしい誤りが混ざる（`claims_labeling.md` CL-3）。依頼の形を決めておけば、判断を止めずに調査だけを安全な側へ回せる。

---

## 6. スキル

**R12. Library のスキルは、ワークスペース直下の `.claude/skills/` にジャンクションを作って読み込ませる（§4 の手順7）。claude.ai には上げない。**
理由: Library の中に置いただけでは、Library の下のファイルに触るまで読み込まれない。そのため Project で作業すると、claude.ai に上げた古い写し（ガスの事実が抜けた版）が使われた（2026-09-29 実測）。
ワークスペース直下の `.claude/skills/` は起動時に読み込まれ、claude.ai から同期したスキルと名前が重なると同期していない方が優先される（公式: https://code.claude.com/docs/en/skills 。デスクトップアプリで調べた）。ジャンクションでも起動時に読み込まれ、正本が優先されることを 2026-09-29 に `/skills` で確かめた。
シンボリックリンクは、このPCでは管理者権限が要る（2026-09-29 実測）。ジャンクションは要らない。
claude.ai に上げない理由: Claude Code では正本が優先されて写しは使われず、残すと古い写しを間違って呼ぶおそれがある。デスクトップアプリの役割は Web の調査に限る（R10）ので、そこでも要らない。

---

## 7. 規則を足すとき

**R9. 規則は、実際に困ったときに足す。起きていない問題のための規則や装置は作らない。**
理由: 旧規約は前のプロジェクトの脅威を前提にした規則を抱えたまま移植され、後のプロジェクトを縛った。

プロジェクト固有の規則は、そのプロジェクトの `CLAUDE.md` に `P-` 番号で書く。
