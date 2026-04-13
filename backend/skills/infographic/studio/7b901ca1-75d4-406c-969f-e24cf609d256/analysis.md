---
title: "A State-of-the-Art SQL Reasoning Model using RLVR"
topic: "technical"
data_type: "process"
complexity: "complex"
point_count: 12
source_language: "en"
user_language: "zh"
---

## Main Topic
This document presents Databricks Mosaic Research's approach to developing a state-of-the-art SQL reasoning model using Reinforcement Learning with Verifiable Rewards (RLVR), achieving 75.68% accuracy on the BIRD benchmark with self-consistency.

## Learning Objectives
After viewing this infographic, the viewer should understand:
1. How RLVR (Reinforcement Learning with Verifiable Rewards) works for fine-tuning LLMs on text-to-SQL tasks
2. The two-stage training pipeline: offline TAO warm-up followed by online RLVR training
3. The achieved results: 73.56% accuracy without self-consistency and 75.68% with self-consistency on BIRD private test set

## Target Audience
- **Knowledge Level**: Intermediate to Expert (data scientists, ML engineers, enterprise AI practitioners)
- **Context**: Understanding how to apply RLVR for enterprise-specific knowledge integration
- **Expectations**: Learn the practical framework for fine-tuning LLMs on verifiable reward tasks

## Content Type Analysis
- **Data Structure**: Process flow with supporting evidence (benchmark results, methodology comparison)
- **Key Relationships**: TAO offline RL → RLVR online training → self-consistency inference; text2sql task → verifiable reward → model optimization
- **Visual Opportunities**: Pipeline diagram (Figure 1), benchmark comparison chart (Figure 2), accuracy metrics, training stages timeline

## Key Data Points (Verbatim)
- "73.56% without self-consistency and 75.68% with self-consistency"
- "With no additional training data beyond the BIRD training set and no use of proprietary models"
- "BIRD dataset consists of a train set of 9,428 examples, a dev set of 1,534 examples, and a test set of 1,789 examples"
- "our very first submission to the BIRD leaderboard reached state-of-the-art accuracy on the private test set"
- "our model also required fewer generations than the second-best approach"
- "RLVR is a post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models"
- "The evaluation metric for BIRD is a strict 0-1 metric where given the generated SQL code, we execute both the gold SQL and the generated SQL code on the database and check if their outputs match (1) or not (0)"
- "Test-time Adaptive Optimization (TAO), an offline RL approach"
- "Our RLVR service supports popular learning approaches such as GRPO"

## Layout × Style Signals
- Content type: process/technical → suggests `linear-progression` or `structural-breakdown`
- Tone: technical, research-oriented → suggests `technical-schematic` or `craft-handmade`
- Audience: data scientists, ML engineers → suggests clean, professional style
- Complexity: complex (multiple stages, technical concepts) → suggests structured layout with clear sections
- User parameters: layout=`bento-grid`, style=`craft-handmade`, aspect=`landscape`

## Design Instructions (from user input)
- Layout: bento-grid (specified in parameters)
- Style: craft-handmade (specified in parameters)
- Aspect: landscape (横向)
- Language: 简体中文 (content should be in Simplified Chinese)
- Detail level: 标准 (standard)

## Recommended Combinations
1. **bento-grid + craft-handmade** (User Selected): Balanced overview layout with approachable hand-drawn style makes complex technical content more accessible while maintaining clarity across multiple information modules
2. **linear-progression + technical-schematic**: Emphasizes the sequential two-stage training pipeline (TAO → RLVR) with blueprint-style precision for technical audience
3. **structural-breakdown + craft-handmade**: Explodes the RLVR pipeline components showing how verifiable rewards are computed and applied to model optimization
