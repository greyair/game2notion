# Game2Notion

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

同步 Steam 游戏信息到 Notion 数据库的工具

## 快速开始

### 安装

```bash
git clone https://github.com/yourusername/game2notion.git
cd game2notion

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，填入：
# STEAM_API_KEY=your_key
# STEAM_USER_ID=your_id
# NOTION_API_KEY=your_key
# NOTION_GAMES_DATABASE_ID=your_id
# NOTION_DAILY_RECORDS_DB_ID=your_id
```

### 使用

```bash
# 同步所有游戏
python -m src.notion_game_list

# 添加单个游戏 (by AppID)
python -m src.notion_game_list add 730

# 添加多个游戏
python -m src.notion_game_list add 730,570

# 同步每日游玩记录
python -m src.daily_game_records

# 调试模式
python -m src.notion_game_list --debug
```

### Makefile 快捷命令

```bash
make install    # 安装依赖
make dev        # 安装开发工具
make run        # 运行游戏同步
make run-daily  # 运行每日记录同步
make test       # 运行测试
make lint       # 代码检查
make format     # 代码格式化
make check      # 完整检查
```

## 项目结构

```
src/
├── config.py              # 配置文件
├── utils.py               # 工具函数
├── notion_game_list.py    # 游戏库同步
├── daily_game_records.py  # 每日记录同步
└── platforms/
    └── steam.py           # Steam API 接口

tests/                      # 单元测试
.github/workflows/ci.yml    # GitHub Actions CI/CD
```

## 功能

- 🎮 从 Steam 获取游戏库
- 📊 游戏元数据同步
- 🏆 游戏成就信息
- 📅 每日游玩记录
- 🔄 增量/全量更新

## API Keys

- **Steam**: https://steamcommunity.com/dev/apikey
- **Notion**: https://www.notion.so/my-integrations
- **Steam ID**: https://steamid.io/

## 贡献

欢迎提交 Issue 和 Pull Request！请见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT - 详见 [LICENSE](LICENSE)
