import os
import tomllib


def read(file_path) -> dict:
    """读取 toml 文件"""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "rb") as f:
        return tomllib.load(f)
