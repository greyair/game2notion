# Game2Notion

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**同步 Steam 游戏信息到 Notion 数据库的工具**

将你的 Steam 游戏库、游玩记录和成就数据自动同步到 Notion，创建一个个性化的游戏管理系统。

## 功能特性

- 🎮 从 Steam 获取完整游戏库信息
- 📊 支持游戏元数据：类型、开发商、发行商、发行日期等
- 🏆 自动获取游戏成就信息
- 📅 同步每日游玩记录
- 🔄 增量更新和全量同步支持
- 🛠️ 命令行工具，操作简便

## 安装

### 需求

- Python 3.8 或更高版本
- Steam API Key
- Notion API Key

### 快速开始

1. **克隆仓库**

```bash
git clone https://github.com/yourusername/game2notion.git
cd game2notion
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

或者用 pip 安装包：

```bash
pip install -e .
```

3. **配置环境变量**

创建 `.env` 文件在项目根目录：

```env
STEAM_API_KEY=your_steam_api_key
STEAM_USER_ID=your_steam_user_id
NOTION_API_KEY=your_notion_api_key
NOTION_GAMES_DATABASE_ID=your_database_id
NOTION_DAILY_RECORDS_DB_ID=your_daily_records_db_id
```

## 使用方法

### 同步所有游戏（默认）

```bash
python -m src.notion_game_list
# 或显式指定
python -m src.notion_game_list sync
```

### 添加或更新单个游戏

通过 AppID 添加游戏到 Notion，如果已存在则强制更新：

```bash
python -m src.notion_game_list add 387290
```

### 添加或更新多个游戏

使用逗号分隔多个 AppID：

```bash
# 无空格
python -m src.notion_game_list add 5501,24534,387290

# 有空格
python -m src.notion_game_list add 5501, 24534, 387290
```

### 调试模式

添加 `--debug` 参数启用详细日志：

```bash
python -m src.notion_game_list --debug
python -m src.notion_game_list add 387290 --debug
```

### 同步每日游玩记录

```bash
python -m src.daily_game_records
```

## 项目结构

```
game2notion/
├── src/
│   ├── __init__.py
│   ├── config.py                    # 配置文件和常量
│   ├── utils.py                     # 工具函数
│   ├── notion_game_list.py          # 游戏库同步脚本
│   ├── daily_game_records.py        # 每日记录同步脚本
│   └── platforms/
│       ├── __init__.py
│       └── steam.py                 # Steam API 接口
├── tests/                           # 测试文件
├── docs/                            # 文档
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI/CD
├── setup.py                         # 安装配置
├── pyproject.toml                   # 项目元数据
├── requirements.txt                 # Python 依赖
├── README.md                        # 项目文档
└── .gitignore
```

## 配置说明

### config.py

主要配置项：

- `STEAM_API_KEY` - Steam API Key
- `STEAM_USER_ID` - Steam 用户 ID
- `NOTION_API_KEY` - Notion API Key
- `NOTION_GAMES_DATABASE_ID` - Notion 游戏库数据库 ID
- `NOTION_DAILY_RECORDS_DB_ID` - Notion 每日记录数据库 ID

详见 [src/config.py](src/config.py) 中的 `NOTION_PROPERTIES` 和 `NOTION_DAILY_PROPERTIES`。

## 开发

### 设置开发环境

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行代码格式检查
black src/

# 运行 linting
flake8 src/

# 运行类型检查
mypy src/

# 运行测试
pytest tests/
```

## 常见问题

**Q: 如何获取 Steam API Key？**

A: 访问 https://steamcommunity.com/dev/apikey 获取。

**Q: 如何获取 Steam User ID？**

A: 访问 https://steamid.io/ 查询你的 Steam ID。

**Q: 如何获取 Notion API Key？**

A: 访问 https://www.notion.so/my-integrations 创建集成并获取 API Key。

## 更新日志

### v1.0.0 (2026-01-20)

- ✨ 初始版本发布
- 🎮 支持 Steam 游戏库同步
- 📊 支持游戏元数据和成就
- 📅 支持每日游玩记录同步

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 相关链接

- [Steam API 文档](https://developer.valvesoftware.com/wiki/Steam_Web_API)
- [Notion API 文档](https://developers.notion.com/)
- [Notion Python SDK](https://github.com/ramnes/notion-sdk-py)
