"""
申论文本格式化脚本 v2
- 清除页号
- 合并 PDF 硬换行为自然段落
- 规范化空白行
"""
import re
from pathlib import Path

TEXT_DIR = Path("/workspace/shenlun/shenlunEvaSkill/文本整理")

# ── 页号模式（先清除） ──────────────────────────────
PAGE_PATTERNS = [
    re.compile(r"第\s*\d+\s*页(\s*共\s*\d+\s*页)?"),  # 第 X 页, 第 X 页 共 Y 页
    re.compile(r"^\d+\s*/\s*\d+\s*$", re.MULTILINE),   # 1 / 12 (单独成行)
    re.compile(r"^\d{1,3}\s*$", re.MULTILINE),           # 裸数字(单独成行)
]


def clean_page_numbers(text: str) -> str:
    """清除页号"""
    for pat in PAGE_PATTERNS:
        text = pat.sub("", text)
    return text


# ── 关键分段标记（确保这些标签独立成行） ────────────
# 在这些标记前插入换行，确保它们不被合并到上一段
SECTION_MARKERS = [
    # 材料标记
    (re.compile(r"(材料\s*\d+)"), r"\n\1\n"),
    # 题目标记（第X题）- 但不匹配 "第X页"
    (re.compile(r"(第\s*\d+\s*题)"), r"\n\1\n"),
    # 给定资料、作答要求、注意事项、参考答案
    (re.compile(r"(给定资料)"), r"\n\1\n"),
    (re.compile(r"(作答要求)"), r"\n\1\n"),
    (re.compile(r"(注意事项)"), r"\n\1\n"),
    (re.compile(r"(参考答案)"), r"\n\1\n"),
    # 开头标题行 (年份+内容)
    (re.compile(r"(\d{4}\s*年[^\n]{0,30}?(?:题|卷|试卷))"), r"\n\1\n"),
    # 试卷头 (年份+年度+省份+申论)
    (re.compile(r"(\d{4}\s*年度[^\n]{0,30}?申论)"), r"\n\1\n"),
    # 题目序号标记 (第1题, 第2题...)
    (re.compile(r"(\n第\s*\d+\s*题\s*\n)"), r"\n\n\1\n"),
]


def enforce_section_breaks(text: str) -> str:
    """在关键标记前后插入换行"""
    for pattern, replacement in SECTION_MARKERS:
        text = pattern.sub(replacement, text)
    return text


# ── 标题/标签模式（这些块保持独立不参与合并） ────────
KEEP_SOLO_RE = re.compile(
    r"^\s*("
    r"材料\s*\d+|"
    r"题目[一二三四五六七八九十\d]+|"
    r"题目要求|"
    r"给定资料|"
    r"作答要求|"
    r"注意事项|"
    r"参考答案|"
    r"\d{4}\s*年.*(?:题|卷|试卷|申论)|"
    r"\d{4}年度.*申论|"
    r"粉笔|中公|华图|小红书|Kiwi|千寻|唐棣|"
    r"申论\s*$|半月谈|"
    r"第\s*\d+\s*[题章]|"
    r"[二三三四五六七八九十]、"
    r")\s*$"
)


def is_keep_solo(block_text: str) -> bool:
    """判断块是否应该保持独立"""
    text = block_text.strip()
    if not text:
        return True
    if KEEP_SOLO_RE.match(text):
        return True
    # 短标签 (≤15 字且包含答案来源关键词)
    if len(text) <= 15:
        if any(
            kw in text
            for kw in [
                "粉笔", "中公", "华图", "小红书", "Kiwi", "千寻", "唐棣",
                "半月谈", "站长", "袁东", "白鹭", "飞扬", "高资", "Kiwi",
                "导氮", "小马哥", "超格", "纵横", "蚂蚁", "今晚打老虎",
                "小张申论", "申论树人", "文曲星", "刘大师", "江牧云",
                "相丽君", "B站", "登科", "跃跃", "离别开出瓜", "HiLunaaa",
                "陈去病", "骐骥", "公考静姐", "ccm", "卡次西西",
                "蓝鲸镇少年", "春天有很好的风", "哲学走向荒野",
                "小萝卜申论", "星夜申论",
            ]
        ):
            return True
    return False


def merge_block(lines: list[str]) -> str:
    """将块内行合并为自然段落"""
    stripped = [l.strip() for l in lines if l.strip()]
    if not stripped:
        return ""
    return "".join(stripped)  # 中文直接拼接，不加空格


def format_text(text: str) -> str:
    """格式化整个文本"""
    # Step 0: 清除页号
    text = clean_page_numbers(text)

    # Step 1: 在关键标记前后插入分段
    text = enforce_section_breaks(text)

    # Step 2: 按空白行分块
    lines = text.split("\n")
    blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                blocks.append(current_block)
                current_block = []
            blocks.append([])  # 空行标记
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)

    # Step 3: 处理每个块
    output: list[str] = []
    prev_was_empty = False
    for block in blocks:
        if not block:
            if not prev_was_empty:
                output.append("")
                prev_was_empty = True
            continue
        prev_was_empty = False

        block_text = "".join(b.strip() for b in block).strip()
        if not block_text:
            continue

        # 检查是否是页号残留
        if re.match(r"^\d{1,3}$", block_text):
            continue

        if is_keep_solo(block_text):
            output.append(block[0].strip())
        else:
            merged = merge_block(block)
            if merged:
                output.append(merged)

    return "\n".join(output)


def main():
    print("=" * 50)
    print("申论文本格式化 v2")
    print("=" * 50)

    total_files = 0
    total_lines_before = 0
    total_lines_after = 0
    pages_removed = 0

    # 统计页号
    for root, dirs, files in os.walk(TEXT_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = Path(root) / fname
            original = fpath.read_text(encoding="utf-8")
            for pat in PAGE_PATTERNS:
                pages_removed += len(pat.findall(original))

    print(f"预估页号残留: {pages_removed} 处\n")

    pages_removed = 0
    for root, dirs, files in os.walk(TEXT_DIR):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            fpath = Path(root) / fname

            original = fpath.read_text(encoding="utf-8")
            lines_before = original.count("\n")

            for pat in PAGE_PATTERNS:
                pages_removed += len(pat.findall(original))

            formatted = format_text(original)
            lines_after = formatted.count("\n")

            fpath.write_text(formatted, encoding="utf-8")

            rel_path = fpath.relative_to(TEXT_DIR)
            reduction = lines_before - lines_after
            print(f"[OK] {rel_path}  行: {lines_before}→{lines_after} (-{reduction})")

            total_files += 1
            total_lines_before += lines_before
            total_lines_after += lines_after

    print(f"\n{'=' * 50}")
    print(f"全部完成!")
    print(f"文件数: {total_files}")
    print(f"总行数: {total_lines_before:,} → {total_lines_after:,}")
    print(f"清除页号: {pages_removed} 处")


if __name__ == "__main__":
    import os

    main()
