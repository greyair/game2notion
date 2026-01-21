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
python -m src.notion_game_list sync

# 添加单个游戏 (by AppID)
python -m src.notion_game_list add 730

# 添加多个游戏
python -m src.notion_game_list add 730,570

# 同步游戏库 + 每日记录
python -m src.notion_game_list sync --daily

# 调试模式
python -m src.notion_game_list --debug
```

## GitHub Actions 自动化部署

项目已配置 GitHub Actions 工作流（`.github/workflows/deploy.yml`），支持自动定时同步。

### 定时任务（北京时间）

- **23:55** - 运行 `notion_game_list sync --daily`

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
- 北京时间 23:55 → UTC 15:55 (`cron: '55 15 * * *'`)

## 项目结构

```
src/
├── config.py              # 配置文件
├── utils.py               # 工具函数
├── notion_game_list.py    # 游戏库同步
└── platforms/
    └── steam.py           # Steam API 接口
.github/workflows/          # GitHub Actions 工作流
```

## 功能

- 🎮 从 Steam 获取游戏库
- 📊 游戏元数据同步
- 🏆 游戏成就信息
- 📅 每日游玩记录
- 🔄 增量/全量更新
- ⏰ 定时自动化同步

## Notion 数据库创建指南

### 1) 游戏库数据库（NOTION_GAMES_DATABASE_ID）

在 Notion 新建一个数据库（表格视图），并添加以下属性（名称可自定义，但需在 config.py 中映射）：

- 游戏名称（Title）
- 游戏商品名（Rich text）
- 游戏时长（Number，单位：分钟）
- 游戏类型（Multi-select）
- 开发商（Multi-select）
- 发行商（Multi-select）
- 发行日期（Date）
- 上次游玩时间（Date，包含时间）
- 商店链接（URL）
- 成就总数（Number）
- 获得成就（Number）
- 成就首次解锁（Date）
- 游戏简介（Rich text）
- 游戏标签（Multi-select）
- 游戏平台（Select）
- 商店价格（Rich text）
- 玩家评分（Select）
- appid（Rich text）

### 2) 每日记录数据库（NOTION_DAILY_RECORDS_DB_ID）

新建第二个数据库（表格视图），并添加以下属性：

- 日期（Date）
- 标题（Title）
- 游戏名称（Relation，关联到游戏库数据库）
- 游玩时间（Number，单位：分钟）
- 总游玩时间（Number，单位：分钟）

### 3) 配置数据库 ID

打开数据库页面链接，复制链接中的数据库 ID，填入 `.env` 或 GitHub Secrets：

- NOTION_GAMES_DATABASE_ID
- NOTION_DAILY_RECORDS_DB_ID

## API Keys

- **Steam**: https://steamcommunity.com/dev/apikey
- **Notion**: https://www.notion.so/my-integrations
- **Steam ID**: https://steamid.io/

## 贡献

欢迎提交 Issue 和 Pull Request！请见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT - 详见 [LICENSE](LICENSE)
