"""流式读取 FASTQ/FASTA 文件（支持 gzip），yield 序列字符串"""
import os
from typing import Generator
from utils import open_file, is_fasta, is_fastq
from logger import get_logger

logger = get_logger()


def parse_sequences(filepath: str) -> Generator[str, None, None]:
    """
    自动识别文件格式（FASTQ/FASTA）和压缩，流式 yield 每条序列字符串。
    不将整个文件读入内存，适合超大文件。
    """
    if is_fastq(filepath):
        yield from _parse_fastq(filepath)
    elif is_fasta(filepath):
        yield from _parse_fasta(filepath)
    else:
        logger.error(f"无法识别的文件格式：{filepath}")
        return


def _parse_fastq(filepath: str) -> Generator[str, None, None]:
    """每4行为一条记录：@header / seq / + / quality"""
    with open_file(filepath) as f:
        while True:
            header = f.readline()
            if not header:
                break
            seq = f.readline().strip()
            f.readline()   # +
            f.readline()   # quality
            if seq:
                yield seq


def _parse_fasta(filepath: str) -> Generator[str, None, None]:
    """流式读取 FASTA，支持多行序列"""
    with open_file(filepath) as f:
        current_seq_parts = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_seq_parts:
                    yield "".join(current_seq_parts)
                current_seq_parts = []
            else:
                current_seq_parts.append(line)
        if current_seq_parts:
            yield "".join(current_seq_parts)


def fastq_to_fasta(input_path: str, output_path: str) -> int:
    """
    将 FASTQ 文件转换为 FASTA 文件，返回转换的序列数。
    流式处理，支持超大文件和 gzip 输入。
    """
    count = 0
    with open_file(input_path) as fin, open(output_path, "w", encoding="utf-8") as fout:
        while True:
            header = fin.readline()
            if not header:
                break
            seq = fin.readline().strip()
            fin.readline()   # +
            fin.readline()   # quality
            if seq:
                read_id = header.strip().lstrip("@")
                fout.write(f">{read_id}\n{seq}\n")
                count += 1
    logger.info(f"FASTQ→FASTA 转换完成：{os.path.basename(input_path)}，共 {count} 条序列")
    return count
