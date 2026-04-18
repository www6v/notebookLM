A State-of-the-Art SQL Reasoning Model using RLVR
The Databricks Mosaic Research and Genie Teamsa
Developing custom reasoning models via Reinforcement Learning (RL) that can incorporate
organization-specific knowledge has great potential to address problems faced by enterprise
customers. In many of these problems, the reward function is verifiable, a setting termed
RL with Verifiable Rewards (RLVR). We apply RLVR to a popular data science benchmark
called BIRD that measures the ability of an AI agent to convert natural language query
for a database to SQL executions. We apply a simple and general-purpose training recipe
involving careful prompt and model selection, a warm-up stage using our offline RL approach
called TAO, followed by rigorous online RLVR training. With no additional training data
beyond the BIRD training set and no use of proprietary models, our very first submission
to the BIRD leaderboard reached state-of-the-art accuracy on the private test set: 73.56%
without self-consistency and 75.68% with self-consistency. In the latter case, our model also
required fewer generations than the second-best approach. While BIRD is only a proxy task,
the simplicity of our framework makes it broadly applicable to enterprise domains such as
business intelligence, data science, and coding.
aA complete list of contributors is given in the appendix.
1 Introduction
LLMs have become a fixture in a range of enterprise problems including software engineering [45],
data science [11], and more recently even research itself [ 9]. However, despite sometime impres-
sive performance of off-the-shelf LLMs, they face limitations in doing more bespoke enterprise
tasks displaying limitations such as unable to understand organization-specific terminology or use
organization-specific concepts, tools, and APIs. Post-training LLMs using approaches such as Rein-
forcement Learning with Verifiable Rewards (RLVR) [8, 12, 42] provides one way to address this. In
this report, we show how we applied RLVR to fine-tune an LLM to achieve state-of-the-art reasoning
model on the popular data science benchmark BIRD [20].
Figure 1 shows an example of the text2sql task which is a common data science task of allowing a
user to query a database. In tasks such as these, off-the-shelf LLMs can struggle for various reasons.
For example, different organizations or industries might use specific jargon that may not be present
in LLM’s knowledge. For example, given a user query“show me all churned users for 2024?", the
model may not know how the organization defines“churned users". Or, the model may not be aware
of certain preferences such as always sorting certain queries with a given column. And yet other
reasons, can be not knowing how to use certain APIs, tools, and know where to find data. Unlike math
problems where the training data might be more available on the internet, organizational knowledge
might be more protected and less represented on the internet posing challenges for LLMs whose
training data may not cover this.
There are several ways to address this knowledge gap. Post-training LLMs through approaches such
as RLVR provide one way to address this knowledge gap. In particular, for data science and coding
tasks, one can often compute averifiable rewardwhich does not need to be trained and serves as an
objective quality metric. For the task in Figure 1, we can measure if a given AI agent’s SQL response
is correct by matching it against the ground truth SQL response for that user query. Other approaches
such as GEPA [1] approach this by optimizing prompts instead of LLM weights. At Databricks
we support both these approaches along with a suite of other methods. The preference for a given
approach can depend on the type of dataset and other resource requirements. In this report, we focus
on RLVR and demonstrate its power by applying it to the BIRD benchmark (Figure 1).
Our approach starts by carefully selecting the model, context, and prompt. The prompt can be
chosen using prompt optimization approaches such as GEPA [15, 1]. We then perform a two-stage
fine-tuning of the model with the chosen context and prompt. First, we warm start the model using
Test-time Adaptive Optimization (TAO), an offline RL approach [2]. This is followed by fine-tuning
1
arXiv:2509.21459v1  [cs.CL]  25 Sep 2025

Offline TAO Stage + Online RLVR StageBird Train Set
Name the movie with 
the most ratings.
Database Schema
  Table name: actor
   - Column: ActorID, Integer, etc. 
   - Column: Name, Integer, etc.
Databases
Gold SQL
  SELECT movie_title   
   FROM movies ……
LLM
Response 1
Response 2
Response k
1
0
-1
Veriﬁable 
Reward (VR)
TAO  
Optimization 
loss
time
RLVR  
Optimization 
loss
time
Figure 1: Illustration of our RLVR-based fine-tuning pipeline applied to text-to-SQL. Given a user
query (e.g., “Name the movie with the most ratings”) together with the structure of relevant database
tables and associated domain knowledge, the goal is to produce SQL that matches the reference
(“gold”) SQL shown in the lower left. Our pipeline generates verifiable rewards by sampling k
candidate SQL queries from the current model, executing them, and comparing results against the
gold SQL. These RLVR rewards are then used to update the model with either TAO our offline RL
approach, or an online RLVR optimization.
the model using Databricks’s RLVR service. Our RLVR service supports popular learning approaches
such as GRPO [ 35], as well as more powerful alternatives. Finally, we perform self-consistency
on top of the fine-tuned model at inference time. This general recipe allowed us to establish a new
state-of-the-art accuracy of75.68%on the private test set of the BIRD benchmark in single-model
category with our first submission.1 Our RLVR-trained model already achieves state-of-the-art in
single-model single-LLM call category, whereas self-consistency adds complimentary benefits and
gives us the overall best single-model performance. Further, our model generalizes better than other
top-submissions and achieves state-of-the-art using fewer self-consistency responses than the second
best result.
2 Overview
We first provide an overview of our setup and approach.
Reinforcement Learning from Verifiable Rewards (RLVR).RLVR is a post-training paradigm
of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward
function measures an objective truth without needing any parametrized reward models [ 8, 12, 42,
32]. RLVR is particulary suited to tasks where the LLM is trying to predict facts, mathematical
statements, or generating executable code, as its responses can be measured objectively given access
to ground truth. This contrasts with non-verifiable tasks that typically measure subjective tasks such
as generating poetry, or an essay on a given topic [4]. Significant focus has been on applying RLVR to
maths and coding tasks [32]. An important current challenge is applying RLVR to complex enterprise
tasks such as business analysis and data science workflows.
Text2SQL.In this report, we focus on evaluation on an important data science problem called
text2sql [7, 26, 13, 20]. In this task, a user asks a natural language query x∈ X to access a database
d∈ D . An agent then generates a SQL code y∈ Y which is executed on the database and its output
is returned to the user. The goal of the agent is to generate a SQL code that best captures the intent
of the user query. The main challenge in text2sql is that it requires understanding the query in the
1BIRD benchmark is available here: https://bird-bench.github.io/. All numbers are current as of September
15th, 2025.
2

O1
O3-mini GPT-4o
GPT-4o-mini
Claude Sonnet
Llama 3.1 8b InstructLlama 3.1 70b InstructLlama 3.3 70b InstructGemma 3 1b InstructGemma 3 4b InstructGemma 3 12b InstructGemma 3 27b Instruct
DeepSeek R1 Distill Llama 70b
Qwen 2.5 Coder Instruct
Qwen 3-32B
Qwen QwQ 32B
LLMs
0
10
20
30
40
50
60Bird Evaluation Metric
62.39 62.39 63.82
58.28 59.26
41.92
63.43 63.43
4.76
34.75
52.93
60.43
57.95
64.80
60.50 60.82
Results for Various Vanilla LLMs on BIRD
Figure 2: Results on the BIRD dev set across a range of models. We perform greedy decoding for all
models except O1 and O3-mini which only permit temperature based decoding.
context of the database which can be quite complex. For example, the database may have many tables
with many columns, column names can be ambiguous, correct column values may need to be found
and tables may need to be joined to answer the user query.
We approach this problem relying on a reasoning-based LLM [30, 35, 44] P by encoding the context
x and database d in a prompt and then querying the LLM z∼P(· |x, d) to generate a reasoning
trace z∈ Z including the SQL response. The SQL response is marked using delimiters which allows
us to extract it from the trace. We focus on how to fine-tune an LLM on this task using RLVR.
We evaluate on the BIRD benchmark which is a popular text2sql benchmark [20]. A BIRD datapoint
includes a user query, an evidence field providing additional instruction, a database containing
multiple tables, and a gold SQL code denoting ground truth. We combine user query and evidence
into a single unified user query. The evaluation metric for BIRD is a strict 0-1 metric where given the
generated SQL code, we execute both the gold SQL and the generated SQL code on the database and
check if their outputs match (1) or not (0). The BIRD dataset consists of a train set of 9,428 examples,
a dev set of 1,534 examples, and a test set of 1,789 examples. The test set is not publicly available
allowing evaluation without dataset contamination concerns and prevents benchmark hacking [48].
We train the model using the train set and use the dev set performance for model and hyperparameter
selection. We do not use any additional training data.
Test-time Computation.Test-time computation is any approach that spends more inference
compute at test time to improve a model’s performance. One common test-time computation
approach is self-consistency [41] which involves generating multiple responses from an LLM and
then using a procedure to select the most consistent response. We will use self-consistency on top
of our RLVR-ed model.
3 Methodology
In this section, we provide an overview of our methodology.
Prompt and Model Selection.We evaluated a range of open-source models along with closed-
source models on a range of different prompts on the BIRD dev set. We found that the Qwen 2.5 32B
Coder Instruct model produced the best dev performance. This matches the best result reported in the
literature by the OmniSQL study [18]. We show results in Figure 2.
Perhaps surprisingly, we found that proprietary LLMs such as GPT-4o, O3, Claude Sonnet do not do
as well as Qwen and Llama on this task. This challenges the common belief that proprietary LLMs
are always a better choice. We leave further investigation of this for future work.
3

We found that OmniSQL prompt was a good starting point. However, we made important modifica-
tions to it. Firstly, we changed the database encoding to enable the LLM to understand the dataset
more easily. Secondly, we added additional instructions to elicit reasoning since in our early study
we found that the model was often not generating any reasoning trace with the OmniSQL prompt.
Verifiable Reward.We define a simple reward for use in both TAO and RLVR training. We take
the 0-1 BIRD execution metric and add a penalty of -1 if the model generates a syntactically incorrect
SQL code. This simple metric captures the desired evaluation metric up to an added penalty. Our
preliminary investigation using reward shaping did not yield any significant improvements.
TAO Training.We first perform TAO training which is an offline RL approach pioneered at
Databricks [2]. The goal is to warm start the model for RLVR training by providing it with a good
inductive bias. In a single iteration of TAO, we first generate several responses using the current
model for every BIRD training datapoint. We then compute a reward for each response using the
above verifiable reward. Finally, we perform TAO optimization which performs offline RL on the
collected dataset. This entire procedure can be repeated multiple times.
RLVR Training.We finally perform online RL with verifiable rewards (RLVR) on top of the best
TAO-ed model using our Databricks fine-tuning service. We swept through a variety of hyperparame-
ters and noticed that in general the use of lower learning rate and a lower KL-divergence coefficient
was desirable. In fact, completely removing the KL divergence term in RLVR did not significantly
hurt the performance echoing recent findings in the literature [32]. Our RLVR fine-tuning service per-
forms several improvements on top of known state-of-the-art RLVR approaches such as GRPO [35].
These improvements address various efficiency concerns such as ensuring the training focuses on
challenging problems and to avoid reward saturation.
4 Empirical Results and Discussion
We first present results without test-time compute and then with it.
4.1 Results without test-time compute
Table 1 shows the top models on the BIRD leaderboard that do not use self-consistency. 2 For
clarity, in all the tables below we refer to our full model—Qwen2.5-32B-Coder-Instruct fine-tuned
with TAO and RLVR—as “Databricks-RLVR-32B”. We also report results with the base model
(“Qwen2.5-32B”) and a TAO-only variant (“Qwen2.5-32B + TAO”) for comparison purposes.
Our model achieves the best test set performance in this single-call setting. Accuracy follows BIRD’s
exact-match execution metric.Although our model also had the highest dev set performance, it
generalizes well to the test set (70.80% vs. 73.56%), showing stronger generalization than other top
submissions.
We also noticed that performing limited TAO training already gets us a non-trivial improvement of
67.40%, which at the time of writing would have placed it in the top 10 on the leaderboard by dev
set performance. We only used limited TAO training since our preliminary experiments showed that
over-training led to less overall gains in the later online RL stage.
4.2 Results with test-time compute (self-consistency)
Table 2 shows the results with self-consistency. We generate 7 responses from Databricks-RLVR-32B
and use a parameter-free weighted majority vote based approach to pick the best response. We
achieve state-of-the-art results in the BIRD single-model category by using self-consistency on top
of our Databricks-RLVR-32B model. In fact we do so while requiring fewer LLM calls (7) than
the next best submission (8–32).
Finally, it’s worth stressing that benefits of RLVR and self-consistency are complimentary as demon-
strated.
2We directly use results from the leaderboard and all leaderboard results are current as of September 15th,
2025.
4

Accuracy (exact-match)
Model Dev set Test set
Databricks-RLVR-32B 70.80 73.56
Qwen2.5-32B-Coder-Instruct + TAO 67.40 –
Qwen2.5-32B-Coder-Instruct 64.80 –
Arctic-Text2SQL-R1-32B [46] 70.47 71.83
Arctic-ExCoT-70B [47] 68.51 68.53
Command A [5] 63.49 65.68
OneSQL-v0.1-Qwen-32B3 64.60 63.33
SuperSQL [17] 58.50 62.66
SFT CodeS-15B [19] 58.47 60.37
Table 1: Results on the BIRD benchmark in the single-model, single-call category (i.e., no self-
consistency). Accuracy is reported as exact-match execution accuracy on the dev and test sets. A
dash (“–”) indicates results not computed. Our full method (“Databricks-RLVR-32B”) achieves
the best test accuracy, while TAO alone (“Qwen2.5-32B-Coder-Instruct + TAO”) already reaches a
competitive 67.4%—roughly top-10 at the time of writing.
Accuracy (exact-match) Num.
Model Dev set Test set responses
Databricks-RLVR-32B – 75.68 7
Sophon-Text2SQL-32B 72.43 74.79 8–32
Arctic-Text2SQL-R1-32B [46] 72.20 73.84 1–7
Arctic-Text2SQL-R1-14B [46] 71.40 72.22 1–7
SIFT-32B 70.08 70.93 >32
CrazyData-Text2SQL-32B - 70.71 8–32
Infly-RL-SQL-32B 70.08 70.60 1–7
Arctic-Text2SQL-R1-7B [46] 70.70 70.43 1–7
XiYanSQL-QwenCoder-32B [23] 67.01 69.03 1–7
Table 2: Results on the BIRD benchmark in the single-model category with self-consistency. Accuracy
is reported as exact-match execution accuracy on the dev and test sets; “–” indicates results not
computed. The “Num. responses“ column denotes the number of LLM generations used for self-
consistency. The BIRD leaderboard bins this value into three categories: “few” (1–7), “many” (8–32),
and “scale” (> 32). Our method (“Databricks-RLVR-32B”) achieves the best test accuracy (75.68%)
while requiring only 7 responses, compared to 8–32 for the next best system.
We provide sample generations in the Appendix.
5 Related work
Reinforcement learning and reasoning models.Recent work has increasingly explored using
reinforcement learning to train models that perform multi-step reasoning, rather than relying solely
on test-time computation [38]. Common approaches use algorithms such as PPO [33] or GRPO [35].
Reinforcement learning was popularized in domains like games [ 27, 36, 37, 40], protein folding
[34, 14], and code generation [3, 16, 22, 21, 6]. In the LLM setting, Reinforcement Learning from
Human Feedback (RLHF) typically uses a reward model trained from human preference data, whereas
RLVR replaces human preferences with verifiable signals from the environment—such as whether
generated SQL produces the correct answer. Prior work in this area [ 24, 46] has applied RL to
text-to-SQL and related code generation tasks. In contrast, we use a straightforward reward definition
5

and combine offline and online RL strategies to fine-tune a single model, achieving state-of-the-art
performance on BIRD.
Text-to-SQL.Early text-to-SQL systems were largely rule-based, relying on hand-written gram-
mars and schema-specific heuristics. The introduction of large language models has moved the field
toward training models that candirectlytranslate natural language questions into SQL queries,without
relying on manual rules. Many recent systems follow anagentic design, combining a (fine-tuned)
base model with components for schema linking (e.g., value retrieval), self-reflection, orchestration,
and tightly engineered prompts (see, e.g., [23, 31]). Many prior works also put considerable effort
into carefully curating large fine-tuning datasets; in contrast, we use a relatively small and simple
dataset, relying on reinforcement learning to do most of the heavy lifting. Our main contribution is to
show that reinforcement learning, even with this minimal setup, can deliver state-of-the-art results for
text-to-SQL. A few recent papers have taken a similar reinforcement learning-based direction for
text-to-SQL [24, 46], and our work builds on this trend.
Real-world enterprise applications of text-to-SQL.Natural language interfaces to structured data
have been deployed in a variety of settings. Early examples include Microsoft Power BI’s Q&A and
ThoughtSpot, which relied on symbolic techniques such as pattern matching and rule-based parsing.
More recently, LLM-based systems have been integrated into general-purpose copilots (e.g., GitHub
Copilot [10], OpenAI’s Code Interpreter [28] and reasoning models such as o1/o3 [29, 30]) as well as
tools for data analysis (e.g., Databricks’ Genie [43] and Snowflake’s Cortex Analyst [39]). The range
of deployed systems is too broad to cover in full, but these examples illustrate the growing utility
of text-to-SQL in both developer and analyst workflows. Our results on BIRD suggest that even a
single-model system, trained with a simple reinforcement learning setup, can reach state-of-the-art
performance, making this approach a promising candidate for practical deployment.
6 Conclusion
In this report, we showed the power of Databricks RLVR and TAO fine-tuning services. We show that
our approach when applied to BIRD – a popular data science benchmark led to a new state-of-the-art
performance with our first submission. The approach here is very general-purpose and can be applied
to many other enterprise domains including in data science, coding, and business intelligence tasks.
Our approach will be rolling in our new Agent Bricks product [25] and will be available to Databricks
customers.
References
[1] Lakshya A Agrawal, Shangyin Tan, Dilara Soylu, Noah Ziems, Rishi Khare, Krista Opsahl-Ong,
Arnav Singhvi, Herumb Shandilya, Michael J Ryan, Meng Jiang, et al. Gepa: Reflective prompt
evolution can outperform reinforcement learning.arXiv preprint arXiv:2507.19457, 2025.
[2] Raj Ammanabrolu, Ashutosh Baheti, Jonathan Chang, Xing Chen, Ta-Chung Chi,
Brian Chu, Brandon Cui, Erich Elsen, Jonathan Frankle, Ali Ghodsi, Pallavi Kop-
pol, Sean Kulinski, Jonathan Li, Dipendra Misra, Jose Javier Gonzalez Ortiz, Sean
Owen, Mihir Patel Patel, Mansheej Paul, Cory Stephenson, Alex Trott, Ziyi Yang,
Matei Zaharia, Andy Zhang, and Ivan Zhou. Tao: Using test-time compute to
train efficient llms without labeled data. https://www.databricks.com/blog/
tao-using-test-time-compute-train-efficient-llms-without-labeled-data .
Accessed: Aug-11-2025.
[3] Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde de Oliveira Pinto,
Jared Kaplan, Harri Edwards, Yuri Burda, Nicholas Joseph, Greg Brockman, Alex Ray, Raul
Puri, Gretchen Krueger, Michael Petrov, Heidy Khlaaf, Girish Sastry, Pamela Mishkin, Brooke
Chan, Scott Gray, Nick Ryder, Mikhail Pavlov, Barnabas Power, Christina Kaiser, Mohammad
Bavarian, Clemens Winter, Phil Tillet, Felipe Petroski Such, Daniel Cummings, Matthias
Plappert, Fotios Chantzis, Elizabeth Barnes, Ariel Herbert-V oss, William H. Guss, Alex Nichol,
Igor Paino, Nikolas Tezak, Jie Tang, Igor Babuschkin, S. Balaji, S. Jain, William Saunders,
Christopher Hesse, Andrew Carr, Jan Leike, Joshua Achiam, Vedant Misra, E. Morikawa, Alec
Radford, M. Knight, Miles Brundage, Mira Murati, Kathleen Mayer, Peter Welinder, Bob
6

McGrew, Dario Amodei, Ilya Sutskever, and Wojciech Zaremba. Evaluating large language
models trained on code.arXiv preprint arXiv:2107.03374, 2021.
[4] Paul F Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei.
Deep reinforcement learning from human preferences. In I. Guyon, U. V on Luxburg, S. Ben-
gio, H. Wallach, R. Fergus, S. Vishwanathan, and R. Garnett, editors,Advances in Neural
Information Processing Systems, volume 30. Curran Associates, Inc., 2017.
[5] Team Cohere, Arash Ahmadian, Marwan Ahmed, Jay Alammar, Milad Alizadeh, Yazeed
Alnumay, Sophia Althammer, Arkady Arkhangorodsky, Viraat Aryabumi, Dennis Aumiller,
et al. Command a: An enterprise-ready large language model.arXiv preprint arXiv:2504.00698,
2025.
[6] Shihan Dou, Yan Liu, Haoxiang Jia, Enyu Zhou, Limao Xiong, Junjie Shan, Caishuang Huang,
Xiao Wang, Xiaoran Fan, Zhiheng Xi, Yuhao Zhou, Tao Ji, Rui Zheng, Qi Zhang, Tao Gui, and
Xuanjing Huang. StepCoder: Improving code generation with reinforcement learning from
compiler feedback. In Lun-Wei Ku, Andre Martins, and Vivek Srikumar, editors,Proceedings
of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long
Papers), pages 4571–4585, Bangkok, Thailand, August 2024. Association for Computational
Linguistics.
[7] Catherine Finegan-Dollak, Jonathan K. Kummerfeld, Li Zhang, Karthik Ramanathan, Sesh
Sadasivam, Rui Zhang, and Dragomir Radev. Improving text-to-SQL evaluation methodology.
In Iryna Gurevych and Yusuke Miyao, editors,Proceedings of the 56th Annual Meeting of the
Association for Computational Linguistics (Volume 1: Long Papers), pages 351–360, Melbourne,
Australia, July 2018. Association for Computational Linguistics.
[8] Allen Institute for AI. Tülu 3 technical report. https://allenai.org/blog/
tulu-3-technical, November 2024. Accessed: 2025-08-18.
[9] Isa Fulford, Zhiqing Sun, et al. Openai: Introducing deep research. https://openai.com/
index/introducing-deep-research/. Accessed: August 4, 2025.
[10] GitHub. Introducing github copilot: your ai pair program-
mer. https://github.blog/news-insights/product-news/
introducing-github-copilot-ai-pair-programmer/ , Jun 2021. Accessed: 2025-08-
15.
[11] Sirui Hong, Yizhang Lin, Bang Liu, Bangbang Liu, Binhao Wu, Ceyao Zhang, Chenxing Wei,
Danyang Li, Jiaqi Chen, Jiayi Zhang, et al. Data interpreter: An llm agent for data science.
arXiv preprint arXiv:2402.18679, 2024.
[12] Jingcheng Hu, Yinmin Zhang, Qi Han, Daxin Jiang, Xiangyu Zhang, and Heung-Yeung Shum.
Open-reasoner-zero: An open source approach to scaling up reinforcement learning on the base
model.arXiv preprint arXiv:2503.24290, 2025.
[13] Wonseok Hwang, Jinyeong Yim, Seunghyun Park, and Minjoon Seo. A comprehensive explo-
ration on wikisql with table-aware word contextualization.arXiv preprint arXiv:1902.01069,
2019.
[14] John Jumper, Richard Evans, Alexander Pritzel, Tim Green, Michael Figurnov, Olaf Ron-
neberger, Kathryn Tunyasuvunakool, Russ Bates, Augustin Žídek, Anna Potapenko, Alex
Bridgland, Anna A. Meyer, Simon A. A. Kohl, Andrew J. Ballard, Andrew Cowie, Bernardino
Romera-Paredes, Stanislav Nikolov, Rishub Jain, Jonas Adler, Trevor Back, Stig Petersen,
David Reiman, Ellen Clancy, Michal Zielinski, Martin Steinegger, Michalina Pacholska, Tamas
Berghammer, Sebastian Bodenstein, Dylan Silver, Oriol Vinyals, Andrew W. Senior, Koray
Kavukcuoglu, Pushmeet Kohli, and Demis Hassabis. Highly accurate protein structure predic-
tion with alphafold.Nature, 596:583–589, 2021.
[15] Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri
Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T Joshi, Hanna Moazam, et al. Dspy:
Compiling declarative language model calls into self-improving pipelines.arXiv preprint
arXiv:2310.03714, 2023.
7

[16] Hung Le, Yue Wang, Akhilesh Deepak Gotmare, Silvio Savarese, and Steven Hoi. CodeRL:
Mastering code generation through pretrained models and deep reinforcement learning. In
Alice H. Oh, Alekh Agarwal, Danielle Belgrave, and Kyunghyun Cho, editors,Advances in
Neural Information Processing Systems, 2022.
[17] Boyan Li, Yuyu Luo, Chengliang Chai, Guoliang Li, and Nan Tang. The dawn of natural
language to sql: Are we fully ready?arXiv preprint arXiv:2406.01265, 2024.
[18] Haoyang Li, Shang Wu, Xiaokang Zhang, Xinmei Huang, Jing Zhang, Fuxin Jiang, Shuai Wang,
Tieying Zhang, Jianjun Chen, Rui Shi, et al. Omnisql: Synthesizing high-quality text-to-sql
data at scale.arXiv preprint arXiv:2503.02240, 2025.
[19] Haoyang Li, Jing Zhang, Hanbing Liu, Ju Fan, Xiaokang Zhang, Jun Zhu, Renjie Wei, Hongyan
Pan, Cuiping Li, and Hong Chen. Codes: Towards building open-source language models for
text-to-sql.Proceedings of the ACM on Management of Data, 2(3):1–28, 2024.
[20] Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, Bailin Wang, Bowen Qin,
Ruiying Geng, Nan Huo, et al. Can llm already serve as a database interface? a big bench for
large-scale database grounded text-to-sqls.Advances in Neural Information Processing Systems,
36:42330–42357, 2023.
[21] Yujia Li, David Choi, Samuel K Ainsworth, Sebastian Borgeaud, Geoffrey Irving, Camilo Ruiz,
Trevor Cai, Dylan Banarse, Wojciech Stokowiec, Aidan Clark, et al. Competition-level code
generation with alphacode 2.arXiv preprint arXiv:2310.16470, 2023.
[22] Yujia Li, David Choi, Junyoung Chung, Nate Kushman, Julian Schrittwieser, Rémi Leblond,
Tom Eccles, James Keeling, Felix Gimeno, Theophane Weber, Hamza Merzic, Timo Ewalds,
James Lishman, David Budden, Aliaksei Severyn, Misha Pavlov, Diego de Las Casas, Aidan
Guy, Chris Jones, James Bradbury, Matthew Johnson, Saran Tunyasuvunakool, Pushmeet Kohli,
Demis Hassabis, Koray Kavukcuoglu, and Oriol Vinyals. Competition-level code generation
with alphacode.Science, 378(6624):1092–1097, 2022.
[23] Yifu Liu, Yin Zhu, Yingqi Gao, Zhiling Luo, Xiaoxia Li, Xiaorong Shi, Yuntao Hong, Jinyang
Gao, Yu Li, Bolin Ding, et al. Xiyan-sql: A novel multi-generator framework for text-to-sql.
arXiv preprint arXiv:2507.04701, 2025.
[24] Peixian Ma, Xialie Zhuang, Chengjin Xu, Xuhui Jiang, Ran Chen, and Jian Guo. Sql-r1:
Training natural language to sql reasoning model by reinforcement learning, 2025.
[25] Xiangrui Meng, Kasey Uhlenhuth, Hanlin Tang, Patrick Wendell, and Matei Zaharia. Introduc-
ing agent bricks: Auto-optimized agents using your data. https://www.databricks.com/
blog/introducing-agent-bricks. Accessed: Aug-12-2025.
[26] Dipendra Misra, Ming-Wei Chang, Xiaodong He, and Wen-tau Yih. Policy shaping and
generalized update equations for semantic parsing from denotations. In Ellen Riloff, David
Chiang, Julia Hockenmaier, and Jun’ichi Tsujii, editors,Proceedings of the 2018 Conference
on Empirical Methods in Natural Language Processing, pages 2442–2452, Brussels, Belgium,
October-November 2018. Association for Computational Linguistics.
[27] V olodymyr Mnih, Koray Kavukcuoglu, David Silver, Andrei A. Rusu, Joel Veness, Marc G.
Bellemare, Alex Graves, Martin Riedmiller, Andreas K. Fidjeland, Georg Ostrovski, Stig Pe-
tersen, Charles Beattie, Amir Sadik, Ioannis Antonoglou, Helen King, Dharshan Kumaran, Daan
Wierstra, Shane Legg, and Demis Hassabis. Human-level control through deep reinforcement
learning.Nature, 518(7540):529–533, 2015.
[28] OpenAI. Chatgpt plugins. https://openai.com/index/chatgpt-plugins/, Mar 2023.
Introduces browsing, retrieval, and code interpreter plugins. Accessed: 2025-08-15.
[29] OpenAI. Openai o1 system card, 2024.
[30] OpenAI. Openai o3 and o4-mini system card. https://openai.com/index/
o3-o4-mini-system-card/, Apr 2025. Accessed: 2025-08-15.
8

[31] Mohammadreza Pourreza, Hailong Li, Ruoxi Sun, Yeounoh Chung, Shayan Talaei, Gaurav Tar-
lok Kakkar, Yu Gan, Amin Saberi, Fatma Ozcan, and Sercan O. Arik. Chase-sql: Multi-path
reasoning and preference optimized candidate selection in text-to-sql. InThe Thirteenth Inter-
national Conference on Learning Representations, 2025.
[32] Abhinav Rastogi, Albert Q. Jiang, Andy Lo, Gabrielle Berrada, Guillaume Lample, Jason Rute,
Joep Barmentlo, Karmesh Yadav, Kartik Khandelwal, Khyathi Raghavi Chandu, Léonard Blier,
Lucile Saulnier, Matthieu Dinot, Maxime Darrin, Neha Gupta, Roman Soletskyi, Sagar Vaze,
Teven Le Scao, Yihan Wang, Adam Yang, Alexander H. Liu, Alexandre Sablayrolles, Amélie
Héliou, Amélie Martin, Andy Ehrenberg, Anmol Agarwal, Antoine Roux, Arthur Darcet, Arthur
Mensch, Baptiste Bout, Baptiste Rozière, Baudouin De Monicault, Chris Bamford, Christian
Wallenwein, Christophe Renaudin, Clémence Lanfranchi, Darius Dabert, Devon Mizelle, Diego
de las Casas, Elliot Chane-Sane, Emilien Fugier, Emma Bou Hanna, Gauthier Delerce, Gauthier
Guinet, Georgii Novikov, Guillaume Martin, Himanshu Jaju, Jan Ludziejewski, Jean-Hadrien
Chabran, Jean-Malo Delignon, Joachim Studnia, Jonas Amar, Josselin Somerville Roberts,
Julien Denize, Karan Saxena, Kush Jain, Lingxiao Zhao, Louis Martin, Luyu Gao, Lélio Renard
Lavaud, Marie Pellat, Mathilde Guillaumin, Mathis Felardos, Maximilian Augustin, Mickaël
Seznec, Nikhil Raghuraman, Olivier Duchenne, Patricia Wang, Patrick von Platen, Patryk Saffer,
Paul Jacob, Paul Wambergue, Paula Kurylowicz, Pavankumar Reddy Muddireddy, Philomène
Chagniot, Pierre Stock, Pravesh Agrawal, Romain Sauvestre, Rémi Delacourt, Sanchit Gandhi,
Sandeep Subramanian, Shashwat Dalal, Siddharth Gandhi, Soham Ghosh, Srijan Mishra,
Sumukh Aithal, Szymon Antoniak, Thibault Schueller, Thibaut Lavril, Thomas Robert, Thomas
Wang, Timothée Lacroix, Valeriia Nemychnikova, Victor Paltz, Virgile Richard, Wen-Ding Li,
William Marshall, Xuanyu Zhang, and Yunhao Tang. Magistral, 2025.
[33] John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. Proximal
policy optimization algorithms, 2017.
[34] Andrew W. Senior, Richard Evans, John Jumper, James Kirkpatrick, Laurent Sifre, Tim Green,
Chloe Qin, Augustin Zıdek, Alexander W. R. Nelson, Alex Bridgland, Helena Penedones, Stig
Petersen, Karen Simonyan, Steve Crossan, Pushmeet Kohli, David T. Jones, David Silver, Koray
Kavukcuoglu, and Demis Hassabis. Improved protein structure prediction using potentials from
deep learning.Nature, 577:706–710, 2020.
[35] Zhihong Shao, Peiyi Wang, Qihao Zhu, Runxin Xu, Junxiao Song, Mingchuan Zhang, Y .K. Li,
Y . Wu, and Daya Guo. Deepseekmath: Pushing the limits of mathematical reasoning in open
language models, 2024.
[36] David Silver, Aja Huang, Chris J Maddison, Arthur Guez, Laurent Sifre, George Van Den Driess-
che, Julian Schrittwieser, Ioannis Antonoglou, Veda Panneershelvam, Marc Lanctot, et al. Mas-
tering the game of go with deep neural networks and tree search.nature, 529(7587):484–489,
2016.
[37] David Silver, Julian Schrittwieser, Karen Simonyan, Ioannis Antonoglou, Aja Huang, Arthur
Guez, Thomas Hubert, Lucas Baker, Matthew Lai, Adrian Bolton, et al. Mastering the game of
go without human knowledge.nature, 550(7676):354–359, 2017.
[38] Charlie Victor Snell, Jaehoon Lee, Kelvin Xu, and Aviral Kumar. Scaling LLM test-time com-
pute optimally can be more effective than scaling parameters for reasoning. InThe Thirteenth
International Conference on Learning Representations, 2025.
[39] Snowflake. Cortex analyst: Paving the way to self-service analytics. https://
www.snowflake.com/en/blog/cortex-analyst-ai-self-service-analytics/ , Aug
2024. Accessed: 2025-08-15.
[40] Oriol Vinyals, Igor Babuschkin, Wojciech M Czarnecki, Michaël Mathieu, Andrew Dudzik, Jun-
young Chung, David H Choi, Richard Powell, Timo Ewalds, Petko Georgiev, et al. Grandmaster
level in starcraft ii using multi-agent reinforcement learning.nature, 575(7782):350–354, 2019.
[41] Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang, Aakanksha
Chowdhery, and Denny Zhou. Self-consistency improves chain of thought reasoning in language
models.arXiv preprint arXiv:2203.11171, 2022.
9

[42] Xumeng Wen, Zihan Liu, Shun Zheng, Zhijian Xu, Shengyu Ye, Zhirong Wu, Xiao Liang,
Yang Wang, Junjie Li, Ziming Miao, Jiang Bian, and Mao Yang. Reinforcement learning
with verifiable rewards implicitly incentivizes correct reasoning in base llms.arXiv preprint
arXiv:2506.14245, June 2025. Submitted June 17, 2025.
[43] Wong, Ken and Hormati, Amir and Tomlinson, Richard. Ai/bi genie now generally avail-
able. https://www.databricks.com/blog/aibi-genie-now-generally-available ,
Aug 2025. Accessed: 2025-08-15.
[44] An Yang, Anfeng Li, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng, Bowen Yu,
Chang Gao, Chengen Huang, Chenxu Lv, et al. Qwen3 technical report.arXiv preprint
arXiv:2505.09388, 2025.
[45] John Yang, Carlos E Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik
Narasimhan, and Ofir Press. Swe-agent: Agent-computer interfaces enable automated software
engineering.Advances in Neural Information Processing Systems, 37:50528–50652, 2024.
[46] Zhewei Yao, Guoheng Sun, Lukasz Borchmann, Zheyu Shen, Minghang Deng, Bohan Zhai,
Hao Zhang, Ang Li, and Yuxiong He. Arctic-text2sql-r1: Simple rewards, strong reasoning in
text-to-sql, 2025.
[47] Bohan Zhai, Canwen Xu, Yuxiong He, and Zhewei Yao. Optimizing reasoning for text-to-SQL
with execution feedback. InFindings of the Association for Computational Linguistics: ACL
2025, 2025.
[48] Kun Zhou, Yutao Zhu, Zhipeng Chen, Wentong Chen, Wayne Xin Zhao, Xu Chen, Yankai Lin,
Ji-Rong Wen, and Jiawei Han. Don’t make your llm an evaluation benchmark cheater.arXiv
preprint arXiv:2311.01964, 2023.
10

7 Appendix
7.1 Contributing authors
The following members of the Databricks Mosaic Research and Genie teams contributed to this work
(listed alphabetically):
Alnur Ali, Ashutosh Baheti, Jonathan Chang, Ta-Chung Chi, Brandon Cui, Andrew Drozdov, Jonathan
Frankle, Abhay Gupta, Pallavi Koppol, Sean Kulinski, Jonathan Li, Dipendra Misra, Krista Opsahl-
Ong, Jose Javier Gonzalez Ortiz, Matei Zaharia, and Yue Zhang.
7.2 Sample model generations
We list some successful examples below. The first successful example is fairly easy. The second one
performs a table join and also shows model correcting a generation.
Example 1 (Success)
Question:“What is the highest eligible free rate for K-12 students in the schools in Alameda
County?"
Evidence:“Eligible free rate for K-12 = ‘Free Meal Count (K-12)‘ / ‘Enrollment (K-12)‘"
Database:california_schools
Response:To determine the highest eligible free rate for K-12 students in the schools in
Alameda County, we need to follow these steps:
1. Identify the relevant table and columns. In this case, the ‘frpm‘ table contains
the necessary information about the free meal counts and enrollments for K-12 students.
2. Filter the data to include only schools in Alameda County.
3. Calculate the eligible free rate for each school using the formula: ‘Free Meal Count
(K-12)‘ / ‘Enrollment (K-12)‘.
4. Find the maximum value of the calculated eligible free rate.
Let´s translate these steps into an SQL query:
```sql
SELECT MAX("Free Meal Count (K-12)" / "Enrollment (K-12)") AS MaxEligibleFreeRate
FROM frpm
WHERE "County Name" = Álameda´;
```
This query will return the highest eligible free rate for K-12 students in the schools
in Alameda County.
Example 2 (Success)
Question:“Among the superheroes with the race of god/eternal, how many of them are
male"
Evidence:“race "god/eternal" refers to race_id = 21; male refers to gender.id = 1"
Database:superhero
Response:To solve this problem, we need to follow these steps:
1. Identify the table that contains the superhero information, including their race and gender.
In this case, it’s the ‘superhero‘ table.
2. Determine the tables that contain the race and gender information. Here, the ‘race‘ table
contains the race information, and the ‘gender‘ table contains the gender information.
11

3. Join the ‘superhero‘ table with the ‘race‘ table on the ‘race_id‘ to filter superheroes with
the race "god/eternal".
4. Join the ‘superhero‘ table with the ‘gender‘ table on the ‘gender_id‘ to filter superheroes
who are male.
5. Count the number of superheroes that meet both conditions (race "god/eternal" and gender
male).
Let’s translate these steps into an SQL query:
```sql
SELECT COUNT(*)
FROM superhero AS h
JOIN race AS r ON h.race_id = r.id
JOIN gender AS g ON h.gender_id = g.id
WHERE r.race = “God/Eternal" AND g.gender = “Male";
```
However, the question specifies that "race ’god/eternal’" refers to ‘race_id = 21‘. We can use
this information directly in the WHERE clause to avoid joining the ‘race‘ table. Here is the
optimized query:
```sql
SELECT COUNT(*)
FROM superhero AS h
JOIN gender AS g ON h.gender_id = g.id
WHERE h.race_id = 21 AND g.gender = ’Male’;
```
This query will give us the count of male superheroes with the race "god/eternal".
We also list an unsuccessful example below. In this case, the model makes two mistakes. It uses type
of foreign_data table instead of the card’s table which has different value even though the names are
confusing. Second, it forgot to apply distinct to the returned values.
Example 3 (Failure)
Question:“What’s the German type of the card ‘Ancestor’s Chosen’?"
Evidence:“German refers to language = ’German’; "Ancestor’s Chosen" refers to name =
’Ancestor’s Chosen’"
Database:card_games
Response:To determine the German type of the card "Ancestor’s Chosen", we need to join
the ‘cards‘ table with the ‘foreign_data‘ table. The ‘cards‘ table contains the English name of
the card, and the ‘foreign_data‘ table contains the translated types in different languages. We
will filter the results to only include the card with the name "Ancestor’s Chosen" and the
language set to ’German’.
Here are the steps to construct the SQL query:
1. Identify the table that contains the card names and their corresponding UUIDs (‘cards‘).
2. Identify the table that contains the translated types and their corresponding UUIDs
(‘foreign_data‘).
3. Join the ‘cards‘ table with the ‘foreign_data‘ table on the UUID column.
4. Filter the joined table to only include rows where the card name is "Ancestor’s Chosen"
and the language is ’German’.
5. Select the ‘type‘ column from the ‘foreign_data‘ table.
12

Let’s translate these steps into an SQL query:
```sql
SELECT fd.type
FROM cards c
JOIN foreign_data fd ON c.uuid = fd.uuid
WHERE c.name = “Ancestor’s Chosen" AND fd.language = “German";
```
13