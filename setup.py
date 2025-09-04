"""LLM指令遵循與結構化輸出標準庫安裝配置"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# 讀取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "docs" / "LLM_INSTRUCTION_STANDARD.md").read_text(encoding='utf-8')

# 讀取requirements文件
def read_requirements(filename):
    """讀取requirements文件"""
    requirements = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    requirements.append(line)
    return requirements

# 核心依賴
install_requires = [
    "jsonschema>=4.17.0",
    "requests>=2.28.0",
    "typing-extensions>=4.4.0",
    "openai>=1.0.0",
    "anthropic>=0.8.0",
    "google-generativeai>=0.3.0",
    "pydantic>=2.0.0",
    "dataclasses-json>=0.6.0",
    "aiohttp>=3.8.0",
    "aiofiles>=23.0.0",
    "cachetools>=5.3.0",
    "structlog>=23.0.0",
    "tenacity>=8.2.0",
    "backoff>=2.2.0",
    "python-dotenv>=1.0.0",
    "PyYAML>=6.0",
    "cryptography>=40.0.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "python-dateutil>=2.8.0",
    "httpx>=0.24.0",
    "orjson>=3.8.0",
    "validators>=0.20.0",
    "psutil>=5.9.0",
    "packaging>=23.0"
]

# 可選依賴
extras_require = {
    'redis': ['redis>=4.5.0'],
    'monitoring': ['prometheus-client>=0.16.0'],
    'dev': [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'pytest-cov>=4.0.0',
        'pytest-mock>=3.10.0',
        'responses>=0.23.0',
        'black>=23.0.0',
        'isort>=5.12.0',
        'flake8>=6.0.0',
        'mypy>=1.0.0',
        'pre-commit>=3.0.0'
    ],
    'docs': [
        'sphinx>=6.0.0',
        'sphinx-rtd-theme>=1.2.0',
        'mkdocs>=1.4.0',
        'mkdocs-material>=9.0.0'
    ],
    'profiling': [
        'memory-profiler>=0.60.0',
        'line-profiler>=4.0.0',
        'py-spy>=0.3.0'
    ],
    'data': [
        'numpy>=1.24.0',
        'pandas>=2.0.0',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0'
    ],
    'all': [
        'redis>=4.5.0',
        'prometheus-client>=0.16.0',
        'numpy>=1.24.0',
        'pandas>=2.0.0',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0'
    ]
}

setup(
    name="llm-instruction-standard",
    version="1.0.0",
    author="JobSpy Team",
    author_email="team@jobspy.com",
    description="統一的LLM指令遵循與結構化輸出標準庫",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jobspy/llm-instruction-standard",
    project_urls={
        "Bug Tracker": "https://github.com/jobspy/llm-instruction-standard/issues",
        "Documentation": "https://llm-instruction-standard.readthedocs.io/",
        "Source Code": "https://github.com/jobspy/llm-instruction-standard",
    },
    packages=find_packages(include=['llm_standard', 'llm_standard.*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "llm-standard=llm_standard.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "llm_standard": [
            "schemas/*.json",
            "templates/*.json",
            "config/*.yaml",
            "config/*.json"
        ],
    },
    zip_safe=False,
    keywords=[
        "llm", "ai", "machine-learning", "natural-language-processing",
        "openai", "anthropic", "google", "deepseek",
        "instruction-following", "structured-output", "json-schema",
        "api-client", "standardization", "interoperability"
    ],
    license="MIT",
    platforms=["any"],
    test_suite="tests",
    tests_require=[
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "responses>=0.23.0"
    ],
)