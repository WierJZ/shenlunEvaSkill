"""
申论 PDF 批量提取脚本
遍历国考和江苏的 PDF，提取文本保存为 Markdown 文件
"""
import os
import re
from pathlib import Path
from pypdf import PdfReader

BASE_DIR = Path("/workspace/shenlun/shenlunEvaSkill")
OUTPUT_DIR = BASE_DIR / "文本整理"

# 三个源目录
SOURCES = [
    {
        "src": BASE_DIR / "国考申论对比分年份",
        "out": OUTPUT_DIR / "国考",
        "label": "国考",
    },
    {
        "src": BASE_DIR / "申论答案对比（江苏）",
        "out": OUTPUT_DIR / "江苏" / "对比答案",
        "label": "江苏-对比答案",
        "exclude_dir": "江苏申论真题",  # 子目录单独处理
    },
    {
        "src": BASE_DIR / "申论答案对比（江苏）" / "江苏申论真题",
        "out": OUTPUT_DIR / "江苏" / "真题",
        "label": "江苏-真题",
    },
]


def clean_text(text: str) -> str:
    """清洗提取的文本"""
    # 去掉行首行尾多余空白
    text = text.strip()
    # 压缩连续 3 个以上空行为 2 个
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text


def extract_pdf(pdf_path: Path) -> str:
    """提取单个 PDF 的全部文本"""
    reader = PdfReader(str(pdf_path))
    texts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            texts.append(t.strip())
    return "\n\n".join(texts)


def process_directory(cfg: dict):
    """处理一个源目录"""
    src = cfg["src"]
    out = cfg["out"]
    label = cfg["label"]
    exclude = cfg.get("exclude_dir", "")

    if not src.exists():
        print(f"[SKIP] 目录不存在: {src}")
        return []

    out.mkdir(parents=True, exist_ok=True)

    results = []
    for item in sorted(src.iterdir()):
        if item.is_dir() and item.name == exclude:
            continue
        if not item.suffix.lower() == ".pdf":
            continue

        # 修正文件名中的双点
        safe_name = item.name.replace("..pdf", ".pdf")
        out_path = out / (safe_name.rsplit(".", 1)[0] + ".md")

        print(f"[{label}] 提取: {item.name}")
        raw_text = extract_pdf(item)
        clean = clean_text(raw_text)

        out_path.write_text(clean, encoding="utf-8")
        results.append(
            {
                "name": safe_name,
                "pages": len(PdfReader(str(item)).pages),
                "chars": len(clean),
            }
        )

    return results


def generate_index(all_results: list):
    """生成索引文件"""
    lines = [
        "# 申论文本整理索引\n",
        f"共 {sum(len(r) for r in all_results)} 份文档\n",
    ]

    labels = {
        "国考": "国考申论（对比答案）",
        "江苏-对比答案": "江苏申论（对比答案）",
        "江苏-真题": "江苏申论（真题卷）",
    }

    for i, (cfg, results) in enumerate(zip(SOURCES, all_results)):
        label = labels.get(cfg["label"], cfg["label"])
        lines.append(f"\n## {label}\n")
        lines.append(f"共 {len(results)} 份\n")

        total_chars = sum(r["chars"] for r in results)
        lines.append(f"总字数约 {total_chars:,}\n")

        for r in results:
            name = r["name"].replace(".pdf", "")
            lines.append(f"- {name} ({r['pages']}页, {r['chars']:,}字)")

    index_path = OUTPUT_DIR / "README.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n索引已生成: {index_path}")


def main():
    print("=" * 50)
    print("申论 PDF 文本提取")
    print("=" * 50)

    all_results = []
    for cfg in SOURCES:
        results = process_directory(cfg)
        all_results.append(results)
        print(f"  完成 {cfg['label']}: {len(results)} 个文件\n")

    generate_index(all_results)

    total = sum(len(r) for r in all_results)
    total_chars = sum(
        sum(item["chars"] for item in results) for results in all_results
    )
    print(f"\n全部完成! 共 {total} 个文件, 总字数约 {total_chars:,}")


if __name__ == "__main__":
    main()
