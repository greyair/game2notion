# 🚀 Game2Notion - 快速部署指南

## 🎯 5分钟快速开始

### 步骤 1: 准备环境 (1 分钟)

```bash
# 克隆项目
git clone https://github.com/yourusername/game2notion.git
cd game2notion

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate           # macOS/Linux
# 或
venv\Scripts\activate              # Windows PowerShell
```

### 步骤 2: 安装依赖 (1 分钟)

```bash
# 使用 Makefile（推荐）
make install
make dev

# 或手动安装
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 步骤 3: 配置 API Keys (2 分钟)

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入：
# STEAM_API_KEY=xxx
# STEAM_USER_ID=xxx
# NOTION_API_KEY=xxx
# NOTION_GAMES_DATABASE_ID=xxx
# NOTION_DAILY_RECORDS_DB_ID=xxx
```

### 步骤 4: 运行程序 (1 分钟)

```bash
# 同步所有游戏
make run

# 或调试模式
make run-debug

# 或同步每日记录
make run-daily
```

---

## 📋 详细安装指南

### 系统要求
- Python 3.8+
- pip 或 conda
- 网络连接

### 获取所需的 Keys

#### 1️⃣ Steam API Key 和 User ID

访问 https://steamcommunity.com/dev/apikey 获取 API Key

访问 https://steamid.io/ 查询 User ID

#### 2️⃣ Notion API Key

1. 访问 https://www.notion.so/my-integrations
2. 点击 "Create new integration"
3. 填写名称和描述
4. 选择 "Read content", "Update content", "Create content"
5. 复制 "Internal Integration Token"

#### 3️⃣ Notion Database IDs

1. 在 Notion 中打开你的数据库
2. 从 URL 中复制 ID：`https://notion.so/xxxxx?v=xxxxx`
3. ID 是 `xxxxx` 部分（32 个字符）

### 完整安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/game2notion.git
cd game2notion

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate          # macOS/Linux
# 或
.\venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. 更新 pip
pip install --upgrade pip

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装开发依赖（可选但推荐）
pip install -e ".[dev]"

# 6. 配置环境
cp .env.example .env
# 编辑 .env 文件

# 7. 测试安装
python -m src.notion_game_list --debug
```

---

## 🎮 使用示例

### 同步所有游戏

```bash
python -m src.notion_game_list
# 或使用 Makefile
make run
```

### 添加单个游戏

```bash
python -m src.notion_game_list add 730
# 730 是 Counter-Strike 2 的 App ID
```

### 添加多个游戏

```bash
python -m src.notion_game_list add 730,570,10
# 或带空格
python -m src.notion_game_list add 730, 570, 10
```

### 调试模式

```bash
python -m src.notion_game_list --debug
```

### 同步每日记录

```bash
python -m src.daily_game_records
```

---

## 🛠️ Makefile 命令参考

```bash
make install      # 安装项目依赖
make dev         # 安装开发依赖
make test        # 运行单元测试
make lint        # 代码检查 (flake8 + mypy)
make format      # 代码格式化 (black)
make clean       # 清理临时文件
make check       # 运行所有检查
make run         # 运行游戏列表同步
make run-daily   # 运行每日记录同步
make run-debug   # 调试模式运行
```

---

## 🐛 常见问题解决

### 问题 1: Python 版本不对

```bash
# 检查 Python 版本
python --version

# 需要 Python 3.8+
# 如果版本过低，下载最新版本
# https://www.python.org/downloads/
```

### 问题 2: 模块导入错误

```bash
# 确保你在虚拟环境中
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 问题 3: API Key 无效

```bash
# 检查 .env 文件
cat .env

# 重新获取 API Key：
# Steam: https://steamcommunity.com/dev/apikey
# Notion: https://www.notion.so/my-integrations
```

### 问题 4: 请求超时

```bash
# 网络问题，尝试：
# 1. 检查网络连接
# 2. 使用代理
# 3. 重新尝试
```

---

## 📊 项目目录说明

```
game2notion/
├── src/                    # 源代码
│   ├── config.py          # 配置文件
│   ├── utils.py           # 工具函数
│   ├── notion_game_list.py # 主程序
│   ├── daily_game_records.py # 每日记录
│   └── platforms/         # 游戏平台模块
│       └── steam.py       # Steam API
├── tests/                 # 测试代码
├── docs/                  # 文档
├── .env.example           # 环境变量示例
├── requirements.txt       # Python 依赖
├── setup.py              # 包配置
└── Makefile              # 快捷命令
```

---

## 🔗 有用的链接

| 资源 | 链接 |
|------|------|
| Steam Web API | https://developer.valvesoftware.com/wiki/Steam_Web_API |
| Notion API 文档 | https://developers.notion.com/ |
| Python 文档 | https://docs.python.org/3/ |
| requests 库 | https://docs.python-requests.org/ |

---

## 💬 需要帮助？

1. 查看 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) 开发指南
2. 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 贡献指南
3. 提交 Issue: https://github.com/yourusername/game2notion/issues
4. 查看项目 Wiki: https://github.com/yourusername/game2notion/wiki

---

**祝你使用愉快！** 🎉

有任何问题，欢迎提出 Issue 或 Pull Request！
