"""
M2 parser 模块单元测试
对应 docs/M2_SPEC.md 第 5 节
"""
import pytest
from pathlib import Path

from src.parser.txt_parser import read_txt
from src.parser.chapter_splitter import split_chapters, _extract_title

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_QA = FIXTURES_DIR / "sample_qa.txt"


# ---------------------------------------------------------------------------
# 辅助：加载 fixture 并解析，避免每个测试重复 IO
# ---------------------------------------------------------------------------

def _load_sample() -> list[dict]:
    text = read_txt(SAMPLE_QA)
    return split_chapters(text)


# ===========================================================================
# TestReadTxt
# ===========================================================================

class TestReadTxt:
    def test_basic_utf8_read(self):
        """正常 UTF-8 文件能读取，返回非空字符串"""
        text = read_txt(SAMPLE_QA)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_remove_full_width_space(self):
        """去除行首全角空格 \\u3000（中文排版段首缩进）"""
        text = read_txt(SAMPLE_QA)
        for line in text.split("\n"):
            assert not line.startswith("\u3000"), f"行首仍有全角空格: {repr(line[:20])}"

    def test_collapse_multiple_blank_lines(self):
        """3 个以上连续空行应合并为最多 2 个空行"""
        text = read_txt(SAMPLE_QA)
        assert "\n\n\n" not in text, "发现连续 3 个以上空行，未被合并"

    def test_file_not_found(self):
        """文件不存在时抛 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            read_txt("/不存在的路径/no_such_file.txt")

    def test_tmp_file_with_full_width_space(self, tmp_path):
        """临时文件验证全角空格清洗逻辑"""
        f = tmp_path / "test.txt"
        # 写入带全角空格段首的内容
        f.write_text("\u3000\u3000你好\n\u3000\u3000世界\n", encoding="utf-8")
        text = read_txt(f)
        assert "你好" in text
        assert not any(line.startswith("\u3000") for line in text.split("\n"))

    def test_collapse_blank_lines_tmp(self, tmp_path):
        """临时文件验证连续空行合并"""
        f = tmp_path / "test.txt"
        f.write_text("第一段\n\n\n\n\n第二段\n", encoding="utf-8")
        text = read_txt(f)
        assert "\n\n\n" not in text
        assert "第一段" in text
        assert "第二段" in text


# ===========================================================================
# TestSplitChapters
# ===========================================================================

class TestSplitChapters:
    def test_sample_qa_returns_4_items(self):
        """sample_qa.txt 应解析出 4 个条目（前言 + 3 章）"""
        result = _load_sample()
        assert len(result) == 4, f"期望 4 个条目，实际得到 {len(result)} 个"

    def test_preface_is_chapter_zero(self):
        """前言的 chapter_num 是 0，title 是 '前言'"""
        result = _load_sample()
        preface = result[0]
        assert preface["chapter_num"] == 0
        assert preface["title"] == "前言"

    def test_chapter_titles_stripped(self):
        """章节标题已去除前导编号和分隔符"""
        result = _load_sample()
        assert result[1]["title"] == "\u201c我是\u201d之意识", (
            f"第 1 章标题不符，实际: {repr(result[1]['title'])}"
        )
        assert result[2]["title"] == "对身体的执着"
        assert result[3]["title"] == "当下"

    def test_chapter_num_sequential(self):
        """章节编号从 1 开始依次递增"""
        result = _load_sample()
        nums = [r["chapter_num"] for r in result]
        assert nums == [0, 1, 2, 3]

    def test_chapter_content_excludes_title(self):
        """章节正文不包含标题行本身"""
        result = _load_sample()
        assert "1、" not in result[1]["content"], "第 1 章 content 中出现了标题行"
        assert "2、" not in result[2]["content"]
        assert "3、" not in result[3]["content"]

    def test_chapter_content_includes_qa(self):
        """章节正文包含问答内容（全角冒号 ：）"""
        result = _load_sample()
        # sample_qa.txt 使用全角冒号，如 "问：" "马："
        assert "问：" in result[1]["content"], "第 1 章 content 中未找到 '问：'"
        assert "马：" in result[1]["content"], "第 1 章 content 中未找到 '马：'"

    def test_preface_content(self):
        """前言正文包含传记性内容（M2_SPEC 5.4 验收标准）"""
        result = _load_sample()
        assert "当被问及他的出生日期" in result[0]["content"]

    def test_chapter1_content(self):
        """第 1 章正文包含指定文字（M2_SPEC 5.4 验收标准）"""
        result = _load_sample()
        assert "每天早晨醒来时" in result[1]["content"]

    def test_chapter2_content(self):
        """第 2 章正文包含指定文字（M2_SPEC 5.4 验收标准）"""
        result = _load_sample()
        assert "马哈拉吉，你坐在我的面前" in result[2]["content"]

    def test_chapter3_content(self):
        """第 3 章正文包含指定文字（M2_SPEC 5.4 验收标准）"""
        result = _load_sample()
        assert "我的身体和我的真实存在都没有问题" in result[3]["content"]

    def test_no_chapter_titles(self):
        """整个文件没有章节标题时，全部作为前言返回"""
        text = "这是一段没有章节标题的纯文本。"
        result = split_chapters(text)
        assert len(result) == 1
        assert result[0]["chapter_num"] == 0
        assert result[0]["title"] == "前言"

    def test_no_preface(self):
        """文件开头就是章节标题时，不生成前言条目"""
        text = "1、第一章\n问：你好。\n马：你好。"
        result = split_chapters(text)
        assert len(result) == 1
        assert result[0]["chapter_num"] == 1

    def test_multiple_chapters_no_preface(self):
        """多章节、无前言情形"""
        text = "1、第一章\n内容A\n\n2、第二章\n内容B"
        result = split_chapters(text)
        assert len(result) == 2
        assert result[0]["chapter_num"] == 1
        assert result[0]["title"] == "第一章"
        assert "内容A" in result[0]["content"]
        assert result[1]["chapter_num"] == 2
        assert result[1]["title"] == "第二章"
        assert "内容B" in result[1]["content"]


# ===========================================================================
# TestExtractTitle
# ===========================================================================

class TestExtractTitle:
    def test_pattern_with_dunhao(self):
        """1、xxx 格式（顿号分隔）"""
        assert _extract_title("1、\u201c我是\u201d之意识") == "\u201c我是\u201d之意识"

    def test_pattern_with_dot(self):
        """2. xxx 格式（英文点分隔）"""
        assert _extract_title("2. 对身体的执着") == "对身体的执着"

    def test_pattern_with_space(self):
        """3 xxx 格式（空格分隔）"""
        assert _extract_title("3 当下") == "当下"

    def test_three_digit_chapter(self):
        """3 位数章节号"""
        assert _extract_title("100、百章") == "百章"
