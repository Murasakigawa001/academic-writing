# docx 定点修改的可靠写法

原则：**能从源重建的就重建，只有重建成本过高的文档才做定点修改**。一旦做了定点修改，要么把它写回源，要么把补丁写进构建脚本，否则下一轮重建会把它抹掉。

## 0 先判断改哪个

| 情形 | 做法 |
|---|---|
| 正文与附录正文由 md → docx 渲染 | 改 md，重跑 `build_*.py` |
| 表格、图、早期手工排版件 | 直接改 docx（python-docx），并把改动记进 `patch_*.py` 脚本 |
| 参考文献从原稿逐字复制 | 改构建脚本里的复制逻辑，不要改产物 |

## 1 整段替换文字（保留格式）

```python
def settext(p, text):
    if not p.runs:
        p.add_run(text); return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ''
```

`run[0]` 的字符格式（字号、斜体）会作用于整段。**先确认段内没有斜体 run**，否则会把斜体（书名、刊名）洗掉：

```python
if [r for r in p.runs if r.italic]:
    # 逐 run 替换，或改用跨 run 的正则重建
```

## 2 跨 run 的词

Word 常把一个词拆成两个 run（复制粘贴、拼写检查都会造成）。现象：`p.text` 里有目标词，但每个 run 里都没有。

```python
if 'programmeme' in p.text and 'programmeme' not in ''.join(r.text for r in p.runs):
    p.runs[0].text = p.text.replace('programmeme', 'programme')
    for r in p.runs[1:]:
        r.text = ''
```

## 3 拆段 / 插段

```python
import copy
from docx.text.paragraph import Paragraph

def split_para(p, marker):
    """在 marker 处把段落一分为二，返回后半段。"""
    t = p.text
    i = t.find(marker)
    if i <= 0:
        return None
    settext(p, t[:i].rstrip())
    np = copy.deepcopy(p._p)
    p._p.addnext(np)
    para = Paragraph(np, p._parent)
    settext(para, t[i:])
    return para
```

- 要在标题前插段：`heading._p.addprevious(new._p)`；连续插多段时**从后往前**插，否则顺序会颠倒。
- 插入后要重设段间距，否则沿用被复制段的格式（可能要 `space_before`、`keep_with_next`）。

## 4 新增表格行

```python
row = table.add_row()
for cell, val in zip(row.cells, values):
    cell.text = val
# 挪到指定位置
table._tbl.remove(row._tr)
target_row._tr.addprevious(row._tr)
```

`add_row()` 不计入表格样式之外的边框（三线表边框在表级，通常没问题），但字号可能继承默认值，需逐 cell 设 `runs[0].font.size`。

## 5 真斜体代替星号

Markdown 的 `*text*` 在 docx 里要落成 run 级格式：

```python
for part in re.split(r'(\*[^*]+\*)', line):
    if part.startswith('*') and part.endswith('*') and len(part) > 2:
        run = p.add_run(part[1:-1]); run.italic = True
    elif part:
        p.add_run(part)
```

## 6 公式（OMML）会干扰文本检查

含 Word 公式的段落，`p.text` 会把公式抽掉，留下 `the area  beneath` 这类空隙。判断"双空格"是否是问题，先看该段是否含 `oMath`：

```python
if p._p.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'):
    ...  # 文本拼接的空隙，不是排版错误
```

## 7 数字转单词的陷阱

若渲染脚本里有 `numwords()`（把 1–99 转英文单词），修改时必须：

- 标题行、代码块、`Table/Fig./Section` 编号、百分比、年份、月份、区间端点都要放过（维护一个 guard 正则）。
- 你手动写进去的 `"32 needles"` 会被转成 `"thirty-two needles"`——**不要反复改回数字**，那是脚本行为，与作者文风一致就保留。
- 改动 guard 后重跑全文，检查 `thirty November`、`1–four` 这类事故。

## 8 交付前

```bash
python3 build_main.py && python3 build_appendix.py && python3 merge_appendices.py
soffice --headless --convert-to pdf *.docx
pdfinfo *.pdf | grep Pages
python3 scripts/verify_condensed.py output/*.docx --main output/main.docx --limit <N>
```

页数、表数、词数三项与上一轮对比；数字跳变说明有内容被误删或重复。
