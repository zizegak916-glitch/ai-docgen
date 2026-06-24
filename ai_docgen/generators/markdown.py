import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Markdown文档生成器"""

    def generate(self, analysis: dict[str, Any], output_path: str) -> str:
        sections = [
            self._gen_overview(analysis),
            self._gen_setup(analysis),
            self._gen_api_reference(analysis),
            self._gen_permissions(analysis),
            self._gen_accessibility(analysis),
            self._gen_overlay_docs(analysis),
            self._gen_platform_guide(analysis),
        ]
        content = "\n\n".join(sections)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("文档已生成: %s", output_path)
        return output_path

    def _gen_overview(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = [f"# {platform.title()} 项目文档\n", "## 项目概览\n"]

        if platform == "chrome":
            manifest = analysis.get("manifest", {})
            lines.append(f"- **名称**: {manifest.get('name', 'N/A')}")
            lines.append(f"- **版本**: {manifest.get('version', 'N/A')}")
            lines.append(f"- **描述**: {manifest.get('description', 'N/A')}")
            lines.append(f"- **Manifest V**: {manifest.get('manifest_version', 'N/A')}")
        elif platform == "android":
            manifest = analysis.get("manifest", {})
            lines.append(f"- **包名**: {manifest.get('package', 'N/A')}")
            lines.append(f"- **权限数**: {len(manifest.get('permissions', []))}")
            overlay = analysis.get("overlay_config", {})
            if overlay.get("has_overlay"):
                lines.append(f"- **悬浮窗类型**: {overlay.get('overlay_type', 'N/A')}")
        elif platform == "ios":
            info = analysis.get("info_plist", {})
            lines.append(f"- **Bundle ID**: {info.get('CFBundleIdentifier', 'N/A')}")
            lines.append(f"- **版本**: {info.get('CFBundleShortVersionString', 'N/A')}")

        return "\n".join(lines)

    def _gen_setup(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ["## 安装指南\n"]

        if platform == "chrome":
            lines.append("1. 打开 Chrome 浏览器，访问 `chrome://extensions/`")
            lines.append("2. 开启「开发者模式」")
            lines.append("3. 点击「加载已解压的扩展程序」")
            lines.append("4. 选择项目目录")
        elif platform == "android":
            lines.append("1. 使用 Android Studio 打开项目")
            lines.append("2. 同步 Gradle 依赖")
            lines.append("3. 连接设备或启动模拟器")
            lines.append("4. 在设置 > 无障碍 中启用服务")
            lines.append("5. 授予悬浮窗权限（如需要）")
        elif platform == "ios":
            lines.append("1. 使用 Xcode 打开项目")
            lines.append("2. 安装依赖 (`pod install` 或 SPM)")
            lines.append("3. 连接设备")
            lines.append("4. 在设置 > 辅助功能 中启用")

        return "\n".join(lines)

    def _gen_api_reference(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ["## API 参考\n"]

        if platform == "chrome":
            scripts = analysis.get("content_scripts", [])
            if scripts:
                lines.append("### Content Scripts\n")
                for i, script in enumerate(scripts, 1):
                    lines.append(f"**脚本 {i}**")
                    lines.append(f"- 匹配模式: `{', '.join(script.get('matches', []))}`")
                    js_files = script.get("js", [])
                    if js_files:
                        lines.append(f"- JS文件: `{', '.join(js_files)}`")
                    lines.append("")
        elif platform == "android":
            service = analysis.get("accessibility_service", {})
            if service.get("has_accessibility_service"):
                lines.append("### 无障碍服务\n")
                lines.append(f"- 配置文件: `{service.get('config_file', 'N/A')}`")
                events = service.get("accessibility_events", [])
                if events:
                    lines.append("- 事件类型:")
                    for e in events:
                        lines.append(f"  - `{e}`")
        elif platform == "ios":
            apis = analysis.get("accessibility_apis", [])
            if apis:
                lines.append("### 使用的无障碍API\n")
                for api in apis:
                    lines.append(f"- `{api}`")

        return "\n".join(lines)

    def _gen_permissions(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ["## 权限说明\n"]

        if platform == "chrome":
            perms = analysis.get("permissions_file", [])
            if perms:
                lines.append("| 权限 | 说明 |")
                lines.append("|------|------|")
                for p in perms:
                    lines.append(f"| `{p['permission']}` | {p['description']} |")
            else:
                lines.append("无特殊权限要求。")
        elif platform == "android":
            perms = analysis.get("manifest", {}).get("permissions", [])
            if perms:
                lines.append("| 权限 | 用途 |")
                lines.append("|------|------|")
                perm_desc = {
                    "SYSTEM_ALERT_WINDOW": "显示悬浮窗",
                    "FOREGROUND_SERVICE": "前台服务",
                    "BIND_ACCESSIBILITY_SERVICE": "绑定无障碍服务",
                    "INTERNET": "网络访问",
                }
                for p in perms:
                    desc = perm_desc.get(p, "系统权限")
                    lines.append(f"| `{p}` | {desc} |")

        return "\n".join(lines)

    def _gen_accessibility(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = ["## 无障碍特性\n"]

        if platform == "chrome":
            perms = analysis.get("permissions", [])
            if "accessibility" in str(perms).lower():
                lines.append("本扩展支持无障碍访问。")
        elif platform == "android":
            service = analysis.get("accessibility_service", {})
            if service.get("has_accessibility_service"):
                lines.append(f"- **配置文件**: `{service.get('config_file', 'N/A')}`")
                events = service.get("accessibility_events", [])
                if events:
                    lines.append("- **监听事件**:")
                    for e in events:
                        lines.append(f"  - `{e}`")
        elif platform == "ios":
            features = analysis.get("accessibility_features", [])
            if features:
                lines.append("### 无障碍功能\n")
                for f in features:
                    lines.append(f"- **{f['description']}** (`{f['feature']}`) - 文件: `{f['file']}`")

        return "\n".join(lines)

    def _gen_overlay_docs(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        if platform != "android":
            return ""

        overlay = analysis.get("overlay_config", {})
        buttons = analysis.get("floating_buttons", [])
        lines = ["## 悬浮窗/浮窗按钮文档\n"]

        if not overlay.get("has_overlay"):
            lines.append("未检测到悬浮窗实现。\n")
            return "\n".join(lines)

        lines.append("### 悬浮窗配置\n")
        lines.append(f"- **悬浮窗类型**: `{overlay.get('overlay_type', 'N/A')}`")
        lines.append(f"- **WindowManager 使用**: {'是' if overlay.get('window_manager_usage') else '否'}")
        lines.append(f"- **悬浮服务**: {'是' if overlay.get('floating_service') else '否'}")

        if overlay.get("overlay_files"):
            lines.append("\n### 相关文件\n")
            for f in overlay["overlay_files"]:
                lines.append(f"- `{f}`")

        if overlay.get("code_snippets"):
            lines.append("\n### 关键代码片段\n")
            for snippet in overlay["code_snippets"][:3]:
                lines.append(f"**{snippet['file']}** ({snippet['keyword']})")
                lines.append("```java")
                lines.append(snippet["snippet"][:300])
                lines.append("```\n")

        if buttons:
            lines.append("### 检测到的按钮/视图\n")
            lines.append("| 类型 | 文件 | 代码 |")
            lines.append("|------|------|------|")
            for btn in buttons[:10]:
                lines.append(f"| {btn['type']} | `{btn['file']}` | `{btn['code'][:50]}...` |")

        lines.append("\n### 悬浮窗实现指南\n")
        lines.append("1. 确保 AndroidManifest.xml 中声明 `SYSTEM_ALERT_WINDOW` 权限")
        lines.append("2. 运行时请求 `Settings.canDrawOverlays()` 权限")
        lines.append("3. 使用 `WindowManager.addView()` 添加悬浮视图")
        lines.append("4. 设置正确的 `WindowManager.LayoutParams` 类型")
        lines.append("5. 处理悬浮窗的拖拽、点击等交互事件")
        lines.append("6. 在无障碍服务中正确管理悬浮窗生命周期")
        lines.append("7. 测试不同屏幕尺寸和 Android 版本的兼容性")

        return "\n".join(lines)

    def _gen_platform_guide(self, analysis: dict[str, Any]) -> str:
        platform = analysis.get("platform", "unknown")
        lines = [f"## {platform.title()} 平台指南\n"]

        if platform == "chrome":
            lines.append("### 开发建议\n")
            lines.append("- 遵循 Chrome 扩展最佳实践")
            lines.append("- 最小化权限请求")
            lines.append("- 使用 Content Security Policy")
            lines.append("- 支持 Manifest V3")
        elif platform == "android":
            lines.append("### 开发建议\n")
            lines.append("- 正确实现 AccessibilityService 生命周期")
            lines.append("- 及时响应 accessibilityEvent")
            lines.append("- 提供有意义的无障碍描述")
            lines.append("- 测试 TalkBack 兼容性")
            overlay = analysis.get("overlay_config", {})
            if overlay.get("has_overlay"):
                lines.append("\n### 悬浮窗最佳实践\n")
                lines.append("- 使用 `TYPE_APPLICATION_OVERLAY`（Android 8.0+）")
                lines.append("- 处理 `canDrawOverlays` 权限请求回调")
                lines.append("- 悬浮窗尺寸适配不同屏幕")
                lines.append("- 支持拖拽移动和双击关闭")
                lines.append("- 避免遮挡系统状态栏和导航栏")
        elif platform == "ios":
            lines.append("### 开发建议\n")
            lines.append("- 设置 accessibilityLabel 和 accessibilityHint")
            lines.append("- 正确使用 accessibilityTraits")
            lines.append("- 支持 VoiceOver 手势")
            lines.append("- 使用 UIAccessibilityPostNotification")

        return "\n".join(lines)
