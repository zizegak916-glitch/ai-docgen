import json
import os
import logging
from typing import Any

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class ChromeExtensionAnalyzer(BaseAnalyzer):
    """Chrome扩展分析器"""

    def get_platform(self) -> str:
        return "chrome"

    def analyze(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "platform": "chrome",
            "manifest": {},
            "background": {},
            "content_scripts": [],
            "popup": {},
            "options_page": {},
            "icons": [],
            "permissions": [],
            "permissions_file": [],
        }

        manifest = self._parse_manifest()
        result["manifest"] = manifest
        result["permissions"] = manifest.get("permissions", [])

        if "background" in manifest:
            bg = manifest["background"]
            if "service_worker" in bg:
                sw_path = bg["service_worker"]
                result["background"] = {
                    "type": "service_worker",
                    "path": sw_path,
                    "content": self._read_file(sw_path),
                }
            elif "scripts" in bg:
                result["background"] = {
                    "type": "scripts",
                    "paths": bg["scripts"],
                    "contents": [self._read_file(s) for s in bg["scripts"]],
                }

        if "content_scripts" in manifest:
            for cs in manifest["content_scripts"]:
                info = {
                    "matches": cs.get("matches", []),
                    "js": cs.get("js", []),
                    "css": cs.get("css", []),
                }
                info["js_contents"] = [self._read_file(f) for f in info["js"]]
                result["content_scripts"].append(info)

        popup_path = manifest.get("action", {}).get("default_popup", "popup.html")
        popup_content = self._read_file(popup_path)
        if popup_content:
            result["popup"] = {
                "html": popup_content,
                "js": self._read_file(popup_path.replace(".html", ".js")),
                "css": self._read_file(popup_path.replace(".html", ".css")),
            }

        options_path = manifest.get("options_page", "")
        if options_path:
            result["options_page"] = {
                "html": self._read_file(options_path),
                "js": self._read_file(options_path.replace(".html", ".js")),
            }

        icon_files = self._scan_files("icons/**/*")
        result["icons"] = [os.path.relpath(i, self.project_path) for i in icon_files]

        result["permissions_file"] = self._extract_permission_descriptions()

        logger.info("Chrome扩展分析完成: %s", manifest.get("name", "unknown"))
        return result

    def _parse_manifest(self) -> dict[str, Any]:
        content = self._read_file("manifest.json")
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("manifest.json 解析失败: %s", e)
            return {}

    def _extract_permission_descriptions(self) -> list[dict[str, str]]:
        permissions_map = {
            "activeTab": "访问当前活动标签页",
            "tabs": "访问浏览器标签页信息",
            "storage": "使用本地存储",
            "notifications": "显示通知",
            "cookies": "访问浏览器Cookie",
            "history": "访问浏览历史",
            "bookmarks": "访问书签",
            "downloads": "管理下载",
            "webRequest": "拦截和修改网络请求",
            "scripting": "注入脚本到页面",
            "clipboardRead": "读取剪贴板",
            "clipboardWrite": "写入剪贴板",
            "management": "管理其他扩展",
            "contextMenus": "创建右键菜单",
            "geolocation": "获取地理位置",
        }
        manifest = self._parse_manifest()
        perms = manifest.get("permissions", [])
        return [{"permission": p, "description": permissions_map.get(p, "自定义权限")} for p in perms]
