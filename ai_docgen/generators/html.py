import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 2rem; }}
        h1 {{ font-size: 2rem; color: #1a1a2e; margin-bottom: 1rem; border-bottom: 3px solid #e94560; padding-bottom: 0.5rem; }}
        h2 {{ font-size: 1.5rem; color: #16213e; margin: 2rem 0 1rem; }}
        h3 {{ font-size: 1.2rem; color: #0f3460; margin: 1.5rem 0 0.75rem; }}
        p {{ margin: 0.5rem 0; }}
        ul, ol {{ margin: 0.5rem 0 0.5rem 2rem; }}
        li {{ margin: 0.25rem 0; }}
        code {{ background: #e8e8e8; padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.9em; }}
        pre {{ background: #1a1a2e; color: #e8e8e8; padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 1rem 0; }}
        pre code {{ background: transparent; padding: 0; color: inherit; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #16213e; color: white; }}
        tr:hover {{ background: #f0f0f0; }}
        .section {{ background: white; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }}
        .badge-chrome {{ background: #4285f4; color: white; }}
        .badge-android {{ background: #3ddc84; color: #1a1a2e; }}
        .badge-ios {{ background: #007aff; color: white; }}
    </style>
</head>
<body>
<div class="container">
    {content}
</div>
</body>
</html>"""


class HTMLGenerator:
    """HTML文档生成器"""

    def generate(self, analysis: dict[str, Any], output_path: str) -> str:
        platform = analysis.get("platform", "unknown")
        title = f"{platform.title()} 项目文档"

        sections = [
            self._gen_overview(analysis),
            self._gen_setup(analysis),
            self._gen_api_reference(analysis),
            self._gen_permissions(analysis),
            self._gen_accessibility(analysis),
            self._gen_platform_guide(analysis),
        ]
        content = "\n".join(sections)
        html = HTML_TEMPLATE.format(title=title, content=content)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info("HTML文档已生成: %s", output_path)
        return output_path

    def _gen_overview(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        badge_cls = f"badge-{platform}"
        lines = [f'<h1>{platform.title()} 项目文档 <span class="badge {badge_cls}">{platform.upper()}</span></h1>']
        lines.append('<div class="section"><h2>项目概览</h2>')

        if platform == "chrome":
            manifest = analysis.get("manifest", {})
            lines.append(f"<p><strong>名称:</strong> {manifest.get('name', 'N/A')}</p>")
            lines.append(f"<p><strong>版本:</strong> {manifest.get('version', 'N/A')}</p>")
            lines.append(f"<p><strong>描述:</strong> {manifest.get('description', 'N/A')}</p>")
        elif platform == "android":
            manifest = analysis.get("manifest", {})
            lines.append(f"<p><strong>包名:</strong> {manifest.get('package', 'N/A')}</p>")
        elif platform == "ios":
            info = analysis.get("info_plist", {})
            lines.append(f"<p><strong>Bundle ID:</strong> {info.get('CFBundleIdentifier', 'N/A')}</p>")

        lines.append("</div>")
        return "\n".join(lines)

    def _gen_setup(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ['<div class="section"><h2>安装指南</h2><ol>']

        if platform == "chrome":
            lines.extend([
                "<li>打开 Chrome 浏览器，访问 <code>chrome://extensions/</code></li>",
                "<li>开启「开发者模式」</li>",
                "<li>点击「加载已解压的扩展程序」</li>",
                "<li>选择项目目录</li>",
            ])
        elif platform == "android":
            lines.extend([
                "<li>使用 Android Studio 打开项目</li>",
                "<li>同步 Gradle 依赖</li>",
                "<li>连接设备或启动模拟器</li>",
                "<li>在设置 > 无障碍 中启用服务</li>",
            ])
        elif platform == "ios":
            lines.extend([
                "<li>使用 Xcode 打开项目</li>",
                "<li>安装依赖 (<code>pod install</code> 或 SPM)</li>",
                "<li>连接设备</li>",
                "<li>在设置 > 辅助功能 中启用</li>",
            ])

        lines.append("</ol></div>")
        return "\n".join(lines)

    def _gen_api_reference(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ['<div class="section"><h2>API 参考</h2>']

        if platform == "chrome":
            for i, script in enumerate(analysis.get("content_scripts", []), 1):
                lines.append(f"<h3>Content Script {i}</h3><ul>")
                lines.append(f"<li>匹配: <code>{', '.join(script.get('matches', []))}</code></li>")
                for js in script.get("js", []):
                    lines.append(f"<li>JS: <code>{js}</code></li>")
                lines.append("</ul>")
        elif platform == "android":
            service = analysis.get("accessibility_service", {})
            if service.get("service_class"):
                lines.append(f"<h3>无障碍服务</h3><p><code>{service['service_class']}</code></p>")
        elif platform == "ios":
            apis = analysis.get("accessibility_apis", [])
            if apis:
                lines.append("<h3>无障碍API</h3><ul>")
                for api in apis:
                    lines.append(f"<li><code>{api}</code></li>")
                lines.append("</ul>")

        lines.append("</div>")
        return "\n".join(lines)

    def _gen_permissions(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ['<div class="section"><h2>权限说明</h2>']

        if platform == "chrome":
            perms = analysis.get("permissions_file", [])
            if perms:
                lines.append("<table><tr><th>权限</th><th>说明</th></tr>")
                for p in perms:
                    lines.append(f"<tr><td><code>{p['permission']}</code></td><td>{p['description']}</td></tr>")
                lines.append("</table>")
        elif platform == "android":
            perms = analysis.get("manifest", {}).get("permissions", [])
            if perms:
                lines.append("<table><tr><th>权限</th></tr>")
                for p in perms:
                    lines.append(f"<tr><td><code>{p}</code></td></tr>")
                lines.append("</table>")

        lines.append("</div>")
        return "\n".join(lines)

    def _gen_accessibility(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ['<div class="section"><h2>无障碍特性</h2>']

        if platform == "android":
            service = analysis.get("accessibility_service", {})
            if service.get("service_class"):
                lines.append(f"<p><strong>服务类:</strong> <code>{service['service_class']}</code></p>")
                events = analysis.get("accessibility_events", [])
                if events:
                    lines.append("<ul>")
                    for e in events:
                        lines.append(f"<li><code>{e}</code></li>")
                    lines.append("</ul>")
        elif platform == "ios":
            features = analysis.get("accessibility_features", [])
            if features:
                lines.append("<ul>")
                for f in features:
                    lines.append(f"<li><strong>{f['description']}</strong> (<code>{f['feature']}</code>) - {f['file']}</li>")
                lines.append("</ul>")

        lines.append("</div>")
        return "\n".join(lines)

    def _gen_platform_guide(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = [f'<div class="section"><h2>{platform.title()} 平台指南</h2>']

        if platform == "chrome":
            tips = ["遵循 Chrome 扩展最佳实践", "最小化权限请求", "使用 Content Security Policy", "支持 Manifest V3"]
        elif platform == "android":
            tips = ["正确实现 AccessibilityService 生命周期", "及时响应 accessibilityEvent", "提供有意义的无障碍描述", "测试 TalkBack 兼容性"]
        else:
            tips = ["设置 accessibilityLabel 和 accessibilityHint", "正确使用 accessibilityTraits", "支持 VoiceOver 手势", "使用 UIAccessibilityPostNotification"]

        lines.append("<ul>")
        for tip in tips:
            lines.append(f"<li>{tip}</li>")
        lines.append("</ul></div>")
        return "\n".join(lines)
