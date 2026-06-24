import os
import re
import logging
from typing import Any
from xml.etree import ElementTree

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class AndroidAccessibilityAnalyzer(BaseAnalyzer):
    """Android无障碍服务分析器 - 专注悬浮窗/浮窗按钮"""

    OVERLAY_KEYWORDS = [
        "WindowManager",
        "TYPE_APPLICATION_OVERLAY",
        "TYPE_SYSTEM_ALERT",
        "SYSTEM_ALERT_WINDOW",
        "addView",
        "removeView",
        "floating",
        "overlay",
        "bubble",
        "float",
        "popup_window",
        "toast",
    ]

    OVERLAY_PERMISSIONS = [
        "SYSTEM_ALERT_WINDOW",
        "FOREGROUND_SERVICE",
        "BIND_ACCESSIBILITY_SERVICE",
    ]

    def get_platform(self) -> str:
        return "android"

    def analyze(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "platform": "android",
            "manifest": {},
            "accessibility_service": {},
            "overlay_config": {},
            "floating_buttons": [],
            "layouts": [],
            "source_files": [],
            "permissions": [],
        }

        manifest_info = self._parse_manifest()
        result["manifest"] = manifest_info
        result["permissions"] = manifest_info.get("permissions", [])

        service_info = self._extract_service_config(manifest_info)
        result["accessibility_service"] = service_info

        overlay_info = self._analyze_overlay()
        result["overlay_config"] = overlay_info

        floating_buttons = self._extract_floating_buttons()
        result["floating_buttons"] = floating_buttons

        result["layouts"] = self._parse_layouts()
        result["source_files"] = self._scan_source_files()

        logger.info("Android无障碍悬浮窗分析完成")
        return result

    def _parse_manifest(self) -> dict[str, Any]:
        content = self._read_file("AndroidManifest.xml")
        if not content:
            return {}
        try:
            tree = ElementTree.fromstring(content)
            info: dict[str, Any] = {
                "package": tree.get("package", ""),
                "permissions": [],
                "services": [],
                "has_overlay_permission": False,
            }

            for perm in tree.findall("uses-permission"):
                name = perm.get(f"{ANDROID_NS}name", "")
                if name:
                    info["permissions"].append(name)
                    if "SYSTEM_ALERT_WINDOW" in name:
                        info["has_overlay_permission"] = True

            for service in tree.findall(".//service"):
                svc_info = {
                    "name": service.get(f"{ANDROID_NS}name", ""),
                    "permission": service.get(f"{ANDROID_NS}permission", ""),
                    "exported": service.get(f"{ANDROID_NS}exported", "false"),
                }
                meta_data = service.findall("meta-data")
                for md in meta_data:
                    md_name = md.get(f"{ANDROID_NS}name", "")
                    md_value = md.get(f"{ANDROID_NS}value", "")
                    if "accessibility" in md_name.lower():
                        svc_info["accessibility_config"] = md_value
                info["services"].append(svc_info)

            return info
        except ElementTree.ParseError as e:
            logger.error(f"解析 AndroidManifest.xml 失败: {e}")
            return {}

    def _extract_service_config(self, manifest_info: dict) -> dict[str, Any]:
        config = {
            "service_count": len(manifest_info.get("services", [])),
            "has_accessibility_service": False,
            "config_file": "",
            "accessibility_events": [],
        }

        for svc in manifest_info.get("services", []):
            if "accessibility" in svc.get("accessibility_config", "").lower():
                config["has_accessibility_service"] = True
                config["config_file"] = svc.get("accessibility_config", "")

        xml_files = self._scan_files("*.xml")
        for f in xml_files:
            if "accessibility" in f.lower():
                content = self._read_file(f)
                if content:
                    events = re.findall(r'android:accessibilityEventTypes="[^"]*"([^"]*)', content)
                    if events:
                        config["accessibility_events"] = events[0].split("|")
                    config["config_file"] = f
                    break

        return config

    def _analyze_overlay(self) -> dict[str, Any]:
        overlay = {
            "has_overlay": False,
            "overlay_type": "",
            "window_manager_usage": False,
            "floating_service": False,
            "overlay_files": [],
            "code_snippets": [],
        }

        java_files = self._scan_files("*.java") + self._scan_files("*.kt")
        for f in java_files:
            content = self._read_file(f)
            if not content:
                continue

            if "WindowManager" in content:
                overlay["window_manager_usage"] = True
                overlay["has_overlay"] = True

            if "TYPE_APPLICATION_OVERLAY" in content:
                overlay["overlay_type"] = "APPLICATION_OVERLAY"
                overlay["has_overlay"] = True

            if "TYPE_SYSTEM_ALERT" in content:
                overlay["overlay_type"] = "SYSTEM_ALERT"
                overlay["has_overlay"] = True

            if "addView" in content and "WindowManager" in content:
                overlay["floating_service"] = True

            for keyword in self.OVERLAY_KEYWORDS:
                if keyword in content:
                    overlay["overlay_files"].append(f)
                    snippet = self._extract_code_snippet(content, keyword)
                    if snippet:
                        overlay["code_snippets"].append({
                            "file": f,
                            "keyword": keyword,
                            "snippet": snippet,
                        })
                    break

        return overlay

    def _extract_code_snippet(self, content: str, keyword: str, context_lines: int = 5) -> str:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if keyword in line:
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                return "\n".join(lines[start:end])
        return ""

    def _extract_floating_buttons(self) -> list[dict[str, Any]]:
        buttons = []
        java_files = self._scan_files("*.java") + self._scan_files("*.kt")

        for f in java_files:
            content = self._read_file(f)
            if not content:
                continue

            button_patterns = [
                (r'Button\s*\(\s*[^)]*\)', "Button"),
                (r'ImageButton\s*\(\s*[^)]*\)', "ImageButton"),
                (r'FloatingActionButton', "FAB"),
                (r'findViewById\s*\([^)]*\.id\.[^)]*\)', "View"),
            ]

            for pattern, btn_type in button_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    btn_info = {
                        "type": btn_type,
                        "file": f,
                        "code": match[:100],
                    }
                    buttons.append(btn_info)

        return buttons

    def _parse_layouts(self) -> list[dict[str, str]]:
        layouts = []
        layout_files = self._scan_files("*.xml")
        for f in layout_files:
            if "layout" in f.lower():
                content = self._read_file(f)
                if content:
                    layouts.append({"file": f, "content": content[:500]})
        return layouts

    def _scan_source_files(self) -> list[str]:
        java_files = self._scan_files("*.java")
        kt_files = self._scan_files("*.kt")
        return java_files + kt_files
