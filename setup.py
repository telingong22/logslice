"""Setup configuration for logslice."""
from setuptools import find_packages, setup

setup(
    name="logslice",
    version="0.1.0",
    description="CLI tool to filter and slice structured log files by time range and field patterns.",
    author="logslice contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    entry_points={
        "console_scripts": [
            "logslice=logslice.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: System :: Logging",
    ],
)
