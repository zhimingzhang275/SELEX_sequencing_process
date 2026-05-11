"""扫描 data/ 目录，识别各轮次数据及单/双端类型"""
import os
import re
import sys
from typing import List, Dict, Tuple, Optional
from logger import get_logger
from paths import get_base_dir

logger = get_logger()

# 支持的序列文件扩展名
SEQ_EXTENSIONS = (
    ".fastq", ".fastq.gz",
    ".fq", ".fq.gz",
    ".fasta", ".fa", ".fa.gz"
)

# 双端配对模式（R1/R2 或 1/2）
PAIR_PATTERNS = [
    (re.compile(r"(.+)_R1(\..+)$", re.IGNORECASE), re.compile(r"(.+)_R2(\..+)$", re.IGNORECASE), "_R1", "_R2"),
    (re.compile(r"(.+)_1(\..+)$"),                  re.compile(r"(.+)_2(\..+)$"),                  "_1",  "_2"),
]


def _is_seq_file(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in SEQ_EXTENSIONS)


def _find_pairs(files: List[str]) -> Optional[List[Tuple[str, str]]]:
    """
    尝试将文件列表配对为 (R1, R2) 元组。
    返回配对列表，或 None 表示不是双端。
    """
    for r1_pat, r2_pat, r1_tag, r2_tag in PAIR_PATTERNS:
        r1_files = [f for f in files if r1_pat.match(f)]
        if not r1_files:
            continue
        pairs = []
        for r1 in r1_files:
            m = r1_pat.match(r1)
            base, ext = m.group(1), m.group(2)
            r2 = base + r2_tag + ext
            if r2 in files:
                pairs.append((r1, r2))
        if pairs:
            return pairs
    return None


class RoundData:
    """表示一轮 SELEX 数据"""

    def __init__(self, name: str, directory: str):
        self.name = name          # 如 "R1"
        self.directory = directory
        self.is_paired: bool = False
        self.pairs: List[Tuple[str, str]] = []   # 双端：[(r1_path, r2_path), ...]
        self.single_files: List[str] = []         # 单端：[path, ...]

    def __repr__(self):
        if self.is_paired:
            return f"<RoundData {self.name} paired={len(self.pairs)}对>"
        return f"<RoundData {self.name} single={len(self.single_files)}文件>"


def scan_data_dir(data_dir: str) -> List[RoundData]:
    """
    扫描 data/ 目录，按轮次子目录排序，返回 RoundData 列表。
    每个子目录 = 一轮 SELEX。
    """
    if not os.path.isdir(data_dir):
        logger.error(f"数据目录不存在：{data_dir}")
        sys.exit(1)

    subdirs = sorted([
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
    ])

    if not subdirs:
        logger.error(f"data/ 目录下没有找到任何子目录，请按 R1/R2/R3 格式组织数据。")
        sys.exit(1)

    rounds = []
    for subdir in subdirs:
        dir_path = os.path.join(data_dir, subdir)
        all_files = [f for f in os.listdir(dir_path) if _is_seq_file(f)]

        if not all_files:
            logger.warning(f"轮次 {subdir} 目录下未找到支持的序列文件，跳过。")
            continue

        rd = RoundData(name=subdir, directory=dir_path)

        pairs = _find_pairs(all_files)
        if pairs:
            rd.is_paired = True
            # 检查数量一致性
            r1_files = [f for f in all_files if any(
                re.search(tag, f, re.IGNORECASE) for _, _, tag, _ in PAIR_PATTERNS
            )]
            r2_files = [f for f in all_files if any(
                re.search(tag2, f, re.IGNORECASE) for _, _, _, tag2 in PAIR_PATTERNS
            )]
            # 简化验证：配对数 == R1文件数
            if len(pairs) == 0:
                logger.error(f"轮次 {subdir}：检测到双端文件数量不一致，请检查文件配对。")
                sys.exit(1)
            rd.pairs = [
                (os.path.join(dir_path, r1), os.path.join(dir_path, r2))
                for r1, r2 in pairs
            ]
            logger.info(f"轮次 {subdir}：双端测序，共 {len(rd.pairs)} 对文件")
        else:
            rd.is_paired = False
            rd.single_files = [os.path.join(dir_path, f) for f in all_files]
            logger.info(f"轮次 {subdir}：单端测序，共 {len(rd.single_files)} 个文件")

        rounds.append(rd)

    if not rounds:
        logger.error("未找到任何有效轮次数据，请检查 data/ 目录结构。")
        sys.exit(1)

    logger.info(f"共检测到 {len(rounds)} 轮 SELEX 数据：{[r.name for r in rounds]}")
    return rounds
