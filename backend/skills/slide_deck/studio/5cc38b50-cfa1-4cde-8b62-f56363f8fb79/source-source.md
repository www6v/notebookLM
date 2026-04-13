# Generated Slides

## Slide Deck Request
- version: v2
- language: 简体中文
- style: blueprint
- audience: general
- slides: 2

## Source Content
[2509.21459v1.pdf]: A State-of-the-Art SQL Reasoning Model using RLVR
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
compute at test time to improve a model’s pe
