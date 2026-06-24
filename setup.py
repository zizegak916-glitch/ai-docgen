from setuptools import setup, find_packages

setup(
    name="ai-docgen",
    version="0.1.0",
    description="AI DocGen - 智能文档生成器",
    author="AI DocGen Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "requests",
        "beautifulsoup4",
        "lxml",
    ],
    entry_points={
        "console_scripts": [
            "ai-docgen=ai_docgen.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Documentation",
    ],
)
