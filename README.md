
# Game2Notion

## 使用方法

### 同步所有游戏（默认）
```bash
python notion_game_list.py
# 或显式指定
python notion_game_list.py sync
```

### 添加或更新单个游戏
通过 AppID 添加游戏到 Notion，如果 Notion 中已存在该游戏则强制更新：
```bash
python notion_game_list.py add 387290
```

### 添加或更新多个游戏
使用逗号分隔多个 AppID（无空格或有空格都支持）：
```bash
# 无空格
python notion_game_list.py add 5501,24534,387290

# 有空格
python notion_game_list.py add 5501, 24534, 387290
```

### 调试模式
添加 `--debug` 参数启用详细日志：
```bash
python notion_game_list.py --debug
python notion_game_list.py add 387290 --debug
python notion_game_list.py add 5501,24534 --debug
```

## TODO

- [ ] 需要实现判断商品名为空，或者游玩总时间不一致的时候更新
- [ ] 将工程部署成能docker和github的容器实现