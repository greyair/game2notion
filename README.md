# Game2Notion

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

同步 Steam 游戏信息到 Notion 数据库的工具

## 快速开始

### 本地运行

#### 安装

```bash
git clone https://github.com/yourusername/game2notion.git
cd game2notion

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 配置

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

#### 运行

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

## GitHub Actions 自动化部署

项目已配置 GitHub Actions 工作流（`.github/workflows/deploy.yml`），支持自动定时同步。

### 定时任务（北京时间）

- **00:00** - 运行 `daily_game_records`
- **12:00** - 运行 `daily_game_records`
- **14:00** - 运行 `notion_game_list`

### 部署步骤

1. **提交到 GitHub**
   ```bash
   git add .
   git commit -m "chore: setup github actions automation"
   git push origin main
   ```

2. **配置 Secrets**
   
   打开 GitHub 项目 → Settings → Secrets and variables → Actions，添加：
   
   - `STEAM_API_KEY` - https://steamcommunity.com/dev/apikey
   - `STEAM_USER_ID` - https://steamid.io/
   - `NOTION_API_KEY` - https://www.notion.so/my-integrations
   - `NOTION_GAMES_DATABASE_ID`
   - `NOTION_DAILY_RECORDS_DB_ID`

3. **启用工作流**
   
   打开 Actions 标签页，确认工作流已启用。可点击 "Run workflow" 手动测试。

### 修改运行时间

编辑 `.github/workflows/deploy.yml` 中的 `cron` 表达式（UTC 时区）：

**时区转换（北京时间 → UTC）：**
- 北京时间 08:00 → UTC 00:00 (`cron: '0 0 * * *'`)
- 北京时间 12:00 → UTC 04:00 (`cron: '0 4 * * *'`)
- 北京时间 14:00 → UTC 06:00 (`cron: '0 6 * * *'`)
- 北京时间 20:00 → UTC 12:00 (`cron: '0 12 * * *'`)
- 北京时间 23:59 → UTC 15:59 (`cron: '59 15 * * *'`)

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
.github/workflows/          # GitHub Actions 工作流
```

## 功能

- 🎮 从 Steam 获取游戏库
- 📊 游戏元数据同步
- 🏆 游戏成就信息
- 📅 每日游玩记录
- 🔄 增量/全量更新
- ⏰ 定时自动化同步

## API Keys

- **Steam**: https://steamcommunity.com/dev/apikey
- **Notion**: https://www.notion.so/my-integrations
- **Steam ID**: https://steamid.io/

## 贡献

欢迎提交 Issue 和 Pull Request！请见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT - 详见 [LICENSE](LICENSE)
