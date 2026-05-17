# M2 任务说明书:txt 解析 + 章节切分

> 这份文档是给 Claude Code 的 M2 阶段任务规格。Claude Code 作为 planner,据此把任务拆解给 Copilot CLI(worker)执行,或直接自己实现。

---

## 1. 任务目标

实现 `src/parser/` 模块。把一个符合"问答录"格式的 txt 文件读进来,切成章节列表,作为后续 M3(AI 角色拆分)的输入。

**这一步不涉及任何 AI 调用,纯 Python + 正则表达式。**

---

## 2. 输入与输出规格

### 2.1 输入

一个 UTF-8 编码的 txt 文件,符合以下结构特征:

- 文件开头可能有传记性介绍、引文、题记等"非章节"内容(我们统称为"前言")
- 后续是数字编号的章节,标题格式形如:
  - `1、"我是"之意识`
  - `2、对身体的执着`
  - `3、当下`
  - 编号可能是阿拉伯数字或中文数字(优先支持阿拉伯)
  - 编号后的分隔符可能是 `、` `.` `,` 或空格
- 章节内部由"问:..." / "马:..."(或类似前缀)开头的段落构成
- 段落之间用空行分隔
- 原文可能有全角空格作为段首缩进(中文排版习惯,如 `　　`)

**标准测试样本**:`tests/fixtures/sample_qa.txt`(《我就是那》节选,前 3 章 + 前言 + 题记)

### 2.2 输出

一个 Python 列表,每个元素是字典:

```python
[
    {
        "chapter_num": 0,
        "title": "前言",
        "content": "<第一个章节标题前的所有内容,合并为一个字符串>"
    },
    {
        "chapter_num": 1,
        "title": "\"我是\"之意识",
        "content": "<本章正文,包括所有问答>"
    },
    {
        "chapter_num": 2,
        "title": "对身体的执着",
        "content": "..."
    },
    {
        "chapter_num": 3,
        "title": "当下",
        "content": "..."
    }
]
```

### 2.3 输出字段规则

- `chapter_num`: 整数。前言固定为 0。正式章节按文件中出现的顺序编号(1, 2, 3...),**不**强制等于原文中的编号(虽然通常一致)
- `title`: 字符串。前言固定为 `"前言"`。正式章节的标题需要**去除前导编号和分隔符**:
  - `1、"我是"之意识` → `"我是"之意识`
  - `2、对身体的执着` → `对身体的执着`
- `content`: 字符串。章节正文。**已做清洗**(见 3.2 节)

---

## 3. 模块结构与函数签名

### 3.1 文件组织

```
src/parser/
├── __init__.py           # 暴露主要函数
├── txt_parser.py         # 文件读取 + 文本清洗
└── chapter_splitter.py   # 章节切分主逻辑
```

### 3.2 `txt_parser.py`

```python
from pathlib import Path

def read_txt(file_path: str | Path) -> str:
    """
    读取 txt 文件,返回清洗后的全文字符串。

    清洗规则:
    - 自动检测编码(优先 UTF-8,失败时尝试 GBK)
    - 去除 BOM 头
    - 统一换行符为 \\n
    - 去除每行行首/行尾的空白(包括全角空格 \\u3000)
    - 合并连续 3 个及以上的空行为 2 个空行
    - 去除文件首尾的空白字符

    Args:
        file_path: txt 文件路径

    Returns:
        清洗后的全文字符串

    Raises:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 编码无法识别(UTF-8 和 GBK 都失败)
    """
```

### 3.3 `chapter_splitter.py`

```python
def split_chapters(text: str) -> list[dict]:
    """
    把清洗后的全文切分成章节列表。

    切分逻辑:
    1. 用正则识别所有数字章节标题(行首形如 "1、xxx"、"2.xxx"、"3 xxx" 等)
    2. 第一个章节标题前的所有内容打包为"前言"(chapter_num=0)
       - 如果文件没有任何数字章节标题,则全部内容作为前言返回
       - 如果文件开头就是章节标题(无前言),则不生成前言条目
    3. 按章节标题出现位置切分余下内容,每章一个字典

    Args:
        text: 已经过 read_txt() 清洗的全文

    Returns:
        章节列表,格式见 spec 2.2 节
    """


def _extract_title(raw_title_line: str) -> str:
    """
    从原始章节标题行中提取纯标题。

    示例:
        '1、"我是"之意识'       → '"我是"之意识'
        '2. 对身体的执着'        → '对身体的执着'
        '3 当下'                 → '当下'
    """


# 章节标题识别的核心正则(暴露为模块级常量,方便测试和调试)
# 匹配:行首 + 1~3位阿拉伯数字 + 分隔符(、.,空格) + 标题文字
CHAPTER_TITLE_PATTERN = r'^(\d{1,3})\s*[、.,\s]\s*(.+?)$'
```

### 3.4 `__init__.py`

```python
from .txt_parser import read_txt
from .chapter_splitter import split_chapters

__all__ = ["read_txt", "split_chapters"]
```

---

## 4. 关键设计决策(避免 Claude Code 自由发挥)

### 4.1 编码处理
- 默认按 UTF-8 读
- UTF-8 失败时尝试 GBK(Windows 中文环境的老 txt 常用)
- 两个都失败抛 `UnicodeDecodeError`,不要再试更多编码——避免误判

### 4.2 章节标题识别
- 只识别**阿拉伯数字**开头的标题(`1、xxx`),**不**支持中文数字(`一、xxx`)
- 原因:简单可控,《我就是那》全书用阿拉伯数字。如果用户的书用中文数字,V2 再扩展
- 章节标题必须**独占一行**(整行只有"编号 + 分隔符 + 标题",没有正文混在一起)

### 4.3 关于"伪章节标题"的过滤
有可能正文里出现"3、第三个问题"这种行,被误判为章节标题。

**M2 阶段不处理这个边缘情况**——理由:
- 我们的目标书《我就是那》正文里没有这种伪标题
- 过早优化会让代码复杂
- 如果将来真碰到,M3 的 AI 校对环节可以兜底

**但要做的事**:在 README 和 docstring 里说明这个限制,让用户知道。

### 4.4 章节内容的边界
- 一个章节的 `content` = 从该章节标题的**下一行**开始,到下一个章节标题的**上一行**为止
- 章节标题本身**不**包含在 content 里(标题已经存到 title 字段)
- content 首尾的空行要去掉,中间的空行保留

### 4.5 前言的处理
- 前言 content = 文件开头到第一个章节标题前的所有内容(包括传记、引文、题记)
- 前言的 title 固定为 `"前言"`
- 如果文件第一行就是章节标题,**不**生成前言条目(返回的列表第一个元素就是 chapter_num=1)
- 如果文件从头到尾没有任何章节标题,整个文件作为前言返回(列表只有一个元素,chapter_num=0)

---

## 5. 测试要求

### 5.1 测试素材

把附件那段《我就是那》节选保存为 `tests/fixtures/sample_qa.txt`(老金会单独提供)。

### 5.2 单元测试文件

`tests/test_parser.py`,使用 pytest。

### 5.3 必须覆盖的测试用例

```python
class TestReadTxt:
    def test_basic_utf8_read(self):
        """正常 UTF-8 文件读取"""

    def test_remove_full_width_space(self):
        """去除全角空格 \\u3000(段首缩进)"""

    def test_collapse_multiple_blank_lines(self):
        """3 个以上连续空行合并为 2 个"""

    def test_file_not_found(self):
        """文件不存在时抛 FileNotFoundError"""


class TestSplitChapters:
    def test_sample_qa_returns_4_items(self):
        """sample_qa.txt 应解析出 4 个条目(前言 + 3 章)"""
        # 加载 fixture
        # 调用 read_txt + split_chapters
        # 断言 len(result) == 4

    def test_preface_is_chapter_zero(self):
        """前言的 chapter_num 是 0,title 是 '前言'"""

    def test_chapter_titles_stripped(self):
        """章节标题已去除前导编号"""
        # 断言 result[1]["title"] == '"我是"之意识'
        # 断言 result[2]["title"] == "对身体的执着"
        # 断言 result[3]["title"] == "当下"

    def test_chapter_content_excludes_title(self):
        """章节正文不包含标题行本身"""
        # 断言 '1、"我是"之意识' not in result[1]["content"]

    def test_chapter_content_includes_qa(self):
        """章节正文包含问答内容"""
        # 断言 "问:" in result[1]["content"]
        # 断言 "马:" in result[1]["content"]

    def test_no_chapter_titles(self):
        """整个文件没有章节标题时,全部作为前言"""
        text = "这是一段没有章节标题的纯文本。"
        result = split_chapters(text)
        assert len(result) == 1
        assert result[0]["chapter_num"] == 0
        assert result[0]["title"] == "前言"

    def test_no_preface(self):
        """文件开头就是章节标题时,不生成前言条目"""
        text = '1、第一章\n问:你好。\n马:你好。'
        result = split_chapters(text)
        assert len(result) == 1
        assert result[0]["chapter_num"] == 1


class TestExtractTitle:
    def test_pattern_with_dunhao(self):
        """1、xxx 格式"""
        assert _extract_title('1、"我是"之意识') == '"我是"之意识'

    def test_pattern_with_dot(self):
        """1. xxx 格式"""
        assert _extract_title('2. 对身体的执着') == "对身体的执着"

    def test_pattern_with_space(self):
        """1 xxx 格式"""
        assert _extract_title('3 当下') == "当下"
```

### 5.4 测试运行

```bash
cd H:\Ai-project\Echo-audiobook
pytest tests/test_parser.py -v
```

**验收标准**:所有测试用例通过,且用 `sample_qa.txt` 实测时:
- 解析出 4 个条目
- 前言 content 包含"当被问及他的出生日期"这句
- 第 1 章 title 是 `"我是"之意识`,content 包含"每天早晨醒来时"
- 第 2 章 title 是 `对身体的执着`,content 包含"马哈拉吉,你坐在我的面前"
- 第 3 章 title 是 `当下`,content 包含"我的身体和我的真实存在都没有问题"

---

## 6. 代码风格要求

- 遵循 PEP 8
- public 函数必须有 type hints
- public 函数必须有中文 docstring(说明做什么、入参、出参,简洁,不写废话)
- 内部辅助函数用 `_` 前缀
- 不要用 print 调日志,用 logging 模块(如果需要日志的话)
- **不要引入额外依赖**——只用 Python 标准库

---

## 7. 交付清单

完成 M2 时应当产出:

```
src/parser/
├── __init__.py
├── txt_parser.py
└── chapter_splitter.py

tests/
├── test_parser.py
└── fixtures/
    └── sample_qa.txt    (老金提供)
```

并且:

- `pytest tests/test_parser.py -v` 全部通过
- 用实际的 `sample_qa.txt` 测试,输出符合 5.4 验收标准

---

## 8. Git 工作流

- 在 `feature/m2-parser` 分支开发
- commit message 格式:`[M2] 简短描述`,例如:
  - `[M2] 实现 txt_parser 读取与清洗`
  - `[M2] 实现章节切分主逻辑`
  - `[M2] 补全单元测试`
- M2 完成后合并到 `main`,打 tag `v0.2.0-m2`

---

## 9. 给 Claude Code 的额外提示

- 这是项目的第二个里程碑,代码量不大(预计 200-300 行),不要过度工程化
- 遇到模糊点不要自由发挥,在 commit message 或 PR description 里标注"这里 spec 没说,我按 XX 处理了"
- 测试先行不强求,但所有 public 函数必须有对应测试
- 项目的整体上下文见根目录的 `CLAUDE.md` 和 `docs/ARCHITECTURE.md`
