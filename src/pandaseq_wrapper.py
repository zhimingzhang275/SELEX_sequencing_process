"""自动编译 PANDAseq 并调用进行双端拼接"""
import os
import subprocess
import sys
import time
from logger import get_logger
from utils import get_cpu_count
from paths import get_base_dir, get_pandaseq_bin, get_pandaseq_lib_dir, is_bundled

logger = get_logger()

BASE_DIR = get_base_dir()
PANDASEQ_SRC = os.path.join(BASE_DIR, "pandaseq")


def ensure_pandaseq() -> str:
    """
    确保 pandaseq 已编译可用。若不存在则自动编译（仅开发模式）。
    返回 pandaseq 可执行文件路径。
    """
    pandaseq_bin = get_pandaseq_bin()

    if os.path.isfile(pandaseq_bin) and os.access(pandaseq_bin, os.X_OK):
        logger.info(f"PANDAseq 已就绪：{pandaseq_bin}")
        return pandaseq_bin

    if is_bundled():
        logger.error("打包版本中未找到 PANDAseq，程序包可能损坏。")
        sys.exit(1)

    # 开发模式：自动编译
    logger.info("PANDAseq 未编译，开始自动安装...")

    if not os.path.isdir(PANDASEQ_SRC):
        logger.error(f"PANDAseq 源码目录不存在：{PANDASEQ_SRC}")
        sys.exit(1)

    steps = [
        (["bash", "autogen.sh"], "运行 autogen.sh"),
        (["./configure", f"--prefix={PANDASEQ_SRC}"], "运行 configure"),
        (["make", f"-j{get_cpu_count()}"], "编译（make）"),
        (["make", "install"], "安装（make install）"),
    ]

    for cmd, desc in steps:
        logger.info(f"PANDAseq 安装：{desc}...")
        log_path = os.path.join(BASE_DIR, "logs", "pandaseq_build.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, "a", encoding="utf-8") as log_f:
            result = subprocess.run(cmd, cwd=PANDASEQ_SRC, stdout=log_f, stderr=log_f)

        if result.returncode != 0:
            logger.error(
                f"PANDAseq 安装失败（{desc}），返回码 {result.returncode}。\n"
                f"请查看日志：{log_path}\n"
                f"常见原因：缺少 autoconf / libtool / zlib-dev 等依赖。"
            )
            sys.exit(1)

    if not os.path.isfile(pandaseq_bin):
        logger.error(f"编译完成但未找到可执行文件：{pandaseq_bin}")
        sys.exit(1)

    logger.info("PANDAseq 安装成功！")
    return pandaseq_bin


def _make_env_with_lib():
    """构造包含 libpandaseq 路径的环境变量（打包模式下必须）"""
    env = os.environ.copy()
    lib_dir = get_pandaseq_lib_dir()
    existing = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = f"{lib_dir}:{existing}" if existing else lib_dir
    return env


def merge_paired_reads(
    r1_path: str,
    r2_path: str,
    output_fasta: str,
    round_name: str = "",
    max_retries: int = 1,
) -> bool:
    """
    调用 pandaseq 拼接双端 reads，输出 FASTA。
    失败自动重试一次。返回是否成功。
    """
    pandaseq = ensure_pandaseq()
    cpu = get_cpu_count()
    log_path = os.path.join(BASE_DIR, "logs", f"pandaseq_{round_name}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    cmd = [
        pandaseq,
        "-f", r1_path,
        "-r", r2_path,
        "-w", output_fasta,
        "-g", log_path,
        "-T", str(cpu),
    ]

    env = _make_env_with_lib()

    for attempt in range(max_retries + 1):
        prefix = f"[{round_name}]" if round_name else ""
        logger.info(f"{prefix} 开始拼接双端 reads（尝试 {attempt + 1}/{max_retries + 1}）")
        logger.info(f"  R1: {os.path.basename(r1_path)}")
        logger.info(f"  R2: {os.path.basename(r2_path)}")

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0 and os.path.isfile(output_fasta):
            size = os.path.getsize(output_fasta)
            if size > 0:
                logger.info(f"{prefix} 拼接成功：{output_fasta}（{size:,} 字节）")
                return True
            else:
                logger.warning(f"{prefix} 拼接输出文件为空。")

        logger.warning(
            f"{prefix} 拼接失败（返回码 {result.returncode}）"
            + (f"，将重试..." if attempt < max_retries else "，已放弃。")
        )
        if result.stderr:
            logger.debug(f"stderr: {result.stderr[:500]}")
        if attempt < max_retries:
            time.sleep(2)

    logger.error(f"[{round_name}] PANDAseq 拼接失败，跳过该轮次。")
    return False
