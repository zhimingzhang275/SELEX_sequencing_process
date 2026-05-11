"""公用工具函数"""
import os
import gzip
import io


def get_cpu_count() -> int:
    """返回可用CPU数，最少1"""
    return max(1, os.cpu_count() or 1)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def open_file(path: str, mode: str = "rt", encoding: str = "utf-8"):
    """自动识别 gzip 压缩，返回文本文件句柄"""
    if path.endswith(".gz"):
        return gzip.open(path, mode, encoding=encoding)
    return open(path, mode, encoding=encoding)


def is_fasta(path: str) -> bool:
    """通过扩展名判断文件是 FASTA 还是 FASTQ"""
    name = path.lower()
    # 去掉 .gz 后缀再判断
    if name.endswith(".gz"):
        name = name[:-3]
    return name.endswith((".fasta", ".fa"))


def is_fastq(path: str) -> bool:
    name = path.lower()
    if name.endswith(".gz"):
        name = name[:-3]
    return name.endswith((".fastq", ".fq"))
