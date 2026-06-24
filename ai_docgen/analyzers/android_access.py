import os
import re
import logging
from typing import Any
from xml.etree import ElementTree

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class AndroidAccessibilityAnalyzer(BaseAnalyzer):
    """Android无障碍服务分析器"""

    def get_platform(self) -> str:
        return "android"

    def analyze(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "platform": "android",
            "manifest": {},
            "accessibility_service": {},
            "layouts": [],
            "resources": [],
            "dependencies": [],
            "source_files": [],
            "accessibility_events": [],
        }

        manifest_info = self._parse_manifest()
        result["manifest"] = manifest_info

        service_info = self._extract_service_config(manifest_info)
        result["accessibility_service"] = service_info

        result["layouts"] = self._parse_layouts()
        result["resources"] = self._parse_resources()
        result["dependencies"] = self._parse_gradle()
        result["source_files"] = self._scan_source_files()
        result["accessibility_events"] = self._extract_accessibility_events()

        logger.info("Android无障碍服务分析完成")
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
            }

            for perm in tree.findall("uses-permission"):
                name = perm.get(f"{ANDROID_NS}name", "")
                if name:
                    info["permissions"].append(name)

            for service in tree.findall(".//service"):
                svc_info = {
                    "name": service.get(f"{ANDROID_NS}name", ""),
                    "permission": service.get(f"{ANDROID_NS}permission", ""),
                    "meta_data": [],
                }
                for meta in service.findall("meta-data"):
                    svc_info["meta_data"].append({
                        "name": meta.get(f"{ANDROID_NS}name", ""),
                        "value": meta.get(f"{ANDROID_NS}value", ""),
                    })
                info["services"].append(svc_info)

            return info
        except ElementTree.ParseError as e:
            logger.error("AndroidManifest.xml 解析失败: %s", e)
            return {}

    def _extract_service_config(self, manifest_info: dict) -> dict[str, Any]:
        config: dict[str, Any] = {
            "service_class": "",
            "accessibility_event_types": [],
            "accessibility_feedback_type": "",
            "can_access_window_content": False,
            "notification_timeout": 0,
            "settings_activity": "",
            "description": "",
        }

        for service in manifest_info.get("services", []):
            if "accessibility" in service["name"].lower() or "Accessibility" in service["name"]:
                config["service_class"] = service["name"]
                for meta in service["meta_data"]:
                    value = meta["value"]
                    if "eventTypes" in meta["name"]:
                        config["accessibility_event_types"] = value.split("|")
                    elif "feedbackType" in meta["name"]:
                        config["accessibility_feedback_type"] = value
                    elif "canRetrieveWindowContent" in meta["name"]:
                        config["can_access_window_content"] = value.lower() == "true"
                    elif "notificationTimeout" in meta["name"]:
                        config["notification_timeout"] = int(value) if value.isdigit() else 0
                    elif "settingsActivity" in meta["name"]:
                        config["settings_activity"] = value

        desc_path = self._find_file("accessibility_service_config.xml")
        if desc_path:
            config["description"] = self._read_file(desc_path)

        return config

    def _parse_layouts(self) -> list[dict[str, str]]:
        layouts = []
        for path in self._scan_files("**/res/layout/**/*.xml"):
            rel = os.path.relpath(path, self.project_path)
            content = self._read_file(rel)
            name = os.path.splitext(os.path.basename(path))[0]
            layouts.append({"name": name, "path": rel, "content": content})
        return layouts

    def _parse_resources(self) -> list[dict[str, str]]:
        resources = []
        for path in self._scan_files("**/res/values/**/*.xml"):
            rel = os.path.relpath(path, self.project_path)
            content = self._read_file(rel)
            name = os.path.splitext(os.path.basename(path))[0]
            resources.append({"name": name, "path": rel, "content": content})
        return resources

    def _parse_gradle(self) -> list[dict[str, str]]:
        deps = []
        for gradle_name in ("build.gradle", "build.gradle.kts"):
            content = self._read_file(gradle_name)
            if not content:
                continue
            for match in re.finditer(r"implementation\s+['\"](.+?)['\"]", content):
                deps.append({"dependency": match.group(1), "file": gradle_name})
            break
        return deps

    def _scan_source_files(self) -> list[dict[str, str]]:
        sources = []
        for ext in ("java", "kt"):
            for path in self._scan_files(f"**/*.{ext}"):
                rel = os.path.relpath(path, self.project_path)
                content = self._read_file(rel)
                if "AccessibilityService" in content or "AccessibilityEvent" in content:
                    sources.append({
                        "path": rel,
                        "language": "kotlin" if ext == "kt" else "java",
                        "content": content,
                    })
        return sources

    def _extract_accessibility_events(self) -> list[str]:
        event_types = [
            "TYPE_VIEW_CLICKED", "TYPE_VIEW_LONG_CLICKED", "TYPE_VIEW_FOCUSED",
            "TYPE_VIEW_TEXT_CHANGED", "TYPE_WINDOW_STATE_CHANGED",
            "TYPE_WINDOW_CONTENT_CHANGED", "TYPE_VIEW_SCROLLED",
            "TYPE_ANNOUNCEMENT", "TYPE_TOUCH_EXPLORATION_GESTURE_START",
            "TYPE_VIEW_ACCESSIBILITY_FOCUSED",
        ]
        found = set()
        for source in self._scan_source_files():
            content = source.get("content", "")
            for event in event_types:
                if event in content:
                    found.add(event)
        return sorted(found)

    def _find_file(self, filename: str) -> str | None:
        for path in self._scan_files(f"**/{filename}"):
            return os.path.relpath(path, self.project_path)
        return None
