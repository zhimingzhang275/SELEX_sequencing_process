"""
运行时路径解析。
区分两种运行模式：
  1. 直接用 python src/main.py 运行（开发模式）
  2. PyInstaller --onefile 打包后运行（生产模式）

打包模式下：
  - sys._MEIPASS：临时解压目录，存放 pandaseq 二进制和 libpandaseq
  - BASE_DIR：可执行文件所在目录，data/ results/ logs/ 均相对于此
"""
import os
import sys


def is_bundled() -> bool:
    """是否以 PyInstaller bundle 方式运行"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_base_dir() -> str:
    """项目根目录（data/ results/ logs/ 的父目录）"""
    if is_bundled():
        # 可执行文件所在目录
        return os.path.dirname(sys.executable)
    # 开发模式：src/ 的上一级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_meipass_dir() -> str:
    """PyInstaller 临时解压目录（存放 pandaseq 二进制）"""
    if is_bundled():
        return sys._MEIPASS
    # 开发模式：不使用此路径
    return ""


def get_pandaseq_bin() -> str:
    """返回 pandaseq 可执行文件路径"""
    if is_bundled():
        return os.path.join(sys._MEIPASS, "pandaseq")
    base = get_base_dir()
    return os.path.join(base, "pandaseq", "bin", "pandaseq")


def get_pandaseq_lib_dir() -> str:
    """返回 libpandaseq 所在目录（打包模式下在 _MEIPASS，开发模式下在 pandaseq/lib）"""
    if is_bundled():
        return sys._MEIPASS
    return os.path.join(get_base_dir(), "pandaseq", "lib")
