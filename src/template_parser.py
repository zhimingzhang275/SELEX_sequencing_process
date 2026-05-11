"""将用户输入的文库模板转换为正则表达式，并提取随机区捕获组"""
import re
import sys
from typing import Tuple
from logger import get_logger

logger = get_logger()

LEGAL_CHARS = set("ATCGNUatcgnu")


def parse_template(template: str) -> Tuple[re.Pattern, int]:
    """
    接收用户输入模板（如 CGACTNNNNNCGATCG），返回：
      - 编译后的正则（随机区为捕获组）
      - 捕获组数量（= 随机区段数）

    规则：
      - 去空格，转大写，U→T
      - 非法字符直接终止
      - 连续 N 转为捕获组 ([ATCG]{n})
      - 固定碱基直接匹配
    """
    raw = template.strip()

    if not raw:
        logger.error("模板不能为空。")
        sys.exit(1)

    # 标准化
    raw = raw.upper().replace("U", "T").replace(" ", "")

    # 检查非法字符
    illegal = set(raw) - set("ATCGN")
    if illegal:
        chars = "、".join(sorted(illegal))
        logger.error(f"模板存在非法字符：{chars}\n仅允许 A/T/C/G/N（或 U，自动转为 T）")
        sys.exit(1)

    if "N" not in raw:
        logger.error("模板中没有 N（随机区），无法提取随机序列。请在随机区位置使用 N。")
        sys.exit(1)

    # 将模板拆分为 (is_random, segment) 列表
    segments = _split_segments(raw)

    # 构建正则字符串
    pattern_parts = []
    group_count = 0
    for is_random, seg in segments:
        if is_random:
            n = len(seg)
            pattern_parts.append(f"([ATCG]{{{n}}})")
            group_count += 1
        else:
            pattern_parts.append(re.escape(seg))

    pattern_str = "".join(pattern_parts)
    compiled = re.compile(pattern_str, re.IGNORECASE)

    logger.info(f"模板解析成功：{raw}")
    logger.info(f"生成正则：{pattern_str}（共 {group_count} 个随机区）")

    return compiled, group_count


def _split_segments(template: str):
    """将模板拆分为 [(is_random, str), ...] 列表"""
    segments = []
    i = 0
    while i < len(template):
        if template[i] == "N":
            j = i
            while j < len(template) and template[j] == "N":
                j += 1
            segments.append((True, template[i:j]))
            i = j
        else:
            j = i
            while j < len(template) and template[j] != "N":
                j += 1
            segments.append((False, template[i:j]))
            i = j
    return segments


def extract_random_region(match: re.Match, group_count: int) -> str:
    """从第一个随机区起点到最后一个随机区终点整段提取，保留中间固定碱基，去掉两端固定区"""
    return match.string[match.start(1):match.end(group_count)]
