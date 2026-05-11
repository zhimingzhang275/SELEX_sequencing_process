# 需求
# SELEX测序处理软件需求文档（Claude Code开发版）

## 项目目标

开发一个面向非编程用户的 SELEX 高通量测序数据处理软件。

用户只需要：

1. 把每轮测序数据放入指定目录
2. 输入文库模板（例如：CGACTCAGTNNNNNNNNCGATCGTNNNNNNCGATCG）
3. 点击运行

软件自动完成：

* 自动识别单端/双端测序
* 自动安装并编译 PANDAseq
* 双端拼接
* FASTA 提取
* SELEX 文库序列正则匹配
* 序列统计
* frequency 排序
* 多轮次汇总
* 输出 CSV

整个流程必须高度鲁棒、自动化、无代码操作。

---

# 一、目录结构要求

项目根目录：

```bash
/home/ubuntu/data/sequencing_process
```

数据目录：

```bash
/home/ubuntu/data/sequencing_process/data
```

PANDAseq源码目录：

```bash
/home/ubuntu/data/sequencing_process/pandaseq
```

用户数据组织方式：

```bash
data/
├── R1/
│   ├── *.fastq
│   ├── *.fq
│   ├── *_R1.fastq.gz
│   └── *_R2.fastq.gz
├── R2/
├── R3/
├── R4/
```

每个文件夹代表一轮 SELEX。

---

# 二、核心功能需求

---

# 1. 自动识别测序类型

软件需要自动判断：

## 单端测序

例如：

```bash
sample.fastq
sample.fq.gz
```

则直接进入后续处理。

---

## 双端测序

例如：

```bash
xxx_R1.fastq.gz
xxx_R2.fastq.gz
```

或者：

```bash
xxx_1.fastq.gz
xxx_2.fastq.gz
```

自动识别为 paired-end。

---

# 2. 自动安装 PANDAseq

PANDAseq 已经存在于：

```bash
/home/ubuntu/data/sequencing_process/pandaseq
```

软件启动时自动检测：

```bash
pandaseq/bin/pandaseq
```

是否存在。

如果不存在：

自动执行：

```bash
./autogen.sh
./configure
make
make install
```

要求：

* 自动检测依赖
* 自动报错提示
* 自动写入日志
* 用户无需任何操作

---

# 3. 双端测序拼接

如果检测为 paired-end：

自动调用 PANDAseq：

示例：

```bash
pandaseq -f xxx_R1.fastq.gz -r xxx_R2.fastq.gz
```

输出：

```bash
merged.fasta
```

要求：

* 自动识别 gzip
* 自动设置线程数
* 自动判断 overlap
* 自动过滤低质量拼接
* 失败自动重试
* 输出日志

建议参数：

```bash
pandaseq \
-f R1.fastq.gz \
-r R2.fastq.gz \
-w merged.fasta \
-g pandaseq.log \
-T 8
```

---

# 4. FASTA转换

如果输入是 FASTQ：

自动转换 FASTA。

要求：

* 保留 read id
* 自动兼容 gzip
* 自动检测编码
* 超大文件流式处理（不能一次读入内存）

---

# 5. 文库模板输入（核心）

用户不会正则表达式。

因此软件需要支持：

## 用户输入格式

例如：

```text
CGACTCAGTNNNNNNNNCGATCGTNNNNNNCGATCG
```

规则：

* A/T/C/G 为固定碱基
* N 表示任意碱基

---

# 6. 自动转换为正则表达式

例如：

输入：

```text
CGACTCAGTNNNNNNNNCGATCG
```

自动转换：

```python
CGACTCAGT[ATCG]{8}CGATCG
```

要求：

* 自动识别连续 N
* 自动压缩正则
* 忽略大小写
* 自动兼容 U/T
* 自动去除空格
* 自动检查非法字符

非法字符报错：

```text
模板存在非法字符：X
仅允许 A/T/C/G/N
```

---

# 7. 序列提取

从 FASTA 中提取：

* 所有匹配模板的序列
* 统计出现次数

例如：

模板：

```text
AAAANNNNCCCC
```

序列：

```text
AAAATTTTCCCC
```

则匹配成功。

---

# 8. 提取目标区域（重要）

除了匹配整个模板，还需要：

## 提取随机区

例如：

模板：

```text
CGACTCAGTNNNNNNNNCGATCG
```

提取：

```text
NNNNNNNN
```

对应真实序列：

```text
ATCGGGTA
```

最终统计随机区序列 frequency。

这是 SELEX 的核心。

---

# 9. Frequency统计

统计：

```text
sequence,count,frequency
```

frequency：

```python
count / total_matched_reads
```

保留：

```text
6位小数
```

---

# 10. 每轮输出CSV

每轮：

```bash
results/R1.csv
results/R2.csv
```

格式：

| sequence | count | frequency |
| -------- | ----- | --------- |
| ATCGGGTA | 10000 | 0.123456  |

要求：

* frequency 降序排列
* UTF-8编码
* 自动去重
* 超大数据优化

---

# 11. 总表输出（关键）

最终输出：

```bash
results/all_rounds_summary.csv
```

格式：

| sequence | R1_count | R1_freq | R2_count | R2_freq |
| -------- | -------- | ------- | -------- | ------- |

规则：

* 所有轮次序列取并集
* 某轮不存在填0
* frequency 保留6位

例如：

| sequence | R1_count | R2_count |
| -------- | -------- | -------- |
| AAAA     | 100      | 0        |
| CCCC     | 20       | 50       |

---

# 三、鲁棒性要求（非常重要）

---

# 1. 自动识别压缩格式

支持：

```bash
.fastq
.fastq.gz
.fq
.fq.gz
.fasta
.fa
.fa.gz
```

---

# 2. 超大文件处理

必须：

* 流式读取
* 不能一次读入内存
* 支持千万级reads

建议：

```python
yield
generator
```

---

# 3. 自动日志系统

输出：

```bash
logs/
```

包括：

```bash
pipeline.log
pandaseq.log
error.log
```

记录：

* 时间
* 轮次
* reads数量
* 匹配数量
* 错误信息

---

# 4. 自动异常处理

例如：

## R1/R2数量不一致

自动报错：

```text
检测到双端文件数量不一致
```

---

## 拼接失败

自动：

* 重试
* 跳过
* 写日志

---

## 模板不合法

直接终止。

---

# 5. 自动CPU优化

自动检测：

```python
os.cpu_count()
```

用于：

* PANDAseq线程
* 多进程统计

---

# 四、建议技术实现

推荐：

## Python版本

```bash
Python 3.10+
```

---

## 推荐依赖

```bash
biopython
pandas
regex
tqdm
gzip
multiprocessing
```

---

# 五、推荐模块结构

```bash
sequencing_process/
├── data/
├── results/
├── logs/
├── pandaseq/
├── src/
│   ├── main.py
│   ├── detect.py
│   ├── pandaseq_wrapper.py
│   ├── fasta_parser.py
│   ├── template_parser.py
│   ├── extractor.py
│   ├── statistics.py
│   ├── merger.py
│   ├── utils.py
│   └── logger.py
```

---

# 六、命令行设计（用户友好）

用户运行：

```bash
python main.py
```

程序自动：

1. 扫描 data/
2. 检测轮次
3. 检测单双端
4. 安装pandaseq
5. 拼接
6. 提取序列
7. 输出CSV
8. 输出summary

---

# 七、用户输入设计（极简）

程序启动后：

```text
请输入SELEX文库模板:
```

用户输入：

```text
CGACTCAGTNNNNNNNNCGATCG
```

即可。

---

# 八、性能要求

要求支持：

* 10GB+
* 千万reads
* 多轮SELEX

运行时：

* 内存占用尽量低
* CPU并行
* 支持断点恢复（可选）

---

# 九、额外增强功能（建议实现）

## 1. 自动生成QC报告

输出：

```bash
qc_report.txt
```

包括：

* 总reads
* 匹配reads
* 匹配率
* Top10序列

---

## 2. Top N序列导出

例如：

```bash
top100.fasta
```

---

## 3. 自动绘图

输出：

* frequency变化曲线
* 富集趋势图

---

# 十、最终目标

做成：

## “傻瓜式 SELEX测序处理工具”

用户：

* 不需要会Python
* 不需要会Linux
* 不需要会正则
* 不需要安装软件

只需要：

1. 放数据
2. 输入模板
3. 运行

即可得到：

* 每轮频率统计
* 富集结果
* 总表
* 可直接用于后续分析的数据

---

# 十一、关键实现细节（必须）

## 模板匹配逻辑

模板：

```text
CGACTNNNNNTTAA
```

真正统计的是：

```text
NNNNN
```

即随机区。

固定区用于定位。

---

## 正则生成示例

输入：

```text
AAANNNNNNTTTNN
```

生成：

```python
AAA([ATCG]{6})TTT([ATCG]{2})
```

最后：

提取：

```python
group(1) + group(2)
```

得到完整随机区。

---

# 十二、代码质量要求

要求：

* 模块化
* 可维护
* 高鲁棒性
* 日志完善
* 错误提示清晰
* 用户看得懂
* 注释详细

---

# 十三、最终交付形式

输出：

```bash
python main.py
```

即可运行。

同时生成：

```bash
requirements.txt
README.md
```

README 必须写：

* 安装方法
* 使用方法
* 常见错误
* 输入格式示例
* 输出说明

---

# 十四、开发优先级

优先实现：

1. 单/双端识别
2. PANDAseq拼接
3. 模板转正则
4. 随机区提取
5. frequency统计
6. 汇总CSV

然后：

7. QC
8. 绘图
9. GUI（未来）

---

# 十五、最终效果（用户视角）

用户：

```bash
python main.py
```

程序：

```text
检测到4轮SELEX数据
检测到双端测序
正在安装PANDAseq...
正在拼接...
正在提取序列...
正在统计频率...
输出完成
```

最终得到：

```bash
results/
├── R1.csv
├── R2.csv
├── R3.csv
├── summary.csv
└── qc_report.txt
```
