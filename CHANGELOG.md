# 更新日志

所有本项目的显著变化都将在此文件中记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [未发布]

### 计划中
- [ ] Docker 容器支持
- [ ] GitHub Actions 自动化部署
- [ ] 数据库迁移工具
- [ ] Web UI 界面

## [1.0.0] - 2026-01-20

### 新增
- 初始版本发布
- Steam 游戏库完整同步功能
- 游戏元数据获取（类型、开发商、发行商等）
- Steam 成就数据同步
- 每日游玩记录同步
- 命令行工具支持
- 增量和全量同步支持

### 技术
- 项目结构优化（GitHub 标准结构）
- 添加 `platforms` 模块管理多平台支持
- CI/CD GitHub Actions 工作流配置
- 完整的 Python 包配置 (setup.py, pyproject.toml)
