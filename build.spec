# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件：SELEX 测序处理工具 Linux 单文件打包
构建命令：pyinstaller build.spec
输出：dist/selex_pipeline（单个可执行文件）
"""

import os

# pandaseq 可执行文件和 libpandaseq 路径
PANDASEQ_BIN = "pandaseq/bin/pandaseq"
PANDASEQ_LIB = "pandaseq/lib/libpandaseq.so.7"

# 需要随二进制一起打包的外部文件：(源路径, 目标目录名)
binaries = []
if os.path.isfile(PANDASEQ_BIN):
    binaries.append((PANDASEQ_BIN, "."))
if os.path.isfile(PANDASEQ_LIB):
    binaries.append((PANDASEQ_LIB, "."))

a = Analysis(
    ["src/main.py"],
    pathex=["src"],          # 让 PyInstaller 在 src/ 里找模块
    binaries=binaries,
    datas=[],
    hiddenimports=[
        "collections",
        "gzip",
        "csv",
        "logging",
        "subprocess",
        "multiprocessing",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="selex_pipeline",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # 不用 UPX 压缩，避免部分系统误报
    console=True,          # 终端程序
    onefile=True,
)
