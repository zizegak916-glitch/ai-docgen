"""AI DocGen Web - 在线文档生成器"""
import os
import sys
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_docgen.analyzers import ChromeExtensionAnalyzer, AndroidAccessibilityAnalyzer, IOSAppAnalyzer
from ai_docgen.generators import MarkdownGenerator, HTMLGenerator

app = Flask(__name__, static_folder=".", static_url_path="")

UPLOAD_DIR = tempfile.mkdtemp(prefix="ai_docgen_")

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


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """接收上传的zip，分析并返回结果"""
    if "file" not in request.files:
        return jsonify({"error": "请上传项目文件（zip格式）"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "仅支持 zip 格式"}), 400

    platform = request.form.get("platform", "auto")

    # 解压到临时目录
    project_dir = tempfile.mkdtemp(dir=UPLOAD_DIR, prefix="proj_")
    zip_path = os.path.join(project_dir, "upload.zip")
    file.save(zip_path)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Check if zip has a single root folder
            names = zf.namelist()
            root_dirs = set()
            for n in names:
                parts = n.split("/")
                if parts[0]:
                    root_dirs.add(parts[0])

            zf.extractall(project_dir)
            os.remove(zip_path)

            # If single root folder, use it as project root
            if len(root_dirs) == 1:
                actual_root = os.path.join(project_dir, list(root_dirs)[0])
            else:
                actual_root = project_dir
    except zipfile.BadZipFile:
        shutil.rmtree(project_dir, ignore_errors=True)
        return jsonify({"error": "zip文件损坏"}), 400

    # 检测平台
    if platform == "auto":
        platform = detect_platform(actual_root)
        if not platform:
            shutil.rmtree(project_dir, ignore_errors=True)
            return jsonify({"error": "无法自动检测平台类型。请确认项目包含 manifest.json、AndroidManifest.xml 或 Info.plist"}), 400

    analyzer_cls = PLATFORM_MAP.get(platform)
    if not analyzer_cls:
        shutil.rmtree(project_dir, ignore_errors=True)
        return jsonify({"error": f"不支持的平台: {platform}"}), 400

    try:
        analyzer = analyzer_cls(actual_root)
        analysis = analyzer.analyze()
    except Exception as e:
        shutil.rmtree(project_dir, ignore_errors=True)
        return jsonify({"error": f"分析失败: {str(e)}"}), 500

    # 生成文档
    output_dir = os.path.join(project_dir, "docs")
    os.makedirs(output_dir, exist_ok=True)

    # Markdown
    md_path = os.path.join(output_dir, f"{platform}_docs.md")
    md_gen = MarkdownGenerator()
    md_gen.generate(analysis, md_path)

    # HTML
    html_path = os.path.join(output_dir, f"{platform}_docs.html")
    html_gen = HTMLGenerator()
    html_gen.generate(analysis, html_path)

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Clean up
    shutil.rmtree(project_dir, ignore_errors=True)

    return jsonify({
        "success": True,
        "platform": platform,
        "analysis": analysis,
        "markdown": md_content,
        "html_doc": html_content,
    })


@app.route("/api/demo", methods=["GET"])
def api_demo():
    """用内置example生成演示文档"""
    examples = {
        "chrome": os.path.join(os.path.dirname(__file__), "examples"),
        "android": os.path.join(os.path.dirname(__file__), "examples", "android-access"),
    }

    # Try android example
    android_path = examples["android"]
    if os.path.exists(android_path):
        analyzer = AndroidAccessibilityAnalyzer(android_path)
        analysis = analyzer.analyze()

        output_dir = os.path.join(UPLOAD_DIR, "demo_docs")
        os.makedirs(output_dir, exist_ok=True)

        md_path = os.path.join(output_dir, "android_docs.md")
        html_path = os.path.join(output_dir, "android_docs.html")

        MarkdownGenerator().generate(analysis, md_path)
        HTMLGenerator().generate(analysis, html_path)

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        return jsonify({
            "success": True,
            "platform": "android",
            "analysis": analysis,
            "markdown": md_content,
            "html_doc": html_content,
        })

    return jsonify({"error": "无可用示例"}), 404


@app.route("/api/download/<fmt>", methods=["POST"])
def api_download(fmt):
    """下载生成的文档"""
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "无内容"}), 400

    content = data["content"]
    platform = data.get("platform", "project")

    if fmt == "md":
        filename = f"{platform}_docs.md"
        mimetype = "text/markdown"
    elif fmt == "html":
        filename = f"{platform}_docs.html"
        mimetype = "text/html"
    else:
        return jsonify({"error": "不支持的格式"}), 400

    tmp = os.path.join(UPLOAD_DIR, filename)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)

    return send_file(tmp, as_attachment=True, download_name=filename, mimetype=mimetype)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
