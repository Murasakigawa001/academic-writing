#!/usr/bin/env python3
"""核验"压缩到限额 + 附录迁移"之后的稿件：字数、交叉引用、重复句、字符与体例异常、表注、页数。

用法：
    python3 verify_condensed.py output/*.docx --main output/main.docx --limit <N>
    python3 verify_condensed.py output/*.docx --main output/正文.docx --limit <N> --unit chars --lang zh

    <N> 是本次任务要求的上限（用户给定 / 载体规定 / 折算所得），脚本不预设任何数值；
    不传 --limit 时只报现状，并在报告里提示"上限未指定"。

要点：把正文、附录、图表一起传——脚本靠"全文出现了哪些章节号/附录字母/表号/图号"
判断引用是否有效，只传附录会把正文里的表号全判成失效引用。

输出是一份可读报告；每类问题给"定位短语"，便于回到原文修改。
退出码 1 表示发现需要处理的问题（便于接入循环）。
"""
import sys, re, argparse, glob, os, subprocess
from collections import Counter

try:
    import docx
except ImportError:
    sys.exit("需要 python-docx: pip install python-docx")

CJK = re.compile(r'[\u4e00-\u9fff]')
AMERICAN = {
    r'\bprogrammeme\b': 'programme',
    r'\bprogram\b(?= of study)': 'programme',
    r'\bpracticed\b': 'practised',
    r'\bpracticing\b': 'practising',
    r'\bto practice\b': 'to practise',
    r'\bcentreed\b': 'centred',
    r'\bhonoree(s)?\b': r'honouree\1',
    r'\bhonors\b': 'honours',
    r'\bhonored\b': 'honoured',
    r'\bdefense\b': 'defence',
    r'\bfavor(s|ed|ing)?\b': r'favour\1',
    r'\blabor\b': 'labour',
    r'\bMHRSS\b': 'MOHRSS',
}
WORDNUM = re.compile(
    r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)'
    r'([\s-](one|two|three|four|five|six|seven|eight|nine))?\s+per cent',
    re.I)


def load(path):
    """返回 (段落文本列表, 表格单元格文本列表, 段落对象列表)"""
    d = docx.Document(path)
    paras = [p for p in d.paragraphs]
    cells = []
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                cells.append(c.text.strip())
    return [p.text.strip() for p in paras], cells, paras


def all_text(path):
    paras, cells, _ = load(path)
    return paras + cells


def word_count_before(path, stop_pattern=r'^References\b', unit='words'):
    """返回 (计数, 截断处标题)。截断处找不到时返回全文计数并提示。"""
    paras, cells, _ = load(path)
    total, cut = 0, None
    for t in paras:
        if re.match(stop_pattern, t, re.I):
            cut = t
            break
        total += len(t.split()) if unit == 'words' else len(re.sub(r'\s', '', t))
    return total, cut


def inventory(paths):
    """收集全稿的结构：章节号、附录字母、表号、图号。"""
    secs, apps, tabs, figs = set(), set(), set(), set()
    for f in paths:
        for t in all_text(f):
            m = re.match(r'^(\d+(?:\.\d+)?)\.?\s+[A-Z]', t)
            if m and len(t) < 120:
                secs.add(m.group(1))
            m = re.match(r'^Appendix\s+([A-Z])\b', t)
            if m:
                apps.add(m.group(1))
            for m in re.finditer(r'^(?:Table|Tableau)\s+([A-Z]?\d+)[.:]', t):
                tabs.add(m.group(1))
            for m in re.finditer(r'^(?:Fig\.|Figure)\s+(\d+)[.:]', t):
                figs.add(m.group(1))
    return secs, apps, tabs, figs


def check_refs(paths, secs, apps, tabs, figs):
    out = []
    for f in paths:
        for t in all_text(f):
            for m in re.finditer(r'Sections?\s+(\d+(?:\.\d+)?)', t):
                if m.group(1) not in secs and len(m.group(1)) > 1:
                    out.append((os.path.basename(f), 'section', m.group(1),
                                t[max(0, m.start() - 60):m.end() + 30]))
            for m in re.finditer(r'Appendix\s+([A-Z])(?:\.\d+)*', t):
                if m.group(1) not in apps:
                    out.append((os.path.basename(f), 'appendix', m.group(1), t[:90]))
            for m in re.finditer(r'Table\s+([A-Z]?\d+)', t):
                if m.group(1) not in tabs:
                    out.append((os.path.basename(f), 'table', m.group(1),
                                t[max(0, m.start() - 50):m.end() + 20]))
            for m in re.finditer(r'Figures?\s+(\d+)', t):
                if m.group(1) not in figs:
                    out.append((os.path.basename(f), 'figure', m.group(1),
                                t[max(0, m.start() - 50):m.end() + 20]))
    return out


def duplicates(paths, cross_file=False):
    """同一文件内重复的整句。默认不跨文件比较：附录常常是正文某节的完整版，
    跨文件的同句属于正常结构，跨文件去重会误导修改。"""
    per_file = {}
    for f in paths:
        sents = []
        for t in all_text(f):
            if len(t.split()) < 7:
                continue
            for s in re.split(r'(?<=[.!?])\s+(?=[A-Z"“(])', t):
                s = s.strip()
                if len(s.split()) > 10:
                    sents.append(s)
        per_file[f] = sents
    if cross_file:
        c = Counter(s for v in per_file.values() for s in v)
        return [(s, n) for s, n in c.items() if n > 1]
    out = []
    for f, sents in per_file.items():
        c = Counter(sents)
        out += [(s, n) for s, n in c.items() if n > 1]
    return out


CODE_HINTS = ('<-', 'function(', 'seq_len', 'cumsum(', 'outer(', 'sum(', 'paste(',
              'setNames(', 'round(', 'rep(', '==', '$', '\"', '=', '),', '[');
CODE_SIGNATURE = re.compile(r'^Listing\s+[A-Z]?\d+|^#\s|^\s{2,}')

def is_code(t):
    """代码行/脚本块：不参与字符与体例检查。

    R/Stata 片段没有统一的语法边界，这里用"特征符号密度 + 无句末标点"判定，
    宁可漏报（脚本里的引号、星号本来也不该改），不要误报正文。
    """
    if CODE_SIGNATURE.search(t):
        return True
    hits = sum(t.count(h) for h in CODE_HINTS)
    return hits >= 1 and not re.search(r'[.!?]\s|。$', t)


def char_checks(paths, lang='en'):
    issues = []
    for f in paths:
        for t in all_text(f):
            if is_code(t):
                continue
            if lang == 'en' and CJK.search(t):
                issues.append((f, 'CJK 混入', t[:80]))
            if lang == 'zh' and re.search(r'[\u4e00-\u9fff][,;:!?]|[,;:!?][\u4e00-\u9fff]', t):
                issues.append((f, '中文里用了半角标点', t[:80]))
            if re.search(r'(?<!\d)%(?!\d)', t) and len(t.split()) > 4:
                issues.append((f, '% 符号', t[:80]))
            if '*' in t and not re.search(r'^#|\$|<-|==|\* ', t):
                issues.append((f, '星号', t[:80]))
            # 公式（OMML）在纯文本里留空，抽出时会形成 "… .  and ." 这类双空格，不是排版问题
            # 公式（OMML）在纯文本里留空：一段里出现多处双空格时多半是公式占位，不是排版问题
            eq_gap = re.search(r'[.,;]\s{2,}(and|or|is|are|,)|\s{2,}[.,;]', t)
            if t.count('  ') < 3 and not eq_gap and re.search(r'[A-Za-z,.;:)]  [A-Za-z(“]', t):
                issues.append((f, '双空格', t[:80]))
            if '"' in t and not t.startswith(' ') and '=' not in t:
                issues.append((f, '直引号', t[:80]))
    return issues


def style_checks(paths, lang='en'):
    issues = []
    for f in paths:
        for t in all_text(f):
            if is_code(t):
                continue
            if lang != 'en':
                continue
            for pat, fix in AMERICAN.items():
                m = re.search(pat, t, re.I)
                if m:
                    issues.append((f, '拼写', m.group(0), '→ ' + str(fix), t[:70]))
            m = WORDNUM.search(t)
            if m:
                issues.append((f, '百分数写成单词', m.group(0), '→ 数字 + per cent', t[:70]))
            m = re.search(r'(?<![\d/])(\d+)-(\d+)(?![\d/])', t)
            if m and not re.search(r'[/.]', t[max(0, m.start() - 2):m.end() + 2]):
                issues.append((f, '范围用连字符', t[max(0, m.start() - 20):m.end() + 10],
                               '→ en dash', t[:70]))
            m = re.search(r'\((?:[A-Z][A-Za-z\'\-]+)\s+\d{4}', t)
            if m:
                issues.append((f, '引注缺逗号', m.group(0), '→ (Author, Year)', t[:70]))
    return issues


def table_notes(paths, window=6):
    """每个 'Table X.' 题注之后 window 段内应出现 Notes。"""
    missing = []
    for f in paths:
        paras, _, _ = load(f)
        for i, t in enumerate(paras):
            if re.match(r'^Table\s+[A-Z]?\d+[.:]', t):
                nxt = paras[i + 1:i + 1 + window]
                if not any(re.match(r'^Notes?$', q, re.I) for q in nxt):
                    missing.append((f, t[:70]))
    return missing


def heading_case(paths):
    """小节标题（X.n / X.n.n）应为 sentence case。

    只在同一个文件里该词确实也以小写出现过时才报——专名（Matthew、Shanghai、
    Chinese-language）在正文里通常全篇大写，据此排除，避免误报。
    """
    issues = []
    for f in paths:
        texts = all_text(f)
        body = ' '.join(texts)
        lower_seen = set(re.findall(r'\b[a-z][a-z\-]{2,}\b', body))
        for t in texts:
            m = re.match(r'^([A-Z]\.\d+(?:\.\d+)?)\s+(.+)$', t)
            if not m or len(t) > 110:
                continue
            words = m.group(2).split()
            caps = [w for w in words[1:]
                    if w[:1].isupper() and not w.isupper()
                    and w.lower().strip(',:;') in lower_seen]
            if caps:
                issues.append((f, t, caps))
    return issues


def page_count(paths):
    res = []
    for f in paths:
        pdf = os.path.splitext(f)[0] + '.pdf'
        if os.path.exists(pdf):
            try:
                out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
                m = re.search(r'Pages:\s+(\d+)', out)
                if m:
                    res.append((pdf, int(m.group(1))))
            except FileNotFoundError:
                pass
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--main', help='正文文件（用于词数与章节清单）')
    ap.add_argument('--limit', type=int, default=0,
                    help='正文上限（词数或字符数，见 --unit）；来自本次任务要求，不预设默认值')
    ap.add_argument('--requirement', default='',
                    help='限额来源的文字说明，如"投稿须知：正文不超 8,000 词"，会打印在报告里')
    ap.add_argument('--unit', choices=['words', 'chars'], default='words', help='限额单位')
    ap.add_argument('--lang', choices=['en', 'zh'], default='en', help='稿件语言，决定哪些体例检查适用')
    ap.add_argument('--ref-heading', default=r'References|Bibliography|Works Cited|参考文献',
                    help='正文与参考文献分界的标题正则')
    ap.add_argument('--quiet-dups', action='store_true')
    a = ap.parse_args()

    files = []
    for f in a.files:
        files.extend(glob.glob(f))
    files = [f for f in files if f.endswith('.docx')]
    if a.main and a.main not in files:
        files.append(a.main)

    print('=' * 70)
    print('文件：', ', '.join(os.path.basename(f) for f in files))

    if a.main:
        n, cut = word_count_before(a.main, a.ref_heading, a.unit)
        line = '正文%s（不含参考文献）：%d' % ('词数' if a.unit == 'words' else '字符数', n)
        if a.limit:
            line += '　上限 %d　余量 %d' % (a.limit, a.limit - n)
        else:
            line += '　上限未指定（由本次任务要求给定，用 --limit 传入）'
        if a.requirement:
            line += '\n限额来源：%s' % a.requirement
        print(line + ('　[按 "%s" 截断]' % cut if cut else '　[未找到 References 标题]'))

    secs, apps, tabs, figs = inventory(files)
    print('结构：章节 %d 个、附录 %s、表 %s、图 %s'
          % (len(secs), ''.join(sorted(apps)) or '—',
             ','.join(sorted(tabs, key=lambda x: (len(x), x))) or '—',
             ','.join(sorted(figs, key=int)) or '—'))

    refs = check_refs(files, secs, apps, tabs, figs)
    if a.lang == 'zh':
        print('（中文稿：英文拼写与 "per cent" 检查已跳过）')
    print('\n[交叉引用] %d 处可疑' % len(refs))
    for r in refs[:20]:
        print('  -', r[1], r[2], '｜', r[3][:110])

    if not a.quiet_dups:
        dups = duplicates(files)
        print('\n[重复句] %d 句出现两次以上' % len(dups))
        for s, k in dups[:12]:
            print('  x%d %s' % (k, s[:140]))

    ch = char_checks(files, a.lang)
    print('\n[字符] %d 处' % len(ch))
    for c in ch[:15]:
        print('  -', c[1], '｜', c[2][:110])

    st = style_checks(files, a.lang)
    print('\n[体例] %d 处' % len(st))
    for s in st[:20]:
        print('  -', s[1], '｜', s[2], '｜', s[3], '｜', s[4][:80])

    tn = table_notes(files)
    print('\n[表注] 缺 Notes 的表：%d' % len(tn))
    for t in tn:
        print('  -', t[1])

    hc = heading_case(files)
    print('\n[标题大小写] %d 处小节标题含额外大写' % len(hc))
    for h in hc[:12]:
        print('  -', h[1][:80], '｜', h[2])

    pc = page_count(files)
    if pc:
        print('\n[页数]')
        for p, n in pc:
            print('  %s  %d 页' % (os.path.basename(p), n))

    bad = len(refs) + len(ch) + len(tn) + (0 if a.quiet_dups else len(duplicates(files)))
    print('\n结论：%s' % ('需处理 %d 类问题（重复句、字符、表注、引用）' % bad if bad else '未发现结构性问题，仍需回读改动段落'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
