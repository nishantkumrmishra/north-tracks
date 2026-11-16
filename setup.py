from setuptools import setup, find_packages

setup(
    name="northtracks",
    version="1.0.0",
    description="North Tracks - Autonomous 320k Studio Audio Downloader & Organizer",
    author="North Tracks Team",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "mutagen>=1.47.0",
        "pycryptodome>=3.20.0",
        "rich>=13.7.0",
        "prompt_toolkit>=3.0.43"
    ],
    entry_points={
        "console_scripts": [
            "northtracks = musicdl.cli:main",
        ],
    },
    python_requires=">=3.9",
)
