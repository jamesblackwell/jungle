from setuptools import setup

setup(
    name="jungle",
    version="1.0.0",
    description="A CLI tool for Git worktree management",
    py_modules=["jungle"],
    install_requires=[
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "jungle=jungle:main",
        ],
    },
    python_requires=">=3.6",
)