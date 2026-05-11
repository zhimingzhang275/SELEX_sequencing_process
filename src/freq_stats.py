"""频率统计，输出每轮 CSV"""
import os
import csv
from collections import Counter
from typing import List, Tuple
from logger import get_logger

logger = get_logger()


def compute_and_save(
    counter: Counter,
    total_matched: int,
    round_name: str,
    results_dir: str,
    top_n: int = 100,
) -> str:
    """
    计算 frequency，按降序排列，输出 results/Rn.csv。
    同时输出 top{top_n}.fasta 文件。
    返回输出 CSV 路径。
    """
    os.makedirs(results_dir, exist_ok=True)

    if total_matched == 0:
        logger.warning(f"[{round_name}] 没有匹配到任何序列，跳过输出。")
        return ""

    # 排序：按 count 降序
    sorted_items: List[Tuple[str, int]] = counter.most_common()

    csv_path = os.path.join(results_dir, f"{round_name}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sequence", "count", "frequency"])
        for seq, count in sorted_items:
            freq = count / total_matched
            writer.writerow([seq, count, f"{freq:.6f}"])

    logger.info(f"[{round_name}] CSV 已输出：{csv_path}，共 {len(sorted_items):,} 个唯一序列")

    # 输出 top N fasta
    fasta_path = os.path.join(results_dir, f"{round_name}_top{top_n}.fasta")
    with open(fasta_path, "w", encoding="utf-8") as f:
        for rank, (seq, count) in enumerate(sorted_items[:top_n], 1):
            freq = count / total_matched
            f.write(f">rank{rank}_count{count}_freq{freq:.6f}\n{seq}\n")

    logger.info(f"[{round_name}] Top{top_n} FASTA 已输出：{fasta_path}")
    return csv_path
