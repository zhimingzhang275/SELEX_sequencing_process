"""汇总多轮 CSV 输出 all_rounds_summary.csv"""
import os
import csv
from typing import List, Dict
from collections import defaultdict
from logger import get_logger

logger = get_logger()


def merge_all_rounds(csv_paths: List[tuple], output_path: str) -> None:
    """
    csv_paths: [(round_name, csv_path), ...]
    将各轮 CSV 合并为宽格式 summary，序列取并集，缺失填 0。
    不使用 pandas，避免内存峰值，手动实现 outer join。
    """
    if not csv_paths:
        logger.warning("没有有效的轮次 CSV，跳过汇总。")
        return

    # round_name -> {sequence -> (count, frequency)}
    round_data: Dict[str, Dict[str, tuple]] = {}
    all_sequences = set()

    for round_name, csv_path in csv_paths:
        if not csv_path or not os.path.isfile(csv_path):
            logger.warning(f"[{round_name}] CSV 文件不存在，汇总时跳过。")
            continue
        seqs = {}
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                seq = row["sequence"]
                seqs[seq] = (int(row["count"]), row["frequency"])
                all_sequences.add(seq)
        round_data[round_name] = seqs
        logger.info(f"[{round_name}] 读取 {len(seqs):,} 条序列用于汇总")

    if not round_data:
        logger.error("所有轮次 CSV 均无效，无法生成汇总。")
        return

    round_names = [r for r, _ in csv_paths if r in round_data]

    # 构建表头
    header = ["sequence"]
    for rn in round_names:
        header += [f"{rn}_count", f"{rn}_freq"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for seq in sorted(all_sequences):
            row = [seq]
            for rn in round_names:
                if seq in round_data.get(rn, {}):
                    cnt, freq = round_data[rn][seq]
                    row += [cnt, freq]
                else:
                    row += [0, "0.000000"]
            writer.writerow(row)

    logger.info(f"汇总 CSV 已输出：{output_path}，共 {len(all_sequences):,} 条唯一序列")
