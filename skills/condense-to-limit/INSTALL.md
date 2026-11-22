# 安装说明

这个包里是一个技能（skill）：`condense-to-limit` —— 把已成型的长稿压缩到字数/词数/页数上限，并把被删内容迁入附录或补充材料。

技能本身是纯文本（Markdown 说明 + 一个 Python 核验脚本），没有任何隐藏依赖。

## 包结构

```
condense-to-limit/
├── SKILL.md                  技能主文件（frontmatter + 工作流）
├── manifest.json             名称、版本、文件清单、依赖
├── requirements.txt          Python 依赖（仅核验脚本需要）
├── INSTALL.md                本文件
├── references/
│   ├── appendix-design.md    附录/补充材料的设计规则
│   ├── style-checklist.md    体例清单（中英）
│   └── docx-surgery.md       直接改 docx 的可靠写法与坑
└── scripts/
    └── verify_condensed.py   核验脚本
```

## 一、装到 ima.copilot（本平台）

解压后把整个目录注册即可（该平台以目录为单位注册技能）：

```bash
unzip condense-to-limit.zip -d /sandbox/workspace/skills/
ima_skill_create -d /sandbox/workspace/skills/condense-to-limit/
```

注册后在新对话中说"把这篇压缩到 N 词，多出来的放附录"即可触发（N 是当下的要求，技能不预设数值）。

## 二、装到支持 SKILL.md 的通用 Agent

多数支持"技能目录"的 Agent 都认 `SKILL.md`（YAML frontmatter 里的 `name` 与 `description` 用于触发匹配）。把 `condense-to-limit/` 整个目录放进它的技能根目录即可，例如：

```bash
mkdir -p ~/.agent/skills
unzip condense-to-limit.zip -d ~/.agent/skills/
```

不要只复制 `SKILL.md`：`references/` 是按需加载的参考文档，`scripts/` 是可直接执行的核验脚本，缺了会退化成一个普通提示词。

## 三、不装也能用

`SKILL.md` 是一份自足的操作手册，人工照着做即可。核验脚本可以单独调用：

```bash
python3 condense-to-limit/scripts/verify_condensed.py output/*.docx \
    --main output/main.docx --limit <N>
```

## 依赖

| 依赖 | 用途 | 是否必需 |
|---|---|---|
| Python 3.9+ | 运行 `scripts/verify_condensed.py` | 用脚本时必需 |
| `python-docx` | 读写 .docx | 用脚本时必需 |
| LibreOffice（`soffice`） | docx → pdf，核页数 | 可选 |
| Poppler（`pdfinfo`） | 读 PDF 页数 | 可选 |

```bash
pip install -r requirements.txt
```

脚本只读取文件，不修改输入；未找到 PDF 时只是跳过页数检查，其余照常。

## 可选参数

```bash
--main PATH         正文文件（用于字数统计与章节清单），缺省则只查全部文件
--limit N           正文上限（本次任务给定；不给则只报现状）
--requirement TEXT  限额来源，如"投稿须知：正文不超 8,000 词"，会打印在报告里备查
--unit words|chars  限额单位（中文稿常用 chars）
--lang en|zh        稿件语言，决定拼写/标点检查项
--ref-heading REGEX 正文与参考文献的分界标题，默认 References|Bibliography|Works Cited|参考文献
--quiet-dups        只报结构性问题，不列重复句
```

注意：核验交叉引用时，**要把正文、附录、图表一起传**，脚本依赖全文出现的编号判断引用是否有效。

## 卸载

删掉技能目录即可，技能不写任何全局配置。
