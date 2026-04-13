# Generated Infographic

## Infographic Request
- version: v2
- language: 简体中文
- detail_level: 标准
- direction: 横向
- aspect: landscape
- layout: bento-grid
- style: craft-handmade

## Source Content
[2303.06865v2.pdf]: FlexGen: High-Throughput Generative Inference of Large Language Models
with a Single GPU
Ying Sheng 1 Lianmin Zheng 2 Binhang Yuan3 Zhuohan Li 2 Max Ryabinin 4 5 Daniel Y. Fu1 Zhiqiang Xie 1
Beidi Chen 6 7 Clark Barrett 1 Joseph E. Gonzalez 2 Percy Liang 1 Christopher R´e 1 Ion Stoica 2 Ce Zhang 3
Abstract
The high computational and memory require-
ments of large language model (LLM) inference
make it feasible only with multiple high-end ac-
celerators. Motivated by the emerging demand for
latency-insensitive tasks with batched processing,
this paper initiates the study of high-throughput
LLM inference using limited resources, such as
a single commodity GPU. We present FlexGen,
a high-throughput generation engine for running
LLMs with limited GPU memory. FlexGen can
be flexibly configured under various hardware re-
source constraints by aggregating memory and
computation from the GPU, CPU, and disk. By
solving a linear programming problem, it searches
for efficient patterns to store and access tensors.
FlexGen further compresses the weights and the
attention cache to 4 bits with negligible accu-
racy loss. These techniques enable FlexGen to
have a larger space of batch size choices and
thus significantly increase maximum throughput.
As a result, when running OPT-175B on a sin-
gle 16GB GPU, FlexGen achieves significantly
higher throughput compared to state-of-the-art of-
floading systems, reaching a generation through-
put of 1 token/s for the first time with an effec-
tive batch size of 144. On the HELM bench-
mark, FlexGen can benchmark a 30B model with
a 16GB GPU on 7 representative sub-scenarios
in 21 hours. The code is available at https:
//github.com/FMInference/FlexGen.
1Stanford University 2UC Berkeley 3ETH Zurich 4Yandex
5HSE University 6Meta 7Carnegie Mellon University. Correspon-
dence to: Ying Sheng <ying1123@stanford.edu>.
Proceedings of the 40 th International Conference on Machine
Learning, Honolulu, Hawaii, USA. PMLR 202, 2023. Copyright
2023 by the author(s).
This version has an extended author list compared to the
one archived in ICML.
211
213
Latency (s)
20
2 2
2 4
2 6
2 8
OPT-175B
FlexGen (c) FlexGen DeepSpeed Accelerate
28
29
210
Latency (s)
23
21
2 1
2 3
OPT-30B
Generation throughput (token/s)
Figure 1. The total latency for a block and throughput trade-offs of
three offloading-based systems for OPT-175B (left) and OPT-30B
(right) on a single NVIDIA T4 (16 GB) GPU with 208 GB CPU
DRAM and 1.5TB SSD. FlexGen achieves a new Pareto-optimal
frontier with 100× higher maximum throughput for OPT-175B.
Other systems cannot further increase throughput due to out-of-
memory issues. “(c)” denotes compression.
1. Introduction
In recent years, large language models (LLMs) have
demonstrated strong performance across a wide range of
tasks (Brown et al., 2020; Bommasani et al., 2021; Zhang
et al., 2022; Chowdhery et al., 2022). Along with these un-
precedented capabilities, generative LLM inference comes
with unique challenges. These models can have billions, if
not trillions of parameters (Chowdhery et al., 2022; Fedus
et al., 2022), which leads to extremely high computational
and memory requirements to run. For example, GPT-175B
requires 325GB of GPU memory simply to load its model
weights. Fitting this model onto GPUs would require at least
five A100 (80GB) GPUs and complex parallelism strate-
gies (Pope et al., 2022; Aminabadi et al., 2022). Thus,
lowering LLM inference resource requirements has recently
attracted intense interest.
In this paper, we focus on a setting that we call throughput-
oriented generative inference . In addition to interactive
use cases such as chatbots, LLMs are also applied to many
“back-of-house” tasks such as benchmarking (Liang et al.,
2022), information extraction (Narayan et al., 2018), data
wrangling (Narayan et al., 2022), and form processing (Chen
et al., 2021). One key characteristic of these tasks is that they
often require running LLM inference in batches over a large
number of tokens (e.g., all the documents in a company’s
1
arXiv:2303.06865v2  [cs.LG]  12 Jun 2023

FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU
corpus), and are less sensitive to latency. As a result, it
is possible to trade off latency for higher throughput in
these workloads, providing opportunities to reduce resource
requirements.
Prior efforts to lower resource requirements of LLM infer-
ence correspond to three directions: (1) model compression
to decrease total memory footprint (Dettmers et al., 2022;
Yao et al., 2022; Frantar et al., 2022; Xiao et al., 2022);
(2) collaborative inference to amortize inference cost via
decentralization (Borzunov et al., 2022); and (3) offloading
to utilize memory from CPU and disk (Aminabadi et al.,
2022; HuggingFace, 2022). These techniques have signifi-
cantly lowered the resource requirements for using LLMs,
but there are distinct limitations. Research in the first two
directions often assume that the model fits into the GPU
memory and thereby struggle to run 175B-scale models with
a single commodity GPU. On the other hand, state-of-the-
art offloading-based systems in the third category do not
achieve acceptable throughput on a single GPU due to inef-
ficient I/O scheduling and tensor placement. For example,
these systems can be bottlenecked by small batch sizes (e.g.,
batch sizes of only one or two for OPT-175B in some cases).
16 GB208GB1.5 TB
GPUCPUDisk
12 GB/s2 GB/s
Our focus is designing efficient
offloading strategies for high-
throughput generative inference,
on a single commodity GPU . To
run an LLM with limited GPU
memory, we can offload it to sec-
ondary storage and perform com-
putation part-by-part by partially loading it. On a typical
machine, there are three levels of the memory hierarchy, as
illustrated in the figure to the right. Higher levels are faster
but scarce, while lower levels are slower but abundant. In
throughput-oriented scenarios, we can sacrifice latency by
using a large batch size, and amortize the expensive I/O
operations among different memory hierarchies over a large
batch of inputs, overlapped with computation. Fig. 1 shows
the latency-throughput trade-off of three inference systems
with offloading on a single NVIDIA T4 (16 GB) GPU. Note
that the performance in terms of latency and throughput on
limited resources is significantly inferior to that of the cases
with sufficient resources.
Achieving high-throughput generative inference with lim-
ited GPU memory is challenging even if we can sacrifice
the latency. The first challenge is to design an efficient of-
floading strategy. During generative inference, there are
three kinds of tensors: weights, activations, and key-value
(KV) cache. The strategy should specify what tensors to of-
fload, where to offload them within the three-level memory
hierarchy, and when to offload them during inference. The
batch-by-batch, token-by-token, and layer-by-layer struc-
ture of the computation forms a complex dependency graph
where there are multiple ways to conduct computation. To-
gether, these choices form a complex design space. Existing
offloading-based inference systems (Aminabadi et al., 2022;
HuggingFace, 2022) inherit strategies from training, which
turn out to be some suboptimal points for inference, per-
forming excessive I/O and achieving throughput far below
theoretical hardware limits.
The second challenge is to develop effective compression
strategies. Previous works have demonstrated promising
results in compressing the weights and activations of LLMs.
However, when combining compression with offloading for
high-throughput inference, the I/O costs and memory reduc-
tion of the weights and KV cache become more important,
motivating alternative compression schemes.
To address these challenges, we present FlexGen, an of-
floading framework for high-throughput LLM inference.
FlexGen aggregates memory from the GPU, CPU, and disk,
and efficiently schedules I/O operations, along with possible
compression methods and distributed pipeline parallelism.
(Contribution 1) We formally define a search space of
possible offloading strategies by considering computation
schedule, tensor placement, and computation delegation.
We prove that our search space captures a computation
order with I/O complexity within 2× of optimality. We
then develop a linear programming-based search algorithm
to optimize the throughput within the search space. This
algorithm can be configured for various hardware specifica-
tions and can be easily extended to incorporate latency and
throughput constraints, thus helping to navigate the trade-
off space smoothly. Compared with existing strategies, our
solution unifies the placement of weights, activations, and
the KV cache, enabling a dramatically higher batch size
upper bound, which is key to achieving high throughput.
(Contribution 2) We show that it is possible to compress
both the weights and KV cache for LLMs like OPT-175B to
4 bits without retraining or calibration, all with negligible
accuracy loss. This is achieved through fine-grained group-
wise quantization (Shen et al., 2020), which is suitable for
reducing I/O costs and memory usage during offloading.
(Contribution 3) We demonstrate the efficiency of FlexGen
by running OPT-175B on NVIDIA T4 (16GB) GPUs. Com-
pared to DeepSpeed Zero-Inference (Aminabadi et al.,
2022) and Hugging Face Accelerate (HuggingFace, 2022),
two state-of-the-art offloading-based inference systems,
FlexGen often allows a batch size that is orders of mag-
nitude larger. As a result, FlexGen can achieve much higher
throughputs. On a single T4 GPU with 208 GB CPU DRAM
and 1.5 TB SSD, input sequence length 512, and output se-
quence length 32:
• With the same latency of5000 seconds, FlexGen (effec-
tive batch size 64, or 2048 tokens in total) can achieve
2

FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU
more than 40× higher throughput than DeepSpeed
