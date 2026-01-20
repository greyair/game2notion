# Game2Notion - 快速开发指南

## 本地开发设置

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API Keys：

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 4. 运行项目

```bash
# 同步所有游戏
python -m src.notion_game_list

# 同步每日记录
python -m src.daily_game_records

# 调试模式
python -m src.notion_game_list --debug
```

## 项目模块说明

### src/config.py
- Steam 和 Notion API 配置
- 数据库属性映射表
- 常量定义

### src/utils.py
- 网络请求工具函数
- 数据解析辅助函数
- 通用工具函数

### src/platforms/steam.py
- Steam API 接口
- 游戏信息获取
- 成就数据获取

### src/notion_game_list.py
- 主程序入口
- 游戏库同步逻辑
- 单个/多个游戏更新

### src/daily_game_records.py
- 每日记录同步
- 游玩时间统计
- 记录到 Notion

## 常见开发任务

### 添加新的数据源

1. 在 `src/platforms/` 下创建新文件（如 `epic.py`）
2. 实现数据获取接口
3. 在 `src/platforms/__init__.py` 中导出接口
4. 在主程序中集成

### 修改数据库属性

编辑 `src/config.py` 中的 `NOTION_PROPERTIES` 字典

### 调试 API 请求

启用调试模式：

```bash
python -m src.notion_game_list --debug
```

查看详细日志输出

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_steam.py

# 生成覆盖率报告
pytest --cov=src tests/
```

## 代码质量检查

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/ --ignore-missing-imports
```

## 提交前清单

- [ ] 代码已格式化 (`black src/`)
- [ ] 通过 linting 检查 (`flake8 src/`)
- [ ] 通过类型检查 (`mypy src/`)
- [ ] 新功能已添加测试
- [ ] README 已更新（如适用）
- [ ] CHANGELOG.md 已更新

## 有用的资源

- [Steam Web API](https://developer.valvesoftware.com/wiki/Steam_Web_API)
- [Notion API](https://developers.notion.com/)
- [Python requests 库](https://docs.python-requests.org/)
