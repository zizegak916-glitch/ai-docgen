import argparse
import logging
import os
import sys
from typing import Sequence

from ai_docgen import __version__
from ai_docgen.analyzers import ChromeExtensionAnalyzer, AndroidAccessibilityAnalyzer, IOSAppAnalyzer
from ai_docgen.generators import MarkdownGenerator, HTMLGenerator
from ai_docgen.llm import LLMClient

logger = logging.getLogger(__name__)

PLATFORM_MAP = {
    "chrome": ChromeExtensionAnalyzer,
    "android": AndroidAccessibilityAnalyzer,
    "ios": IOSAppAnalyzer,
}


def detect_platform(path: str) -> str | None:
    if os.path.exists(os.path.join(path, "manifest.json")):
        return "chrome"
    if os.path.exists(os.path.join(path, "AndroidManifest.xml")):
        return "android"
    if os.path.exists(os.path.join(path, "Info.plist")) or os.path.exists(os.path.join(path, "Package.swift")):
        return "ios"
    return None


def cmd_analyze(args: argparse.Namespace) -> None:
    platform = args.platform
    if platform == "auto":
        platform = detect_platform(args.path)
        if not platform:
            print("无法自动检测平台类型，请使用 --platform 指定", file=sys.stderr)
            sys.exit(1)
        print(f"检测到平台: {platform}")

    analyzer_cls = PLATFORM_MAP.get(platform)
    if not analyzer_cls:
        print(f"不支持的平台: {platform}", file=sys.stderr)
        sys.exit(1)

    analyzer = analyzer_cls(args.path)
    result = analyzer.analyze()

    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_generate(args: argparse.Namespace) -> None:
    platform = args.platform
    if platform == "auto":
        platform = detect_platform(args.path)
        if not platform:
            print("无法自动检测平台类型，请使用 --platform 指定", file=sys.stderr)
            sys.exit(1)

    analyzer_cls = PLATFORM_MAP.get(platform)
    if not analyzer_cls:
        print(f"不支持的平台: {platform}", file=sys.stderr)
        sys.exit(1)

    analyzer = analyzer_cls(args.path)
    analysis = analyzer.analyze()

    output_dir = args.output or "docs"
    os.makedirs(output_dir, exist_ok=True)

    ext = "html" if args.format == "html" else "md"
    output_path = os.path.join(output_dir, f"{platform}_docs.{ext}")

    if args.format == "html":
        gen = HTMLGenerator()
    else:
        gen = MarkdownGenerator()

    gen.generate(analysis, output_path)
    print(f"文档已生成: {output_path}")


def cmd_enhance(args: argparse.Namespace) -> None:
    if not os.path.exists(args.doc_path):
        print(f"文件不存在: {args.doc_path}", file=sys.stderr)
        sys.exit(1)

    with open(args.doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    llm = LLMClient(provider=args.llm)
    enhanced = llm.enhance_documentation(content, "unknown")

    base, ext = os.path.splitext(args.doc_path)
    output_path = f"{base}_enhanced{ext}"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(enhanced)

    print(f"增强文档已保存: {output_path}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="ai-docgen",
        description="AI DocGen - 智能文档生成器",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="启用详细日志")

    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="分析项目")
    p_analyze.add_argument("path", help="项目路径")
    p_analyze.add_argument("--platform", choices=["chrome", "android", "ios", "auto"], default="auto")

    p_generate = sub.add_parser("generate", help="生成文档")
    p_generate.add_argument("path", help="项目路径")
    p_generate.add_argument("--platform", choices=["chrome", "android", "ios", "auto"], default="auto")
    p_generate.add_argument("--format", choices=["md", "html"], default="md")
    p_generate.add_argument("--output", default="docs")

    p_enhance = sub.add_parser("enhance", help="AI增强文档")
    p_enhance.add_argument("doc_path", help="文档文件路径")
    p_enhance.add_argument("--llm", choices=["deepseek", "openai"], default="deepseek")

    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    commands = {
        "analyze": cmd_analyze,
        "generate": cmd_generate,
        "enhance": cmd_enhance,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
