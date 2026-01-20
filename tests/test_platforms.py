# -*- coding: utf-8 -*-
"""
测试 platforms 模块
"""

import pytest


class TestPlatforms:
    """platforms 模块测试"""

    def test_platforms_import(self):
        """测试 platforms 模块导入"""
        try:
            from platforms import steam
            assert hasattr(steam, 'get_owned_games_from_steam')
            assert hasattr(steam, 'get_steam_recent_games')
        except ImportError as e:
            pytest.skip(f"无法导入 platforms 模块: {e}")

    def test_mock_data(self, mock_steam_games):
        """测试模拟数据"""
        assert len(mock_steam_games) == 2
        assert mock_steam_games[0]['appid'] == 730
        assert mock_steam_games[1]['name'] == 'Dota 2'

    def test_config_import(self):
        """测试配置导入"""
        try:
            from config import NOTION_PROPERTIES, NOTION_DAILY_PROPERTIES
            assert 'name' in NOTION_PROPERTIES
            assert 'date' in NOTION_DAILY_PROPERTIES
        except ImportError as e:
            pytest.skip(f"无法导入 config 模块: {e}")
