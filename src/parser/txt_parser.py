import re
from pathlib import Path


def read_txt(file_path: str | Path) -> str:
    """
    读取 txt 文件，返回清洗后的全文字符串。

    清洗规则：
    - 自动检测编码（优先 UTF-8，失败时尝试 GBK）
    - 去除 BOM 头（utf-8-sig）
    - 统一换行符为 \\n
    - 去除每行行首/行尾的空白（包括全角空格 \\u3000）
    - 合并连续 3 个及以上的空行为 2 个空行
    - 去除文件首尾的空白字符

    Args:
        file_path: txt 文件路径（str 或 Path）

    Returns:
        清洗后的全文字符串

    Raises:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 编码无法识别（UTF-8 和 GBK 均失败）
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 优先 UTF-8（utf-8-sig 会自动去除 BOM）
    try:
        text = file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="gbk")
        except UnicodeDecodeError:
            raise UnicodeDecodeError(
                "utf-8",
                b"",
                0,
                1,
                f"无法识别文件编码（UTF-8 和 GBK 均失败）: {file_path}",
            )

    # 统一换行符为 \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 逐行清洗：去除行首/行尾的全角空格和普通空白
    # strip('\u3000 \t') 同时处理全角空格（\u3000）、半角空格和制表符
    lines = text.split("\n")
    cleaned_lines = [line.strip("\u3000 \t") for line in lines]
    text = "\n".join(cleaned_lines)

    # 合并连续 3 个及以上空行为 2 个空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 去除文件首尾空白
    text = text.strip()

    return text
