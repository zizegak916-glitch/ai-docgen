import os
import re
import logging
from typing import Any
from xml.etree import ElementTree

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class IOSAppAnalyzer(BaseAnalyzer):
    """iOS应用分析器"""

    def get_platform(self) -> str:
        return "ios"

    def analyze(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "platform": "ios",
            "info_plist": {},
            "accessibility_features": [],
            "localizations": [],
            "dependencies": [],
            "source_files": [],
            "accessibility_apis": [],
        }

        result["info_plist"] = self._parse_info_plist()
        result["accessibility_features"] = self._extract_accessibility_features()
        result["localizations"] = self._parse_localizations()
        result["dependencies"] = self._parse_dependencies()
        result["source_files"] = self._scan_accessibility_sources()
        result["accessibility_apis"] = self._extract_accessibility_apis()

        logger.info("iOS应用分析完成")
        return result

    def _parse_info_plist(self) -> dict[str, Any]:
        content = self._read_file("Info.plist")
        if not content:
            return {}
        try:
            tree = ElementTree.fromstring(content)
            return self._plist_to_dict(tree)
        except ElementTree.ParseError as e:
            logger.error("Info.plist 解析失败: %s", e)
            return {}

    def _plist_to_dict(self, element: ElementTree.Element) -> Any:
        if element.tag == "dict":
            d: dict[str, Any] = {}
            children = list(element)
            i = 0
            while i < len(children):
                key = children[i].text or ""
                i += 1
                if i < len(children):
                    d[key] = self._parse_plist_value(children[i])
                    i += 1
            return d
        return self._parse_plist_value(element)

    def _parse_plist_value(self, element: ElementTree.Element) -> Any:
        tag = element.tag
        if tag == "string":
            return element.text or ""
        elif tag == "integer":
            return int(element.text or "0")
        elif tag == "true":
            return True
        elif tag == "false":
            return False
        elif tag == "array":
            return [self._parse_plist_value(child) for child in element]
        elif tag == "dict":
            return self._plist_to_dict(element)
        return element.text

    def _extract_accessibility_features(self) -> list[dict[str, str]]:
        features = []
        feature_keywords = [
            ("UIAccessibility", "UIAccessibility API"),
            ("isAccessibilityElement", "无障碍元素标记"),
            ("accessibilityLabel", "无障碍标签"),
            ("accessibilityHint", "无障碍提示"),
            ("accessibilityValue", "无障碍值"),
            ("accessibilityTraits", "无障碍特征"),
            ("accessibilityFrame", "无障碍框架"),
            ("accessibilityActivationPoint", "无障碍激活点"),
            ("shouldGroupAccessibilityChildren", "无障碍子元素分组"),
            ("accessibilityViewIsModal", "模态无障碍视图"),
            ("post(notification:", "无障碍通知"),
            ("UIAccessibilityPostNotification", "无障碍通知发送"),
        ]

        for path in self._scan_accessibility_sources():
            content = path.get("content", "")
            for keyword, desc in feature_keywords:
                if keyword in content:
                    features.append({
                        "feature": keyword,
                        "description": desc,
                        "file": path["path"],
                    })

        seen = set()
        unique = []
        for f in features:
            key = f["feature"]
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _parse_localizations(self) -> list[dict[str, str]]:
        localizations = []
        for path in self._scan_files("**/InfoPlist.strings"):
            rel = os.path.relpath(path, self.project_path)
            content = self._read_file(rel)
            lang = rel.split("/")[-2] if "/" in rel else "default"
            localizations.append({"language": lang, "path": rel, "content": content})
        return localizations

    def _parse_dependencies(self) -> list[dict[str, str]]:
        deps = []

        podfile = self._read_file("Podfile")
        if podfile:
            for match in re.finditer(r"pod\s+['\"](.+?)['\"]", podfile):
                deps.append({"type": "cocoapods", "dependency": match.group(1), "file": "Podfile"})

        package_swift = self._read_file("Package.swift")
        if package_swift:
            for match in re.finditer(r'\.package\s*\(\s*url:\s*"(.+?)"', package_swift):
                deps.append({"type": "spm", "dependency": match.group(1), "file": "Package.swift"})

        return deps

    def _scan_accessibility_sources(self) -> list[dict[str, str]]:
        sources = []
        for ext in ("swift", "m", "mm"):
            for path in self._scan_files(f"**/*.{ext}"):
                rel = os.path.relpath(path, self.project_path)
                content = self._read_file(rel)
                if any(kw in content for kw in ("UIAccessibility", "accessibilityLabel", "isAccessibilityElement")):
                    sources.append({
                        "path": rel,
                        "language": "swift" if ext == "swift" else "objective-c",
                        "content": content,
                    })
        return sources

    def _extract_accessibility_apis(self) -> list[str]:
        api_patterns = [
            r"UIAccessibility\.\w+",
            r"\.accessibility\w+",
            r"UIAccessibilityPostNotification",
        ]
        found = set()
        for source in self._scan_accessibility_sources():
            content = source.get("content", "")
            for pattern in api_patterns:
                for match in re.finditer(pattern, content):
                    found.add(match.group(0))
        return sorted(found)
