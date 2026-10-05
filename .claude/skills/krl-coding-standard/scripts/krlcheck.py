#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
krlcheck.py -- KRL (.src / .dat) 構造・作法チェッカ

これはコンパイラの代わりではない。
識別子が実在するか、型が合っているか、動くかどうかは一切見ない。
それらは $CONFIG.DAT とオプションパッケージ側にあるため、
実機プロジェクトを WorkVisual に読み込む以外に検証手段はない。

見るのは「ファイルだけで機械的に判定できる構造と作法」のみ。

指摘コードは KRL コーディング作法の条項番号と一致する。
    P  設計原則          00-principles.md
    N  命名              01-naming.md
    S  変数配置・引数    02-variables.md
    M  動作命令          03-motion.md
    C  座標系と S/T      03-motion.md
    T  検証手順          04-verification.md
    V  命名・版管理      05-versioning.md

重大度:
    ERROR  確定条項の違反。直すこと
    WARN   暫定条項の違反、または判定に曖昧さが残るもの
    INFO   参考。作法上は望ましくないが、事情があれば許容

使い方:
    python krlcheck.py WBead.src WBead.dat
    python krlcheck.py ./someDir          (配下の .src/.dat を全部)
    python krlcheck.py --quiet ./someDir  (ERROR のみ)
    python krlcheck.py --only M,S ./x.src (条項の系を絞る)
    python krlcheck.py --format vscode x.src   (VS Code の問題パネル用。1指摘1行)

終了コード: 0 = ERROR なし / 1 = ERROR あり / 2 = 使い方の誤り
           3 = ツール自身の異常 (検査結果ではない)
外部ライブラリ不使用。Python 3.6 以上。
"""

import os
import re
import sys
from collections import defaultdict

# KRL は大文字小文字を区別しない。識別子の比較は常に upper() で行う。

ERROR, WARN, INFO = 'ERROR', 'WARN', 'INFO'
SEV_ORDER = {ERROR: 0, WARN: 1, INFO: 2}

MAX_IDENT = 24                                          # N1
TAGS = ('OFFLINE', 'PHASE4', 'ASSUME', 'TODO')          # N10
AREA_PREFIXES = ('WB_', 'SB_', 'CM_')                   # N2

# N4 長い順に並べる。endswith 判定で取りこぼさないため
UNIT_SUFFIX = ('MmPerMin', 'MmPerSec', 'MPerSec2', 'MPerSec', 'MPerMin',
               'DegPerSec2', 'DegPerSec', 'Deg', 'Rad',
               'Mm', 'Sec', 'Pct', 'M')

# N7 インラインフォームが自動生成する形。手書きでは使わない
GENERATED_IDENT = re.compile(
    r'^(X[A-Z][A-Z0-9_]*|FP\d+|PPDAT\d+|LCPDAT\d+|CPDAT\d+|PDAT\d+|LDAT\d+)$', re.I)

# M1 BAS() 経由の動作パラメータ設定機構
BAS_TOKENS = ('PDAT_ACT', 'LDAT_ACT', '$BWDSTART', 'SET_CD_PARAMS')
BAS_CASES = ('#PTP_PARAMS', '#CP_PARAMS')

# M2 最初の動作命令より前に設定されているべきシステム変数
REQUIRED_SYSVARS = ('$TOOL', '$BASE', '$LOAD',
                    '$VEL_AXIS', '$ACC_AXIS',
                    '$VEL.CP', '$VEL.ORI1', '$VEL.ORI2',
                    '$ACC.CP', '$ACC.ORI1', '$ACC.ORI2',
                    '$ORI_TYPE')

MOTION_RE = re.compile(
    r'^\s*(PTP|LIN|CIRC|PTP_REL|LIN_REL|CIRC_REL|SPTP|SLIN|SCIRC)\b', re.I)
REL_RE = re.compile(r'^\s*(PTP_REL|LIN_REL|CIRC_REL)\b', re.I)

# S2 処理部に書いてよい構造的な定数
STRUCTURAL_LITERALS = {'0', '1', '2', '3', '4', '6',
                       '0.0', '1.0', '2.0', '3.0', '4.0'}

# D001 の対象外。KUKA / WorkVisual が定型で入れる宣言
SKIP_UNUSED = {'SUCCESS', 'LAST_BASIS', 'LAST_TP_PARAMS', 'LAST_ARC_PARAMS'}


# ---------------------------------------------------------------- 字句

def strip_comment(line):
    """; 以降を落とす。文字列リテラル内の ; は残す。"""
    out = []
    in_str = False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == ';' and not in_str:
            break
        out.append(ch)
    return ''.join(out)


def comment_of(line):
    """; 以降だけを返す。無ければ空文字。"""
    code = strip_comment(line)
    return line[len(code):]


def split_top_level(s, sep=','):
    """括弧と波括弧の深さ 0 にある sep だけで分割する。"""
    parts, buf, depth, in_str = [], [], 0, False
    for ch in s:
        if ch == '"':
            in_str = not in_str
        if not in_str:
            if ch in '({[':
                depth += 1
            elif ch in ')}]':
                depth -= 1
            elif ch == sep and depth == 0:
                parts.append(''.join(buf))
                buf = []
                continue
        buf.append(ch)
    parts.append(''.join(buf))
    return [p.strip() for p in parts]


# ---------------------------------------------------------------- 指摘

class Report(object):
    def __init__(self, quiet=False, only=None, fmt='text'):
        self.items = []
        self.quiet = quiet
        self.fmt = fmt
        self.only = None
        if only:
            self.only = set(f.strip().upper() for f in only.split(',') if f.strip())

    def add(self, path, line, code, msg, sev=ERROR):
        if self.only and code[0].upper() not in self.only:
            return
        if self.quiet and sev != ERROR:
            return
        self.items.append((path, line, code, msg, sev))

    def counts(self):
        c = {ERROR: 0, WARN: 0, INFO: 0}
        for _, _, _, _, sev in self.items:
            c[sev] += 1
        return c

    def dump_vscode(self):
        """path:line:col: severity [code] msg  -- VS Code の problemMatcher が読む形式"""
        sev_word = {ERROR: 'error', WARN: 'warning', INFO: 'info'}
        for path, line, code, msg, sev in sorted(
                self.items, key=lambda t: (t[0], SEV_ORDER[t[4]], t[1])):
            print("%s:%d:1: %s [%s] %s"
                  % (os.path.abspath(path), max(line, 1), sev_word[sev], code, msg))
        c = self.counts()
        print("krlcheck: ERROR %d / WARN %d / INFO %d" % (c[ERROR], c[WARN], c[INFO]))
        return 1 if c[ERROR] else 0

    def dump(self):
        if self.fmt == 'vscode':
            return self.dump_vscode()
        if not self.items:
            print("指摘なし")
            print("")
            print("注意: 構文・識別子の実在・型は検査していない。")
            print("      WorkVisual でのコンパイルが別に必要 (04-verification.md T1)。")
            return 0
        by_file = defaultdict(list)
        for path, line, code, msg, sev in self.items:
            by_file[path].append((SEV_ORDER[sev], line, code, msg, sev))
        for path in sorted(by_file):
            print("=== %s" % path)
            for _, line, code, msg, sev in sorted(by_file[path]):
                loc = (":%d" % line) if line else ""
                print("  %-5s [%-3s] %s%s  %s"
                      % (sev, code, os.path.basename(path), loc, msg))
            print("")
        c = self.counts()
        print("ERROR %d 件 / WARN %d 件 / INFO %d 件" % (c[ERROR], c[WARN], c[INFO]))
        print("")
        print("注意: 構文・識別子の実在・型は検査していない。")
        print("      WorkVisual でのコンパイルが別に必要 (04-verification.md T1)。")
        return 1 if c[ERROR] else 0


# ---------------------------------------------------------------- 正規表現

HEADER_RE = re.compile(r'^\s*&(ACCESS|REL|PARAM)\b', re.I)
DEF_RE = re.compile(r'^\s*(?:GLOBAL\s+)?DEF\s+([A-Za-z_]\w*)\s*(\((.*?)\))?\s*$', re.I)
DEFFCT_RE = re.compile(r'^\s*(?:GLOBAL\s+)?DEFFCT\s+\w+\s+([A-Za-z_]\w*)\s*(\((.*?)\))?\s*$', re.I)
DEFDAT_RE = re.compile(r'^\s*DEFDAT\s+([A-Za-z_]\w*)', re.I)
DECL_RE = re.compile(
    r'^\s*(?:GLOBAL\s+)?DECL\s+(?:GLOBAL\s+)?(?:CONST\s+)?([A-Za-z_]\w*)\s+(.+)$', re.I)
CALL_RE = re.compile(r'\b([A-Za-z_]\w*)\s*\(')

BLOCKS = [
    (re.compile(r'^\s*(?:GLOBAL\s+)?DEF\s+', re.I),    re.compile(r'^\s*END\s*$', re.I),       'DEF', 'END'),
    (re.compile(r'^\s*(?:GLOBAL\s+)?DEFFCT\s+', re.I), re.compile(r'^\s*ENDFCT\s*$', re.I),    'DEFFCT', 'ENDFCT'),
    (re.compile(r'^\s*DEFDAT\s+', re.I),               re.compile(r'^\s*ENDDAT\s*$', re.I),    'DEFDAT', 'ENDDAT'),
    (re.compile(r'^\s*IF\b.*\bTHEN\b', re.I),          re.compile(r'^\s*ENDIF\s*$', re.I),     'IF', 'ENDIF'),
    (re.compile(r'^\s*FOR\b', re.I),                   re.compile(r'^\s*ENDFOR\s*$', re.I),    'FOR', 'ENDFOR'),
    (re.compile(r'^\s*WHILE\b', re.I),                 re.compile(r'^\s*ENDWHILE\s*$', re.I),  'WHILE', 'ENDWHILE'),
    (re.compile(r'^\s*SWITCH\b', re.I),                re.compile(r'^\s*ENDSWITCH\s*$', re.I), 'SWITCH', 'ENDSWITCH'),
    (re.compile(r'^\s*LOOP\s*$', re.I),                re.compile(r'^\s*ENDLOOP\s*$', re.I),   'LOOP', 'ENDLOOP'),
]


# ---------------------------------------------------------------- 構造検査

def check_structure(path, lines, stem, ext, rep):
    # N1 ヘッダ
    if not lines or not HEADER_RE.match(lines[0]):
        rep.add(path, 1, 'V6',
                '1行目が &ACCESS 等のヘッダでない (先頭行: %r)'
                % (lines[0][:40] if lines else ''), WARN)

    # N12 モジュール名とファイル名
    modname = None
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        m = DEFDAT_RE.match(code) or DEFFCT_RE.match(code) or DEF_RE.match(code)
        if m:
            modname = m.group(1)
            if modname.upper() != stem.upper():
                rep.add(path, i, 'N12',
                        '%s 名 %s がファイル名 %s と一致しない。'
                        'ファイル名を変えたら中の名前も変えること'
                        % ('DEFDAT' if ext == '.dat' else 'DEF', modname, stem))
            break

    # V1 ファイル名は <機能名>_<YYYYMMDD>[a-z]
    m = re.match(r'^([A-Za-z][A-Za-z0-9]*)_(\d{4})(\d{2})(\d{2})([a-z]?)$', stem)
    if not m:
        rep.add(path, 1, 'V1',
                'ファイル名 %s が <機能名>_<YYYYMMDD> の形式でない '
                '(同日の2版目以降は末尾に a, b, ...)' % stem)
    else:
        mo, dd = int(m.group(3)), int(m.group(4))
        if not (1 <= mo <= 12 and 1 <= dd <= 31):
            rep.add(path, 1, 'V1', '日付 %s%s%s が暦としておかしい'
                    % (m.group(2), m.group(3), m.group(4)))
        if len(m.group(1)) > 15:
            rep.add(path, 1, 'V1',
                    '機能名 %s が %d 文字。日付 9 文字と合わせて識別子 24 文字を超える'
                    % (m.group(1), len(m.group(1))))

    # P4 FOLD 対応 (FOLD はコメント行なので生行で見る)
    fold_stack = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.match(r'^;\s*FOLD\b', s, re.I):
            fold_stack.append(i)
        elif re.match(r'^;\s*ENDFOLD\b', s, re.I):
            m = re.match(r'^;\s*ENDFOLD(.*)$', s, re.I)
            tail = m.group(1).strip()
            if tail and not tail.startswith('('):
                rep.add(path, i, 'P4',
                        ';ENDFOLD に文字が連結している (%r)。FOLD が閉じない' % s)
            if fold_stack:
                fold_stack.pop()
            else:
                rep.add(path, i, 'P4', '対応する ;FOLD のない ;ENDFOLD')
    for i in fold_stack:
        rep.add(path, i, 'P4', ';FOLD が閉じていない')

    # P4 ブロック対応
    stack = []
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        if not code.strip():
            continue
        for op_re, cl_re, op_name, cl_name in BLOCKS:
            if cl_re.match(code):
                if stack and stack[-1][0] == op_name:
                    stack.pop()
                else:
                    exp = stack[-1][0] if stack else 'なし'
                    rep.add(path, i, 'P4',
                            '%s が対応しない (開いているのは %s)' % (cl_name, exp))
                break
            if op_re.match(code):
                stack.append((op_name, i))
                break
    for op_name, i in stack:
        rep.add(path, i, 'P4', '%s が閉じていない' % op_name)

    # P4 中身のない IF ブロック
    for i, line in enumerate(lines, 1):
        code = strip_comment(line).strip()
        if not (re.match(r'^IF\b', code, re.I) and re.search(r'\bTHEN\b', code, re.I)):
            continue
        j, has_stmt = i, False
        while j < len(lines):
            cj = strip_comment(lines[j]).strip()
            if re.match(r'^(ENDIF|ELSE)\b', cj, re.I):
                break
            if cj:
                has_stmt = True
                break
            j += 1
        if not has_stmt:
            rep.add(path, i, 'P4', 'IF ブロックに実行文が無い', WARN)

    return modname


# ---------------------------------------------------------------- 命名検査

def parse_decls(lines):
    """[(name, line, type, has_init, raw)] を返す。"""
    out = []
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        if not code.strip() or 'INTERRUPT' in code.upper():
            continue
        m = DECL_RE.match(code)
        if not m:
            continue
        typ, rest = m.group(1), m.group(2)
        for item in split_top_level(rest):
            nm = re.match(r'([A-Za-z_]\w*)', item)
            if nm:
                out.append((nm.group(1), i, typ.upper(), '=' in item, item))
    return out


def module_prefix(modname):
    """WBead_20260924 -> WB_ , SBead -> SB_ 。日付は除いて導く。導けなければ None。"""
    if not modname:
        return None
    modname = re.sub(r'_\d{8}[a-z]?$', '', modname)
    m = re.match(r'^([A-Za-z])[a-z]*([A-Za-z])', modname)
    return (m.group(1) + m.group(2) + '_').upper() if m else None


def check_naming(path, lines, modname, ext, rep):
    is_dat = (ext == '.dat')
    prefix = module_prefix(modname)

    for name, i, typ, has_init, raw in parse_decls(lines):
        up = name.upper()
        if up in SKIP_UNUSED:
            continue

        # N1 長さと文字種
        if len(name) > MAX_IDENT:
            rep.add(path, i, 'N1',
                    '%s は %d 文字。上限は %d 文字' % (name, len(name), MAX_IDENT))
        if not re.match(r'^[A-Za-z][A-Za-z0-9_$]*$', name):
            rep.add(path, i, 'N1', '%s に使えない文字が含まれる' % name)

        # N7 禁止する形
        if GENERATED_IDENT.match(name):
            rep.add(path, i, 'N7',
                    '%s はインラインフォームの自動生成形。手書きでは使わない' % name)
        if len(name) == 1:
            rep.add(path, i, 'N7', '%s は1文字。用途が分かる名前にする' % name)

        # N8 I[] との衝突
        if up in ('I', 'J', 'K', 'N'):
            rep.add(path, i, 'N8',
                    '%s は W3D のグローバル配列 I[] と衝突しうる '
                    '(KRL は大文字小文字を区別しない)' % name, WARN)

        has_prefix = any(up.startswith(p.upper()) for p in AREA_PREFIXES)

        arc_data = re.match(r'^(WDAT|WP)\d+$', up) is not None
        if is_dat:
            # N2 スコープと領域 ( ArcTech のデータセット名は N11 により対象外 )
            if not has_prefix and not arc_data:
                rep.add(path, i, 'N2',
                        '%s はモジュールレベルだが領域接頭辞 (%s) が無い'
                        % (name, ' / '.join(AREA_PREFIXES)), WARN)
            elif prefix and not arc_data and not up.startswith(prefix):
                rep.add(path, i, 'N2',
                        '%s がこのモジュールの接頭辞 %s を使っていない'
                        % (name, prefix), INFO)

            # S2 初期値
            if not has_init:
                rep.add(path, i, 'S2',
                        '%s に初期値が無い。.dat の未初期化宣言は静かに失敗する' % name)
            elif typ in ('FRAME', 'POS', 'E6POS'):
                missing = [c for c in ('X', 'Y', 'Z', 'A', 'B', 'C')
                           if not re.search(r'[{,]\s*%s\s' % c, raw, re.I)]
                if missing:
                    rep.add(path, i, 'S2',
                            '%s が部分初期化 (%s が未指定)'
                            % (name, ','.join(missing)), WARN)

            # N4 単位サフィックス
            if typ == 'REAL' and not name.endswith(UNIT_SUFFIX):
                rep.add(path, i, 'N4',
                        'REAL %s に単位サフィックスが無い (Mm / MPerSec / Sec / Deg ...)'
                        % name, WARN)

            # N6 否定形のブール名
            if typ == 'BOOL' and re.search(r'(^|_)(not|no)[A-Z_]', name):
                rep.add(path, i, 'N6', '%s は否定形のブール名' % name, WARN)
        else:
            if has_prefix:
                rep.add(path, i, 'N2',
                        '%s はローカルだが領域接頭辞が付いている。'
                        '接頭辞はモジュールレベルの印' % name, WARN)


def check_tags(path, lines, rep):
    """N10 タグ"""
    for i, line in enumerate(lines, 1):
        cm = comment_of(line)
        for m in re.finditer(r'@(\w+)', cm):
            tag = m.group(1).upper()
            if tag not in TAGS:
                rep.add(path, i, 'N10',
                        '未登録のタグ @%s。使えるのは %s'
                        % (m.group(1), ' / '.join('@' + t for t in TAGS)), WARN)
                continue
            if tag == 'OFFLINE':
                rep.add(path, i, 'N10',
                        '@OFFLINE タグが残っている。実機投入前に戻すこと')
            elif tag == 'ASSUME':
                window = ' '.join(comment_of(l) for l in lines[i - 1:i + 5]).upper()
                if 'VERIFY' not in window:
                    rep.add(path, i, 'N10',
                            '@ASSUME に VERIFY: 行が無い。'
                            '消し方が書かれていない前提は消えない', WARN)


def check_version_header(path, lines, ext, rep):
    """V3 / T8 ヘッダの版と検証状態"""
    head = '\n'.join(comment_of(l) for l in lines[:60]).upper()
    if 'VERSION' not in head:
        rep.add(path, 1, 'V3',
                'ヘッダに VERSION 行が無い。実機のファイルからリポジトリを遡れない', WARN)
    if ext == '.src' and 'VERIFIED' not in head:
        rep.add(path, 1, 'T8',
                'ヘッダに VERIFIED ブロックが無い。どの検証段階まで通ったか記録すること',
                WARN)


# ---------------------------------------------------------------- 動作命令検査

def check_motion(path, lines, ext, rep):
    if ext != '.src':
        return

    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        if not code.strip():
            continue
        up = code.upper()

        # M1 BAS() 経由の機構
        for tok in BAS_TOKENS:
            if re.search(r'(?<![\w$])%s\b' % re.escape(tok), up):
                rep.add(path, i, 'M1',
                        '%s は BAS() 経由の機構。'
                        'システム変数に直接代入する方針' % tok, WARN)
        for case in BAS_CASES:
            if re.search(r'BAS\s*\(\s*%s' % re.escape(case), up):
                rep.add(path, i, 'M1',
                        'BAS(%s, ...) は何を設定するか文書化されていない。'
                        'システム変数に直接代入する' % case, WARN)

        # C1 $BASE への直接代入は外部キネマティクスの処理 (EX_BASE -> EK) を通らない
        if re.search(r'\$BASE\s*=\s*BASE_DATA\s*\[', up):
            rep.add(path, i, 'C1',
                    '$BASE = BASE_DATA[n] の直接代入。外部キネマティクスに割り当てたベースでは '
                    'EK() を通らず別の場所を指す。FDAT_ACT を設定して BAS(#FRAMES, 0) を使う')
        if re.search(r'\$TOOL\s*=\s*TOOL_DATA\s*\[|\$LOAD\s*=\s*LOAD_DATA\s*\[', up):
            rep.add(path, i, 'C1',
                    '$TOOL / $LOAD の直接代入。$ACT_TOOL の更新と負荷データの既定値処理が抜ける。'
                    'BAS(#FRAMES, 0) を使う', WARN)

        # M7 C_SPL
        if re.search(r'\bC_SPL\b', up):
            if not re.search(r'\b(SLIN|SPTP|SCIRC|SPL|ENDSPLINE)\b', up):
                rep.add(path, i, 'M7',
                        'C_SPL はスプライン動作専用。PTP/LIN/CIRC/_REL の近似は '
                        'C_PTP / C_DIS / C_ORI / C_VEL / C_APX', WARN)

        # P4 KRL に存在しない演算子 (KSS 8.7 SI 11.14)
        for pat, what in ((r'\bMOD\b', 'MOD (剰余)。一覧の算術演算子は + - * / のみ。'
                                          '偶数判定は ((n / 2) * 2) == n で書ける'),
                          (r'%', '% (剰余)'),
                          (r'!=', '!= 。KRL の不等号は <>'),
                          (r'&&|\|\|', '&& / || 。KRL は AND / OR'),
                          (r'\+\+|--(?!-)|\+=|-=|\*=|/=', '++ / += など。KRL に複合代入は無い')):
            if re.search(pat, code):
                rep.add(path, i, 'P4',
                        'KSS 8.7 の演算子一覧に無い: %s。'
                        '受け付けられるかは未確認' % what, WARN)
                break

        # M6 _REL の基準座標系
        if REL_RE.match(code) and not re.search(r'#(BASE|TOOL)\b', up):
            rep.add(path, i, 'M6', '_REL 動作に #BASE / #TOOL の明示が無い')
        # M6 絶対座標の PTP / LIN / CIRC は #BASE / #TOOL を取らない (KSS 8.7 SI 11.5)
        if (MOTION_RE.match(code) and not REL_RE.match(code)
                and re.search(r'#(BASE|TOOL)\b', up)):
            rep.add(path, i, 'M6',
                    '絶対座標の動作命令に #BASE / #TOOL が付いている。'
                    'KSS 8.7 の構文定義でこれを取るのは _REL 動作だけ。'
                    '受け付けられるかは未確認', WARN)

        # P4 ゼロ変位の相対移動
        if REL_RE.match(code):
            agg = re.search(r'\{([^}]*)\}', code)
            if agg:
                vals = re.findall(r'[XYZABC]\s+(-?\d+(?:\.\d+)?)', agg.group(1), re.I)
                if vals and all(float(v) == 0.0 for v in vals):
                    rep.add(path, i, 'P4', '変位がすべてゼロの相対移動', WARN)

    # M4 最初の動作命令
    first_motion_line = None
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        m = MOTION_RE.match(code)
        if m:
            first_motion_line = i
            if m.group(1).upper() != 'PTP':
                rep.add(path, i, 'M4',
                        '最初の動作命令が %s。完全な PTP でなければならない'
                        % m.group(1).upper(), WARN)
            break

    # M2 最初の動作より前のシステム変数設定
    if first_motion_line:
        head = ' '.join(strip_comment(l) for l in lines[:first_motion_line - 1]).upper()
        frames_by_bas = re.search(r'BAS\s*\(\s*#FRAMES', head) is not None
        for sv in REQUIRED_SYSVARS:
            if frames_by_bas and sv in ('$TOOL', '$BASE', '$LOAD'):
                continue
            pat = re.escape(sv) + r'\s*(\[[^\]]*\])?\s*='
            if not re.search(pat, head):
                rep.add(path, first_motion_line, 'M2',
                        '%s が最初の動作命令より前で設定されていない。'
                        'BAS(#INITMOV,0) の初期値に依存する' % sv, WARN)


def check_ini_fold(path, lines, ext, rep):
    """S6 BAS(#INITMOV) は最初の DEF の中だけ"""
    if ext != '.src':
        return
    def_lines = [i for i, l in enumerate(lines, 1)
                 if DEF_RE.match(strip_comment(l)) or DEFFCT_RE.match(strip_comment(l))]
    if len(def_lines) < 2:
        return
    second = def_lines[1]
    for i, line in enumerate(lines, 1):
        if i > second and re.search(r'BAS\s*\(\s*#INITMOV', strip_comment(line), re.I):
            rep.add(path, i, 'S6',
                    'サブプログラム内の BAS(#INITMOV,0)。'
                    '呼ぶたびに動作パラメータが既定値に戻る')


def check_params(path, lines, rep):
    """S8 転送モードの明示"""
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        m = DEF_RE.match(code) or DEFFCT_RE.match(code)
        if not m:
            continue
        args = m.group(3)
        if not args or not args.strip():
            continue
        for p in split_top_level(args):
            if not p:
                continue
            if not re.search(r':\s*(IN|OUT)\s*$', p, re.I):
                rep.add(path, i, 'S8', '引数 %s に :IN / :OUT の明示が無い' % p)


def check_literals(path, lines, ext, rep):
    """S2 処理部の数値リテラル"""
    if ext != '.src':
        return
    for i, line in enumerate(lines, 1):
        code = strip_comment(line).strip()
        if not code:
            continue
        if re.match(r'^(DECL|DEF|DEFFCT|END|FOR|ENDFOR|IF|ENDIF|ELSE|WHILE|'
                    r'ENDWHILE|SWITCH|CASE|DEFAULT|ENDSWITCH|LOOP|ENDLOOP|'
                    r'INTERRUPT|GLOBAL|BAS|RETURN)\b', code, re.I):
            continue
        if re.search(r'\bWAIT\s+SEC\s+-?\d', code, re.I):
            rep.add(path, i, 'S2',
                    'WAIT SEC にリテラル。待ち時間は .dat に置く', WARN)
            continue
        for m in re.finditer(r'(?<![\w.\[])(-?\d+\.\d+|-?\d+)(?![\w.\]])', code):
            tok = m.group(1).lstrip('-')
            if tok in STRUCTURAL_LITERALS:
                continue
            if re.search(r'\[\s*-?%s\s*\]' % re.escape(tok), code):
                continue
            rep.add(path, i, 'S2',
                    'リテラル %s が処理部にある。物理量は .dat に置く'
                    % m.group(1), INFO)
            break


# ---------------------------------------------------------------- ファイル単位

def check_file(path, rep):
    raw = open(path, 'rb').read()

    # N1 BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        rep.add(path, 1, 'N1', 'UTF-8 BOM が付いている。取り込み時にエラーになる')
        raw = raw[3:]

    text = raw.decode('utf-8', errors='replace')
    lines = [l.rstrip('\r') for l in text.split('\n')]

    base = os.path.basename(path)
    stem, ext = os.path.splitext(base)
    ext = ext.lower()

    # N1 非 ASCII (件数が多くなるので先頭行と合計だけ報告する)
    bad = []
    for i, line in enumerate(lines, 1):
        try:
            line.encode('ascii')
        except UnicodeEncodeError:
            bad.append(i)
    if bad:
        rep.add(path, bad[0], 'N1',
                '非 ASCII 文字を含む行が %d 行ある (最初は %d 行目)。'
                'コメントは ASCII 英語で書く' % (len(bad), bad[0]))

    modname = check_structure(path, lines, stem, ext, rep)
    check_naming(path, lines, modname, ext, rep)
    check_tags(path, lines, rep)
    check_version_header(path, lines, ext, rep)
    check_motion(path, lines, ext, rep)
    check_ini_fold(path, lines, ext, rep)
    check_params(path, lines, rep)
    check_literals(path, lines, ext, rep)

    # 収集 (グループ検査用)
    decls, defs, calls = [], {}, []
    for i, line in enumerate(lines, 1):
        code = strip_comment(line)
        if not code.strip():
            continue

        if 'INTERRUPT' not in code.upper():
            m = DECL_RE.match(code)
            if m:
                typ, rest = m.group(1), m.group(2)
                for item in split_top_level(rest):
                    nm = re.match(r'([A-Za-z_]\w*)', item)
                    if nm:
                        decls.append((nm.group(1), i, typ))

        md = DEF_RE.match(code) or DEFFCT_RE.match(code)
        if md:
            args = md.group(3)
            argc = 0 if (args is None or not args.strip()) else len(split_top_level(args))
            defs[md.group(1).upper()] = (i, argc)
            continue

        for cm in CALL_RE.finditer(code):
            nm = cm.group(1)
            if nm.upper() in ('IF', 'WHILE', 'UNTIL', 'RETURN', 'FOR', 'SWITCH', 'WAIT'):
                continue
            start = cm.end() - 1
            depth, j = 0, start
            while j < len(code):
                if code[j] == '(':
                    depth += 1
                elif code[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = code[start + 1:j]
            argc = 0 if not inner.strip() else len(split_top_level(inner))
            calls.append((nm.upper(), i, argc))

    return {'path': path, 'lines': lines, 'decls': decls, 'defs': defs,
            'calls': calls, 'modname': modname, 'ext': ext, 'stem': stem}


def check_group(infos, rep):
    """.src と .dat をまとめて見る検査。"""
    all_defs = {}
    for info in infos:
        for name, (line, argc) in info['defs'].items():
            all_defs[name] = (info['path'], line, argc)

    # S7 呼び出しの引数個数
    for info in infos:
        for name, line, argc in info['calls']:
            if name in all_defs:
                _, dline, dargc = all_defs[name]
                if argc != dargc:
                    rep.add(info['path'], line, 'S7',
                            '%s の引数が %d 個。定義は %d 個' % (name, argc, dargc))

    # P4 未使用の DECL
    body = []
    for info in infos:
        for i, line in enumerate(info['lines'], 1):
            body.append((info['path'], i, strip_comment(line)))

    for info in infos:
        for name, line, typ in info['decls']:
            if name.upper() in SKIP_UNUSED:
                continue
            pat = re.compile(r'\b' + re.escape(name) + r'\b', re.I)
            used = False
            for p, i, code in body:
                if p == info['path'] and i == line:
                    continue
                if pat.search(code):
                    used = True
                    break
            if not used:
                rep.add(info['path'], line, 'P4',
                        '%s %s は宣言されているが使われていない' % (typ, name), WARN)

    # N12 .src / .dat の対応
    exts = set(info['ext'] for info in infos)
    if exts == {'.src'}:
        rep.add(infos[0]['path'], 0, 'N12',
                '%s に対応する .dat がない' % infos[0]['stem'], WARN)


# ---------------------------------------------------------------- 実行

def collect(paths):
    files = []
    for p in paths:
        # Windows の引数渡しで紛れ込む引用符を落とす。正当なパスに " は含まれない
        p = p.strip().strip('"')
        if not os.path.exists(p):
            print("見つからない (無視): %s" % p)
            continue
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in names:
                    if n.lower().endswith(('.src', '.dat')):
                        files.append(os.path.join(root, n))
        else:
            files.append(p)
    return sorted(files)


def main(argv):
    args = [a for a in argv[1:]]
    quiet = '--quiet' in args
    only = None
    fmt = 'text'
    for a in list(args):
        if a.startswith('--format'):
            if '=' in a:
                fmt = a.split('=', 1)[1]
                args.remove(a)
            else:
                idx = args.index(a)
                if idx + 1 < len(args):
                    fmt = args[idx + 1]
                    args.pop(idx + 1)
                args.remove(a)
    for a in list(args):
        if a.startswith('--only'):
            if '=' in a:
                only = a.split('=', 1)[1]
                args.remove(a)
            else:
                idx = args.index(a)
                if idx + 1 < len(args):
                    only = args[idx + 1]
                    args.pop(idx + 1)
                args.remove(a)
    args = [a for a in args if not a.startswith('--')]

    if not args:
        print(__doc__)
        return 2
    files = collect(args)
    if not files:
        print("対象ファイルがない")
        return 2

    rep = Report(quiet=quiet, only=only, fmt=fmt)
    groups = defaultdict(list)
    for f in files:
        info = check_file(f, rep)
        groups[os.path.join(os.path.dirname(f), info['stem']).upper()].append(info)
    for _, infos in groups.items():
        check_group(infos, rep)

    if fmt != 'vscode':
        print("検査対象 %d ファイル" % len(files))
        print("")
    return rep.dump()


if __name__ == '__main__':
    # 例外で落ちると Python は 1 を返し、「ERROR あり」と区別できなくなる。
    # ツールの故障を検査結果として報告しないよう、専用の終了コードを返す。
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception:
        import traceback
        print("")
        print("!!! krlcheck 自身が異常終了した。これは検査結果ではない !!!")
        print("")
        traceback.print_exc()
        sys.exit(3)
