"""主入口：串联完整 SELEX 测序处理流水线"""
import os
import sys

# 确保 src/ 目录在 Python 路径中（开发模式）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import get_base_dir
from logger import setup_logger, get_logger
from detect import scan_data_dir
from template_parser import parse_template
from fasta_parser import parse_sequences, fastq_to_fasta
from pandaseq_wrapper import merge_paired_reads
from extractor import extract_and_count
from freq_stats import compute_and_save
from merger import merge_all_rounds
from utils import ensure_dir, get_cpu_count

BASE_DIR = get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def print_banner():
    print("=" * 60)
    print("   SELEX 高通量测序数据处理工具")
    print("   傻瓜式全自动流水线 v1.0")
    print("=" * 60)
    print()


def ask_template() -> str:
    print("请输入 SELEX 文库模板（固定碱基用 A/T/C/G，随机区用 N）：")
    print("示例：CGACTCAGTNNNNNNNNCGATCGNNNNNNCGATCG")
    print()
    while True:
        template = input("模板：").strip()
        if template:
            return template
        print("模板不能为空，请重新输入。")


def write_qc_report(qc_records: list, output_path: str):
    """输出 QC 报告"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("SELEX 测序处理 QC 报告\n")
        f.write("=" * 50 + "\n\n")
        for rec in qc_records:
            f.write(f"轮次：{rec['round']}\n")
            f.write(f"  总 reads：{rec['total']:,}\n")
            f.write(f"  匹配 reads：{rec['matched']:,}\n")
            rate = rec['matched'] / rec['total'] * 100 if rec['total'] else 0
            f.write(f"  匹配率：{rate:.2f}%\n")
            f.write(f"  唯一序列数：{rec['unique']:,}\n")
            if rec.get("top10"):
                f.write(f"  Top 10 序列：\n")
                for rank, (seq, cnt) in enumerate(rec["top10"], 1):
                    freq = cnt / rec['matched'] if rec['matched'] else 0
                    f.write(f"    {rank:2d}. {seq}  count={cnt}  freq={freq:.6f}\n")
            f.write("\n")


def process_round(round_data, pattern, group_count, logger):
    """处理单轮 SELEX 数据，返回 (csv_path, qc_record)"""
    rn = round_data.name
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    ensure_dir(tmp_dir)
    ensure_dir(RESULTS_DIR)

    # 收集该轮所有要处理的 FASTA/FASTQ 文件路径列表
    fasta_paths = []

    if round_data.is_paired:
        logger.info(f"[{rn}] 双端拼接，共 {len(round_data.pairs)} 对文件")
        for idx, (r1, r2) in enumerate(round_data.pairs, 1):
            merged_fasta = os.path.join(tmp_dir, f"{rn}_merged_{idx}.fasta")
            success = merge_paired_reads(r1, r2, merged_fasta, round_name=f"{rn}-{idx}")
            if success:
                fasta_paths.append(merged_fasta)
            else:
                logger.warning(f"[{rn}] 第 {idx} 对文件拼接失败，跳过。")
    else:
        logger.info(f"[{rn}] 单端测序，共 {len(round_data.single_files)} 个文件")
        for fp in round_data.single_files:
            # FASTQ 转为内存中流式处理（无需落盘）
            fasta_paths.append(fp)

    if not fasta_paths:
        logger.error(f"[{rn}] 没有可处理的文件，跳过该轮次。")
        return None, None

    # 流式读取所有文件，拼接成一个生成器
    def all_sequences():
        for fp in fasta_paths:
            yield from parse_sequences(fp)

    logger.info(f"[{rn}] 开始提取随机区序列...")
    counter, total, matched = extract_and_count(
        all_sequences(), pattern, group_count, round_name=rn
    )

    rate = matched / total * 100 if total else 0
    logger.info(
        f"[{rn}] 提取完成：总 reads={total:,}，匹配={matched:,}（{rate:.2f}%），"
        f"唯一序列={len(counter):,}"
    )

    csv_path = compute_and_save(counter, matched, rn, RESULTS_DIR)

    qc_rec = {
        "round": rn,
        "total": total,
        "matched": matched,
        "unique": len(counter),
        "top10": counter.most_common(10),
    }

    # 清理临时拼接文件
    for fp in fasta_paths:
        if fp.startswith(tmp_dir) and os.path.isfile(fp):
            os.remove(fp)

    return csv_path, qc_rec


def main():
    ensure_dir(LOGS_DIR)
    setup_logger("selex")
    logger = get_logger()

    print_banner()
    logger.info(f"程序启动，项目目录：{BASE_DIR}")
    logger.info(f"CPU 核心数：{get_cpu_count()}")

    # 1. 获取模板
    template_str = ask_template()
    print()

    # 2. 解析模板
    logger.info("正在解析文库模板...")
    pattern, group_count = parse_template(template_str)

    # 3. 扫描数据目录
    logger.info(f"正在扫描数据目录：{DATA_DIR}")
    rounds = scan_data_dir(DATA_DIR)
    logger.info(f"共检测到 {len(rounds)} 轮 SELEX 数据")

    # 4. 逐轮处理
    csv_results = []   # [(round_name, csv_path), ...]
    qc_records = []

    for rd in rounds:
        logger.info(f"\n{'='*40}")
        logger.info(f"正在处理轮次：{rd.name}")
        csv_path, qc_rec = process_round(rd, pattern, group_count, logger)
        csv_results.append((rd.name, csv_path))
        if qc_rec:
            qc_records.append(qc_rec)

    # 5. 汇总
    logger.info("\n正在生成多轮汇总 CSV...")
    summary_path = os.path.join(RESULTS_DIR, "all_rounds_summary.csv")
    merge_all_rounds(csv_results, summary_path)

    # 6. QC 报告
    qc_path = os.path.join(RESULTS_DIR, "qc_report.txt")
    write_qc_report(qc_records, qc_path)
    logger.info(f"QC 报告已输出：{qc_path}")

    # 7. 完成
    print()
    print("=" * 60)
    print("  处理完成！输出文件：")
    for rn, cp in csv_results:
        if cp:
            print(f"    results/{rn}.csv")
    print(f"    results/all_rounds_summary.csv")
    print(f"    results/qc_report.txt")
    print(f"    logs/pipeline.log")
    print("=" * 60)
    logger.info("全流程完成。")


if __name__ == "__main__":
    main()
