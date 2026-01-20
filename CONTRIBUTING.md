# CONTRIBUTING.md

感谢你对 Game2Notion 项目的兴趣！我们欢迎各种形式的贡献。

## 提交 Issue

在提交 Issue 前，请：
- 确保 Issue 尚未存在
- 清晰描述问题
- 提供复现步骤（如适用）
- 附加日志和环境信息

## 提交 Pull Request

### 准备工作

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 使用 [Black](https://github.com/psf/black) 进行代码格式化
- 使用 [Flake8](https://flake8.pycqa.org/) 进行代码检查
- 使用 [mypy](http://mypy-lang.org/) 进行类型检查
- 编写单元测试覆盖新功能
- 更新相关文档

### 运行检查

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 格式化代码
black src/

# 运行 linting
flake8 src/

# 运行类型检查
mypy src/ --ignore-missing-imports

# 运行测试
pytest tests/
```

## 开发流程

1. 从 main 分支创建新分支
2. 进行更改
3. 测试你的更改
4. 提交 Pull Request

## 提交消息规范

- 使用现在时态 ("Add feature" not "Added feature")
- 使用命令式语气 ("Move cursor to..." not "Moves cursor to...")
- 限制第一行在 50 个字符以内
- 详细描述写在空行后

示例：
```
Add support for game achievements sync

- Fetch achievements from Steam API
- Store achievements in Notion database
- Add achievement unlock date tracking
```

## 许可证

通过提交代码，你同意你的贡献在 MIT 许可证下发布。

感谢！🙏
