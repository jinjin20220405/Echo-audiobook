import re

# 章节标题识别的核心正则（暴露为模块级常量，方便测试和调试）
# 匹配：行首 + 1~3位阿拉伯数字 + 可选空白 + 分隔符（、. , 空格）+ 可选空白 + 标题文字
# 注意：只支持阿拉伯数字开头，不支持中文数字（一、xxx）
# 局限：若正文行以数字+分隔符开头（如"3、第三个问题"），会被误判为章节标题，M2 阶段暂不处理
CHAPTER_TITLE_PATTERN = r"^(\d{1,3})\s*[、.,\s]\s*(.+?)$"


def _extract_title(raw_title_line: str) -> str:
    """
    从原始章节标题行中提取纯标题，去除前导编号和分隔符。

    示例：
        '1、"我是"之意识'  → '"我是"之意识'
        '2. 对身体的执着'  → '对身体的执着'
        '3 当下'           → '当下'

    Args:
        raw_title_line: 完整的章节标题行（已清洗，无前导全角空格）

    Returns:
        纯标题字符串
    """
    m = re.match(CHAPTER_TITLE_PATTERN, raw_title_line.strip())
    if m:
        return m.group(2).strip()
    # 若正则未匹配（不应发生），原样返回
    return raw_title_line.strip()


def split_chapters(text: str) -> list[dict]:
    """
    把清洗后的全文切分成章节列表。

    切分逻辑：
    1. 用正则逐行扫描，识别所有数字章节标题（行首形如 "1、xxx"、"2.xxx"、"3 xxx"）
    2. 第一个章节标题前的所有内容打包为"前言"（chapter_num=0）
       - 如果文件没有任何数字章节标题，则全部内容作为前言返回
       - 如果文件开头就是章节标题（无前言内容），则不生成前言条目
    3. 按章节标题出现位置切分余下内容，每章一个字典

    Args:
        text: 已经过 read_txt() 清洗的全文字符串

    Returns:
        章节列表，每个元素为字典 {"chapter_num": int, "title": str, "content": str}
    """
    lines = text.split("\n")

    # 第一遍扫描：找到所有章节标题的行索引
    chapter_positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if re.match(CHAPTER_TITLE_PATTERN, line):
            chapter_positions.append((i, line))

    result: list[dict] = []

    # 情况一：没有任何章节标题，整个文件作为前言
    if not chapter_positions:
        result.append({
            "chapter_num": 0,
            "title": "前言",
            "content": text.strip(),
        })
        return result

    first_chapter_line_idx = chapter_positions[0][0]

    # 情况二：文件开头到第一个章节标题之间有内容 → 生成前言
    if first_chapter_line_idx > 0:
        preface_lines = lines[:first_chapter_line_idx]
        preface_content = "\n".join(preface_lines).strip()
        if preface_content:
            result.append({
                "chapter_num": 0,
                "title": "前言",
                "content": preface_content,
            })

    # 切分各章节
    for idx, (line_idx, raw_title) in enumerate(chapter_positions):
        chapter_num = idx + 1
        title = _extract_title(raw_title)

        # content 从标题行的下一行开始
        content_start = line_idx + 1
        # 到下一个章节标题行的前一行结束（或文件末尾）
        if idx + 1 < len(chapter_positions):
            content_end = chapter_positions[idx + 1][0]
        else:
            content_end = len(lines)

        content = "\n".join(lines[content_start:content_end]).strip()

        result.append({
            "chapter_num": chapter_num,
            "title": title,
            "content": content,
        })

    return result
