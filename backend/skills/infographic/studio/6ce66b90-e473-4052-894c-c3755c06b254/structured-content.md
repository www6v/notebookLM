# Gemini 2.5 Pro IMO 2025 Performance

## Overview
This infographic presents how Google's Gemini 2.5 Pro model, using a self-verification pipeline with careful prompt design, successfully solved 5 out of 6 problems from the IMO 2025 competition, demonstrating significant advances in automated mathematical reasoning.

## Learning Objectives
The viewer will understand:
1. How Gemini 2.5 Pro achieved gold-medal performance at IMO 2025 by solving 5 out of 6 problems
2. The self-verification pipeline methodology with its 6-step process (initial solution, self-improvement, verification, bug report review, correction, accept/reject)
3. Why IMO serves as a rigorous benchmark for AI reasoning capabilities beyond traditional math benchmarks

---

## Section 1: Research Achievement

**Key Concept**: Gemini 2.5 Pro solved 5 out of 6 IMO 2025 problems using a self-verification pipeline.

**Content**:
- "5 (out of 6) problems are solved correctly"
- "We use Google's Gemini 2.5 Pro on the newly released IMO 2025 problems, avoiding data contamination"
- "Using a self-verification pipeline with careful prompt design"
- "This result underscores the importance of developing optimal strategies to harness the full potential of powerful LLMs for complex reasoning tasks"
- Authors: "Yichen Huang (黄溢辰)", "Lin F. Yang (杨林)"
- "July 28, 2025"
- "arXiv:2507.15855v3 [cs.AI] 25 Jul 2025"
- "Code available at: https://github.com/lyang36/IMO25"

**Visual Element**:
- Type: achievement badge/highlight box
- Subject: "5/6 problems solved" prominently displayed
- Treatment: Craft-handmade style with hand-drawn badge icon, paper texture background

**Text Labels**:
- Headline: "IMO 2025 突破：5/6 问题正确解答"
- Subhead: "Gemini 2.5 Pro 自验证管道成果"
- Labels: "作者：黄溢辰，杨林", "2025 年 7 月 28 日", "arXiv:2507.15855v3"

---

## Section 2: IMO Background

**Key Concept**: The International Mathematical Olympiad is the world's most prestigious pre-university mathematics competition.

**Content**:
- "The International Mathematical Olympiad (IMO) is an esteemed annual competition that convenes the world's most talented pre-university mathematicians"
- "Established in Romania in 1959 with just seven participating countries"
- "expanded to include over 100 nations"
- "each represented by a team of up to six contestants"
- "Held annually, with the sole exception of 1980"
- "two 4.5-hour sessions over two days"
- "three problems per session, each graded out of seven points"
- "IMO problems demand profound insight, originality, and the ability to synthesize diverse mathematical concepts"
- "fields like algebra, geometry, number theory, and combinatorics"

**Visual Element**:
- Type: illustrated timeline/globe icon
- Subject: World map showing 100+ nations, competition format icons
- Treatment: Hand-drawn globe with country markers, paper craft style competition medals

**Text Labels**:
- Headline: "国际数学奥林匹克 (IMO)"
- Subhead: "全球最负盛名的大学前数学竞赛"
- Labels: "1959 年罗马尼亚创立", "7 国→100+ 国", "每队最多 6 名选手", "两天 sessions，每题 7 分"

---

## Section 3: Why IMO Matters for AI

**Key Concept**: IMO serves as a rigorous benchmark for evaluating advanced AI reasoning capabilities beyond traditional math benchmarks.

**Content**:
- "the IMO has also become a grand challenge and a formidable benchmark for evaluating the advanced reasoning capabilities of Artificial Intelligence, particularly Large Language Models (LLMs)"
- "providing a rigorous test of their ability to perform complex, multi-step logical deduction rather than rote calculation"
- "Traditional benchmarks like GSM8K and MATH focus on grade-school and high-school level problems, respectively"
- "IMO problems surpass these in complexity, requiring multi-step reasoning, abstraction, and innovation akin to human expert-level cognition"
- "exposing limitations in LLMs' generalization and vulnerability to hallucinations or superficial heuristics"
- "This positions the IMO as an ideal probe for assessing whether LLMs can truly 'reason' rather than merely replicate memorized solutions"

**Visual Element**:
- Type: comparison diagram
- Subject: Traditional benchmarks (GSM8K, MATH) vs IMO complexity levels
- Treatment: Hand-drawn comparison chart with ascending difficulty stairs

**Text Labels**:
- Headline: "为什么 IMO 是 AI 的终极测试"
- Subhead: "超越传统数学基准的推理挑战"
- Labels: "GSM8K/MATH: 小学/高中水平", "IMO: 需要多步推理、抽象、创新", "测试真正'推理'能力"

---

## Section 4: Self-Verification Pipeline Overview

**Key Concept**: The 6-step pipeline enables iterative improvement through verification and correction cycles.

**Content**:
- "Step 1: Initial solution generation with the prompt in Section 3.1"
- "Step 2: Self-improvement"
- "Step 3: Verifying the solution with the prompt in Section 3.2 and generating a bug report"
- "Step 4: Review of the bug report (optional)"
- "Step 5: Correcting or improving the solution based on the bug report"
- "Step 6: Accept or Reject"
- "We run the procedure some number of times (in parallel or in serial, independently) to obtain a correct solution"

**Visual Element**:
- Type: flow diagram with 6 numbered steps
- Subject: Sequential pipeline with feedback loop from Step 5 back to Step 3
- Treatment: Hand-drawn flow boxes with arrows, craft paper style connectors

**Text Labels**:
- Headline: "自验证管道：6 步流程"
- Step labels: "Step 1: 初始解答生成", "Step 2: 自我改进", "Step 3: 验证并生成 bug 报告", "Step 4: 审查 bug 报告 (可选)", "Step 5: 修正改进", "Step 6: 接受/拒绝"

---

## Section 5: Pipeline Flow Details

**Key Concept**: The pipeline uses iterative verification cycles with specific conditions for acceptance or rejection.

**Content**:
- "go to Step 4 or Step 6 (see below for explanations)"
- "go to Step 3" (from Step 5)
- "failed consecutively passes 5 times" → Accept
- "w/ major issue for 10 steps" → Reject
- "We hope the model either outputs the correct solution, or claims that it fails to identify the solution"

**Visual Element**:
- Type: detailed flow chart with decision points
- Subject: Decision tree showing accept/reject conditions
- Treatment: Hand-drawn decision diamonds, craft-style path arrows

**Text Labels**:
- Headline: "管道流程详解"
- Decision labels: "连续 5 次通过→接受", "10 步仍有重大问题→拒绝"
- Loop label: "迭代改进循环"

---

## Section 6: Solver Methodology

**Key Concept**: The solver prompt emphasizes rigor over finding final answers, with thinking budget constraints addressed through step breakdown.

**Content**:
- "The solver prompt in Section 3.1 for Step 1 is designed to emphasize rigor rather than focus on finding the final answer"
- "Gemini 2.5 Pro is good at mathematics, as a general-purpose LLM, it is not tailored to solving especially challenging mathematical problems"
- "One significant constraint is the thinking budget"
- "The maximum number of thinking tokens of Gemini 2.5 Pro is 32768"
- "Even a trivial fact might take a few thousand tokens for the model to prove"
- "Step 2 effectively injects another budget of 32768 thinking tokens to allow the model review and continue its work"
- "We keep monitoring the entire process and do observe that the outputs have been noticeably improved during Step 2"

**Visual Element**:
- Type: token budget visualization
- Subject: Thinking token allocation across steps (32768 per step)
- Treatment: Hand-drawn battery/token icons, paper craft style progress bars

**Text Labels**:
- Headline: "解答器方法"
- Subhead: "思考预算与逐步突破"
- Labels: "最大思考 tokens: 32768", "Step 1: 几乎用尽预算", "Step 2: 注入新 32768 tokens", "输出显著改进"

---

## Section 7: Verifier Functionality

**Key Concept**: The verifier carefully reviews solutions step by step, classifying issues into critical errors and justification gaps.

**Content**:
- "The verifier plays an important role in our pipeline"
- "Its functionality is to carefully review a solution step by step and find out issues (if any)"
- "We emphasize mathematical rigor and classify issues into critical errors and justification gaps"
- "Critical errors are something that is demonstratively false or with clear logical fallacies"
- "justification gaps can be major or minor"
- "A major justification gap that cannot be repaired would crash an entire proof"
- "minor justification gaps may not even be well defined: A minor gap could sometimes be viewed as concise argument"
- "The bug report contains a list of issues classified as critical errors or justification gaps"
- "For each issue, an explanation is required"

**Visual Element**:
- Type: classification diagram
- Subject: Issue taxonomy (Critical Errors vs Justification Gaps → Major/Minor)
- Treatment: Hand-drawn tree diagram, craft paper style classification boxes

**Text Labels**:
- Headline: "验证器功能"
- Subhead: "问题分类与 bug 报告"
- Labels: "关键错误：明显虚假或逻辑谬误", "论证缺口：主要/次要", "主要缺口无法修复→证明崩溃", "次要缺口：可视为简洁论证"

---

## Section 8: Iterative Improvement Process

**Key Concept**: Steps 3-5 iterate until a solution is accepted or declined based on verification results.

**Content**:
- "In Step 3, we use the verifier to generate a bug report for each solution outputted in Step 2"
- "The bug report will serve as useful information for the model to improve the solution, either fixing errors or filling gaps"
- "Step 4 (optional) is to carefully review each issue in the bug report"
- "If the verifier makes a mistake and reports an issue which is not really an issue, the issue would be deleted from the bug report"
- "Step 4 increases the reliability of the bug report"
- "In Step 5, the model tries to improve the solution based on the bug report"
- "We iterate Steps 3-5 a sufficient number of times until we decide to accept or decline a solution"
- "We accept a solution if it robustly passes the verification process"
- "decline a solution if there are always critical errors or major justification gaps during the iterations"

**Visual Element**:
- Type: iteration cycle diagram
- Subject: Steps 3-5 loop with bug report feedback
- Treatment: Hand-drawn circular arrows, craft paper style iteration markers

**Text Labels**:
- Headline: "迭代改进过程"
- Subhead: "验证→修正→再验证循环"
- Labels: "Step 3: 生成 bug 报告", "Step 4: 审查 (提高可靠性)", "Step 5: 基于报告改进", "稳健通过→接受", "持续关键错误→拒绝"

---

## Section 9: Verifier Reliability

**Key Concept**: The verifier is highly reliable at detecting critical errors, with qualitative observations supporting its effectiveness.

**Content**:
- "We observe that the verifier is quite reliable but can make mistakes"
- "Since our major goal is not to benchmark the verifier, we do not have quantitative results on its effectiveness"
- "We have used this verifier for quite a while (starting from well before IMO 2025)"
- "We have been keeping an eye on its performance and below is our qualitative observation"
- "Critical errors are seldom missed by the verifier"

**Visual Element**:
- Type: reliability indicator
- Subject: Checkmark showing high critical error detection rate
- Treatment: Hand-drawn reliability gauge, craft paper style confidence meter

**Text Labels**:
- Headline: "验证器可靠性"
- Subhead: "定性观察结果"
- Labels: "关键错误很少被遗漏", "自 IMO 2025 之前已使用", "非定量基准测试"

---

## Section 10: Context & Competition

**Key Concept**: Other teams also reported high-level performance on IMO 2025, showing broader progress in the field.

**Content**:
- "Concurrent with our work, other teams also reported high-level performance on the IMO 2025 problems"
- "These include OpenAI [17], Google DeepMind [11], and ByteDance [2]"
- "recent evaluations on problems from the USA Mathematical Olympiad (USAMO) 2025 and IMO 2025 showed that top-tier public models still struggle to produce sound, rigorous proofs"
- "fail to achieve scores comparable to human medalists"
- "often succumbing to logical fallacies and a lack of creative insight"
- "This highlights a critical gap between generating numerically correct answers and constructing logically sound arguments"

**Visual Element**:
- Type: comparison/team logos
- Subject: Multiple teams (OpenAI, DeepMind, ByteDance, this work) with their approaches
- Treatment: Hand-drawn team badges, craft paper style comparison grid

**Text Labels**:
- Headline: "同期进展"
- Subhead: "多团队 IMO 2025 成果"
- Labels: "OpenAI", "Google DeepMind", "ByteDance", "本研究：5/6 正确"

---

## Section 11: Key Innovation

**Key Concept**: Strong existing models can solve difficult math problems, but optimal strategies are essential for harnessing their full potential.

**Content**:
- "Our approach shows that strong existing models are already capable of solving difficult math reasoning problems"
- "but directly using them can result in poor results"
- "Our results demonstrate a significant advance in automated mathematical reasoning"
- "This work exclusively utilizes the problems from the most recent IMO 2025 competition"
- "As these problems were released only days before our evaluation, they serve as a pristine testbed"
- "mitigating the risk of data leakage"
- "providing a robust measure of the model's ability to generalize and reason on genuinely unseen challenges"

**Visual Element**:
- Type: innovation highlight box
- Subject: Key insight about strategy vs model capability
- Treatment: Hand-drawn lightbulb icon, craft paper style insight card

**Text Labels**:
- Headline: "关键创新"
- Subhead: "策略优于直接使用"
- Labels: "强模型已有能力", "需要最优策略", "无数据污染测试", "真正的泛化能力验证"

---

## Data Points (Verbatim)

All statistics, numbers, and quotes exactly as they appear in source:

### Statistics
- "5 (out of 6) problems are solved correctly"
- "Established in Romania in 1959 with just seven participating countries"
- "expanded to include over 100 nations"
- "team of up to six contestants"
- "two 4.5-hour sessions over two days"
- "three problems per session, each graded out of seven points"
- "The maximum number of thinking tokens of Gemini 2.5 Pro is 32768"

### Quotes
- "IMO problems demand profound insight, originality, and the ability to synthesize diverse mathematical concepts" — Introduction
- "Critical errors are something that is demonstratively false or with clear logical fallacies" — Section 2.3
- "justification gaps can be major or minor" — Section 2.3
- "This positions the IMO as an ideal probe for assessing whether LLMs can truly 'reason' rather than merely replicate memorized solutions" — Introduction

### Key Terms
- **International Mathematical Olympiad (IMO)**: "an esteemed annual competition that convenes the world's most talented pre-university mathematicians"
- **Chain-of-Thought (CoT) prompting**: "enables models to generate intermediate reasoning steps, thereby improving performance on tasks requiring complex logic and calculation"
- **Critical errors**: "something that is demonstratively false or with clear logical fallacies"
- **Justification gaps**: "can be major or minor. A major justification gap that cannot be repaired would crash an entire proof"

### References & Metadata
- "Code available at: https://github.com/lyang36/IMO25"
- "arXiv:2507.15855v3 [cs.AI] 25 Jul 2025"
- Authors: "Yichen Huang (黄溢辰)", "Lin F. Yang (杨林)"
- "July 28, 2025"

---

## Design Instructions

Extracted from user's steering prompt:

### Style Preferences
- Visual style: craft-handmade (hand-drawn, paper craft aesthetic)
- Mood: approachable visualization of complex technical content
- Artistic style: clean, professional with handmade charm

### Layout Preferences
- Layout: bento-grid (multiple topics organized in grid modules)
- Structure: 11 sections covering achievement, background, methodology, pipeline, results
- Organization: logical flow from achievement → context → methods → details → conclusions

### Other Requirements
- Aspect ratio: landscape (16:9)
- Language: 简体中文 (all text content in Simplified Chinese)
- Target: technical/research community familiar with AI/LLM concepts
- Platform: publication-ready infographic for research dissemination

### Bento-Grid Module Arrangement
- Top row: Section 1 (Achievement highlight - large), Section 2 (IMO Background)
- Second row: Section 3 (Why IMO), Section 4 (Pipeline Overview)
- Third row: Section 5 (Flow Details), Section 6 (Solver), Section 7 (Verifier)
- Fourth row: Section 8 (Iteration), Section 9 (Reliability), Section 10 (Competition)
- Bottom row: Section 11 (Key Innovation - full width)
