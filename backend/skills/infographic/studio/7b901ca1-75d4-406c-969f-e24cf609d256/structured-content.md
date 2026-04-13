# A State-of-the-Art SQL Reasoning Model using RLVR

## Overview
This infographic presents Databricks Mosaic Research's approach to developing a state-of-the-art SQL reasoning model using Reinforcement Learning with Verifiable Rewards (RLVR), achieving 75.68% accuracy on the BIRD benchmark with self-consistency.

## Learning Objectives
The viewer will understand:
1. How RLVR (Reinforcement Learning with Verifiable Rewards) works for fine-tuning LLMs on text-to-SQL tasks
2. The two-stage training pipeline: offline TAO warm-up followed by online RLVR training
3. The achieved results: 73.56% accuracy without self-consistency and 75.68% with self-consistency on BIRD private test set

---

## Section 1: The Challenge - Enterprise-Specific Knowledge Gaps

**Key Concept**: Off-the-shelf LLMs face limitations in understanding organization-specific terminology, concepts, tools, and APIs.

**Content**:
- "LLMs have become a fixture in a range of enterprise problems including software engineering, data science, and more recently even research itself"
- "Despite sometime impressive performance of off-the-shelf LLMs, they face limitations in doing more bespoke enterprise tasks"
- "Limitations such as unable to understand organization-specific terminology or use organization-specific concepts, tools, and APIs"
- "For example, given a user query 'show me all churned users for 2024?', the model may not know how the organization defines 'churned users'"
- "Or, the model may not be aware of certain preferences such as always sorting certain queries with a given column"
- "Unlike math problems where the training data might be more available on the internet, organizational knowledge might be more protected and less represented on the internet"

**Visual Element**:
- Type: illustration with problem icons
- Subject: LLM struggling with enterprise-specific concepts (jargon, APIs, data locations)
- Treatment: Hand-drawn style showing gap between generic LLM knowledge and organization-specific needs

**Text Labels**:
- Headline: "The Enterprise Knowledge Gap"
- Subhead: "Why Off-the-Shelf LLMs Struggle"
- Labels: "Organization-Specific Terminology", "Custom Tools & APIs", "Protected Data Sources", "Industry Jargon"

---

## Section 2: The Solution - RLVR Framework

**Key Concept**: RLVR is a post-training paradigm that applies reinforcement learning to fine-tune LLMs using verifiable rewards without needing parametrized reward models.

**Content**:
- "RLVR is a post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models"
- "RLVR is particularly suited to tasks where the LLM is trying to predict facts, mathematical statements, or generating executable code, as its responses can be measured objectively given access to ground truth"
- "This contrasts with non-verifiable tasks that typically measure subjective tasks such as generating poetry, or an essay on a given topic"
- "For the task in Figure 1, we can measure if a given AI agent's SQL response is correct by matching it against the ground truth SQL response for that user query"

**Visual Element**:
- Type: conceptual diagram
- Subject: RLVR framework showing verifiable reward mechanism
- Treatment: Clean hand-drawn flow showing query → SQL generation → execution → comparison → reward

**Text Labels**:
- Headline: "Reinforcement Learning with Verifiable Rewards (RLVR)"
- Subhead: "Objective Quality Metrics Without Reward Models"
- Labels: "Verifiable Reward", "Ground Truth", "Objective Measurement"

---

## Section 3: The Text2SQL Task

**Key Concept**: Text2SQL requires understanding user queries in the context of complex database structures to generate correct SQL code.

**Content**:
- "In this task, a user asks a natural language query x∈ X to access a database d∈ D"
- "An agent then generates a SQL code y∈ Y which is executed on the database and its output is returned to the user"
- "The goal of the agent is to generate a SQL code that best captures the intent of the user query"
- "The main challenge in text2sql is that it requires understanding the query in the context of the database which can be quite complex"
- "For example, the database may have many tables with many columns, column names can be ambiguous, correct column values may need to be found and tables may need to be joined to answer the user query"

**Visual Element**:
- Type: task flow diagram
- Subject: User query → database context → SQL generation → execution → result
- Treatment: Hand-drawn database schema with tables, columns, and query flow

**Text Labels**:
- Headline: "The Text2SQL Challenge"
- Subhead: "From Natural Language to Executable SQL"
- Labels: "User Query", "Database Schema", "SQL Code", "Execution Result"

---

## Section 4: The Two-Stage Training Pipeline

**Key Concept**: The approach uses a two-stage fine-tuning process: TAO offline RL warm-up followed by online RLVR training.

**Content**:
- "Our approach starts by carefully selecting the model, context, and prompt"
- "The prompt can be chosen using prompt optimization approaches such as GEPA"
- "We then perform a two-stage fine-tuning of the model with the chosen context and prompt"
- "First, we warm start the model using Test-time Adaptive Optimization (TAO), an offline RL approach"
- "This is followed by fine-tuning the model using Databricks's RLVR service"
- "Our RLVR service supports popular learning approaches such as GRPO, as well as more powerful alternatives"
- "Finally, we perform self-consistency on top of the fine-tuned model at inference time"

**Visual Element**:
- Type: pipeline diagram (based on Figure 1)
- Subject: Two-stage pipeline showing TAO → RLVR → self-consistency flow
- Treatment: Hand-drawn pipeline with clear stage separation, showing reward computation and model updates

**Text Labels**:
- Headline: "Two-Stage Training Pipeline"
- Stage 1: "Offline TAO Warm-Up"
- Stage 2: "Online RLVR Training"
- Final: "Self-Consistency Inference"
- Labels: "Model Selection", "Prompt Optimization", "TAO Optimization", "RLVR Optimization", "Verifiable Reward (VR)"

---

## Section 5: The BIRD Benchmark

**Key Concept**: BIRD is a popular text2sql benchmark used to evaluate the model's ability to convert natural language queries to SQL executions.

**Content**:
- "We apply RLVR to a popular data science benchmark called BIRD that measures the ability of an AI agent to convert natural language query for a database to SQL executions"
- "A BIRD datapoint includes a user query, an evidence field providing additional instruction, a database containing multiple tables, and a gold SQL code denoting ground truth"
- "The BIRD dataset consists of a train set of 9,428 examples, a dev set of 1,534 examples, and a test set of 1,789 examples"
- "The test set is not publicly available allowing evaluation without dataset contamination concerns and prevents benchmark hacking"
- "The evaluation metric for BIRD is a strict 0-1 metric where given the generated SQL code, we execute both the gold SQL and the generated SQL code on the database and check if their outputs match (1) or not (0)"
- "We train the model using the train set and use the dev set performance for model and hyperparameter selection"
- "We do not use any additional training data"

**Visual Element**:
- Type: dataset breakdown visualization
- Subject: BIRD dataset composition (train/dev/test splits)
- Treatment: Hand-drawn bars or modules showing dataset sizes and evaluation metric

**Text Labels**:
- Headline: "BIRD Benchmark"
- Subhead: "Text2SQL Evaluation Dataset"
- Labels: "Train Set: 9,428 examples", "Dev Set: 1,534 examples", "Test Set: 1,789 examples", "Strict 0-1 Metric"

---

## Section 6: State-of-the-Art Results

**Key Concept**: The RLVR-trained model achieved state-of-the-art accuracy on the BIRD private test set with fewer generations than competing approaches.

**Content**:
- "With no additional training data beyond the BIRD training set and no use of proprietary models, our very first submission to the BIRD leaderboard reached state-of-the-art accuracy on the private test set: 73.56% without self-consistency and 75.68% with self-consistency"
- "In the latter case, our model also required fewer generations than the second-best approach"
- "Our RLVR-trained model already achieves state-of-the-art in single-model single-LLM call category"
- "Whereas self-consistency adds complimentary benefits and gives us the overall best single-model performance"
- "Further, our model generalizes better than other top-submissions and achieves state-of-the-art using fewer self-consistency responses than the second best result"

**Visual Element**:
- Type: results highlight with comparison chart (based on Figure 2)
- Subject: Accuracy metrics showing 73.56% and 75.68% with comparison to other models
- Treatment: Hand-drawn bar chart or number highlights emphasizing the SOTA results

**Text Labels**:
- Headline: "State-of-the-Art Results"
- Primary Metric: "75.68% with Self-Consistency"
- Secondary Metric: "73.56% without Self-Consistency"
- Labels: "Single-Model SOTA", "Fewer Generations", "Better Generalization", "First Submission"

---

## Section 7: Broader Applications

**Key Concept**: The simplicity of the RLVR framework makes it broadly applicable to enterprise domains beyond the BIRD proxy task.

**Content**:
- "While BIRD is only a proxy task, the simplicity of our framework makes it broadly applicable to enterprise domains such as business intelligence, data science, and coding"
- "Developing custom reasoning models via Reinforcement Learning (RL) that can incorporate organization-specific knowledge has great potential to address problems faced by enterprise customers"
- "In many of these problems, the reward function is verifiable, a setting termed RL with Verifiable Rewards (RLVR)"

**Visual Element**:
- Type: application icons
- Subject: Enterprise domains (business intelligence, data science, coding)
- Treatment: Hand-drawn icons representing different application areas

**Text Labels**:
- Headline: "Broader Enterprise Applications"
- Labels: "Business Intelligence", "Data Science", "Coding", "Organization-Specific Knowledge"

---

## Data Points (Verbatim)

All statistics, numbers, and quotes exactly as they appear in source:

### Statistics
- "73.56% without self-consistency and 75.68% with self-consistency"
- "BIRD dataset consists of a train set of 9,428 examples, a dev set of 1,534 examples, and a test set of 1,789 examples"
- "our very first submission to the BIRD leaderboard reached state-of-the-art accuracy on the private test set"
- "our model also required fewer generations than the second-best approach"

### Quotes
- "RLVR is a post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models" — Databricks Mosaic Research
- "The evaluation metric for BIRD is a strict 0-1 metric where given the generated SQL code, we execute both the gold SQL and the generated SQL code on the database and check if their outputs match (1) or not (0)" — Databricks Mosaic Research
- "With no additional training data beyond the BIRD training set and no use of proprietary models" — Databricks Mosaic Research

### Key Terms
- **RLVR (Reinforcement Learning with Verifiable Rewards)**: "A post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models"
- **TAO (Test-time Adaptive Optimization)**: "An offline RL approach"
- **Text2SQL**: "A task where a user asks a natural language query to access a database, and an agent generates SQL code which is executed on the database"
- **BIRD Benchmark**: "A popular data science benchmark that measures the ability of an AI agent to convert natural language query for a database to SQL executions"
- **Self-Consistency**: "An inference-time approach that spends more inference compute at test time to improve a model's performance"

---

## Design Instructions

Extracted from user's steering prompt:

### Style Preferences
- Visual Style: craft-handmade (hand-drawn, paper craft aesthetic)
- Detail Level: 标准 (standard)
- Mood: Professional yet approachable, making complex technical content accessible

### Layout Preferences
- Layout: bento-grid (multiple information modules in a balanced grid)
- Aspect: landscape (16:9, 横向)
- Structure: Multiple sections organized in grid modules for overview clarity

### Other Requirements
- Language: 简体中文 (all text content in Simplified Chinese)
- Target Audience: Data scientists, ML engineers, enterprise AI practitioners (Intermediate to Expert level)
- Content Type: Process/technical with supporting evidence
- Preserve all source data verbatim - no summarization or rephrasing of statistics and quotes
