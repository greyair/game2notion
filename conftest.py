# -*- coding: utf-8 -*-
"""
pytest 配置文件
"""

import pytest
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_steam_games():
    """模拟 Steam 游戏数据"""
    return [
        {
            "appid": 730,
            "name": "Counter-Strike 2",
            "playtime_forever": 3600,
            "rtime_last_played": 1705765200,
        },
        {
            "appid": 570,
            "name": "Dota 2",
            "playtime_forever": 7200,
            "rtime_last_played": 1705765200,
        },
    ]


@pytest.fixture
def mock_config():
    """模拟配置"""
    return {
        "STEAM_API_KEY": "test_key",
        "STEAM_USER_ID": "test_user_id",
        "NOTION_API_KEY": "test_notion_key",
    }
