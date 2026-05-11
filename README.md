# SELEX 高通量测序数据处理工具

傻瓜式全自动 SELEX 流水线，非编程用户开箱即用。

---

## 安装方法

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装系统依赖（用于编译 PANDAseq）

Ubuntu/Debian：

```bash
sudo apt-get install -y autoconf libtool pkg-config zlib1g-dev libbz2-dev libgsl-dev
```

CentOS/RHEL：

```bash
sudo yum install -y autoconf libtool pkgconfig zlib-devel bzip2-devel gsl-devel
```

> PANDAseq 会在首次运行时**自动编译**，无需手动操作。

---

## 数据组织方式

将每轮测序数据放入对应子目录：

```
data/
├── R1/
│   ├── sample_R1.fastq.gz
│   └── sample_R2.fastq.gz
├── R2/
│   ├── sample_R1.fastq.gz
│   └── sample_R2.fastq.gz
├── R3/
│   └── sample.fastq.gz     ← 单端测序直接放文件
```

支持的文件格式：

| 格式 | 扩展名 |
|------|--------|
| FASTQ | `.fastq` `.fq` `.fastq.gz` `.fq.gz` |
| FASTA | `.fasta` `.fa` `.fa.gz` |

---

## 使用方法

```bash
python src/main.py
```

程序启动后输入文库模板，例如：

```
请输入 SELEX 文库模板：CGACTCAGTNNNNNNNNCGATCGNNNNNNCGATCG
```

程序将自动完成所有步骤并输出结果。

---

## 模板格式说明

| 字符 | 含义 |
|------|------|
| A/T/C/G | 固定碱基 |
| N | 随机碱基（随机区） |

示例：

```
CGACTCAGTNNNNNNNNCGATCG
         ^^^^^^^^
         这8个N是随机区，程序会统计这里的序列频率
```

生成的正则：`CGACTCAGT([ATCG]{8})CGATCG`

---

## 输出说明

```
results/
├── R1.csv                   ← 第1轮频率统计
├── R1_top100.fasta          ← 第1轮 Top 100 序列
├── R2.csv
├── R2_top100.fasta
├── all_rounds_summary.csv   ← 多轮汇总（宽格式）
└── qc_report.txt            ← QC 质控报告

logs/
├── pipeline.log             ← 完整运行日志
└── error.log                ← 错误日志
```

### CSV 格式

每轮 CSV（如 `R1.csv`）：

| sequence | count | frequency |
|----------|-------|-----------|
| ATCGGGTA | 10000 | 0.123456  |

汇总 CSV（`all_rounds_summary.csv`）：

| sequence | R1_count | R1_freq | R2_count | R2_freq |
|----------|----------|---------|----------|---------|
| ATCGGGTA | 10000    | 0.1234  | 0        | 0.0000  |

---

## 常见错误

### PANDAseq 编译失败

```
PANDAseq 安装失败，请查看日志：logs/pandaseq_build.log
常见原因：缺少 autoconf / libtool / zlib-dev 等依赖
```

解决：安装系统依赖后重新运行。

### 模板非法字符

```
模板存在非法字符：X
仅允许 A/T/C/G/N
```

解决：检查模板，只能包含 `A/T/C/G/N`（大小写均可，空格自动忽略）。

### 双端文件配对失败

```
检测到双端文件数量不一致
```

解决：确保每对文件命名格式为 `xxx_R1.fastq.gz` + `xxx_R2.fastq.gz`。

### 没有找到数据

```
data/ 目录下没有找到任何子目录
```

解决：在 `data/` 下创建轮次子目录（如 `R1/`、`R2/`）并放入测序文件。

---

## 性能说明

- 支持 10GB+ 文件，千万级 reads
- 流式处理，内存占用低
- 自动使用全部 CPU 核心
