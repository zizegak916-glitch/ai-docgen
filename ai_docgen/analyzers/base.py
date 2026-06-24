import os
import glob
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """分析器基类"""

    def __init__(self, project_path: str) -> None:
        self.project_path = os.path.abspath(project_path)
        if not os.path.isdir(self.project_path):
            raise ValueError(f"项目路径不存在: {self.project_path}")

    @abstractmethod
    def analyze(self) -> dict[str, Any]:
        """分析项目并返回结果"""
        ...

    @abstractmethod
    def get_platform(self) -> str:
        """返回平台名称"""
        ...

    def _read_file(self, path: str) -> str:
        """读取文件内容"""
        full_path = os.path.join(self.project_path, path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("文件未找到: %s", full_path)
            return ""
        except Exception as e:
            logger.error("读取文件失败 %s: %s", full_path, e)
            return ""

    def _scan_files(self, pattern: str) -> list[str]:
        """扫描匹配模式的文件"""
        search_pattern = os.path.join(self.project_path, pattern)
        return glob.glob(search_pattern, recursive=True)
