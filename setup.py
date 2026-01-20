# -*- coding: utf-8 -*-
"""
setup.py - Game2Notion 项目配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="game2notion",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Sync Steam game information to Notion database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/game2notion",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
    ],
    entry_points={
        "console_scripts": [
            "game2notion=game2notion.notion_game_list:main",
        ],
    },
)
