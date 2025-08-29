"""
Setup script for Academic Paper Research Assistant
論文リサーチ支援システム セットアップ
"""

from setuptools import setup, find_packages

setup(
    name="academic-paper-research-assistant",
    version="1.0.0",
    description="論文リサーチ支援システム - ハルシネーションなしの学術論文検索",
    author="AI-Driven Research System",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "aiohttp>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "paper-search=main:search_papers",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Researchers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
