# AI DocGen - 智能文档生成器

AI DocGen 是一款智能文档生成工具，支持 Chrome 扩展、Android 无障碍服务和 iOS 应用的代码分析与文档自动生成。结合 AI 增强能力，帮助开发者快速产出专业级技术文档。

## 功能特性

### 支持平台
- **Chrome 扩展** — 分析 manifest.json、content scripts、background/service worker 等
- **Android 无障碍服务** — 分析 AndroidManifest.xml、AccessibilityService、布局文件等
- **iOS 应用** — 分析 Info.plist、UIAccessibility API 使用、依赖管理等

### 文档格式
- **Markdown** — 轻量级文档，适合版本控制
- **HTML** — 带样式的可视化文档，适合在线浏览

### AI 增强
- 文档内容优化与补全
- 代码示例自动生成
- 多语言翻译支持（DeepSeek / OpenAI）

## 安装

```bash
pip install -e .
```

### 依赖

```
requests
beautifulsoup4
lxml
```

## 使用示例

### 分析项目

```bash
# 自动检测平台
ai-docgen analyze /path/to/project

# 指定平台
ai-docgen analyze /path/to/project --platform chrome
```

### 生成文档

```bash
# 生成 Markdown 文档
ai-docgen generate /path/to/project --format md --output docs

# 生成 HTML 文档
ai-docgen generate /path/to/project --format html --output docs
```

### AI 增强文档

```bash
ai-docgen enhance docs/chrome_docs.md --llm deepseek
```

## 支持的平台说明

| 平台 | 检测文件 | 分析内容 |
|------|----------|----------|
| Chrome 扩展 | `manifest.json` | 权限、content scripts、background、popup |
| Android | `AndroidManifest.xml` | 无障碍服务配置、事件类型、权限 |
| iOS | `Info.plist` | 权限、无障碍API、依赖管理 |

## 技术架构

```
ai_docgen/
├── __init__.py              # 包入口
├── analyzers/               # 平台分析器
│   ├── base.py              # 分析器基类
│   ├── chrome_ext.py        # Chrome 扩展分析
│   ├── android_access.py    # Android 无障碍分析
│   └── ios_app.py           # iOS 应用分析
├── generators/              # 文档生成器
│   ├── markdown.py          # Markdown 生成
│   └── html.py              # HTML 生成
├── llm.py                   # LLM 增强模块
└── cli.py                   # 命令行工具
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## License

MIT License
