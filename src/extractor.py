"""从序列中提取随机区，统计频次"""
import re
from collections import Counter
from typing import Generator, Tuple
from template_parser import extract_random_region
from logger import get_logger

logger = get_logger()

# 每处理多少条序列打印一次进度
PROGRESS_INTERVAL = 500_000


def extract_and_count(
    sequences: Generator[str, None, None],
    pattern: re.Pattern,
    group_count: int,
    round_name: str = "",
) -> Tuple[Counter, int, int]:
    """
    流式遍历序列生成器，匹配模板，提取随机区，统计频次。

    返回：
      - counter: Counter，key=随机区序列，value=出现次数
      - total_reads: 总序列数
      - matched_reads: 匹配成功数
    """
    counter: Counter = Counter()
    total = 0
    matched = 0

    for seq in sequences:
        total += 1
        m = pattern.search(seq)
        if m:
            random_region = extract_random_region(m, group_count)
            counter[random_region] += 1
            matched += 1

        if total % PROGRESS_INTERVAL == 0:
            rate = matched / total * 100 if total else 0
            logger.info(
                f"[{round_name}] 已处理 {total:,} 条序列，"
                f"匹配 {matched:,} 条（{rate:.1f}%）"
            )

    return counter, total, matched
