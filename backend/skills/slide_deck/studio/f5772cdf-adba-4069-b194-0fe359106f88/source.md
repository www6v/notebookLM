# Generated Slides

## Slide Deck Request
- version: v2
- language: 简体中文
- style: blueprint
- audience: general
- slides: 2

## Source Content
[2507.15855v3.pdf]: Gemini 2.5 Pro Capable of Winning Gold at IMO 2025 ∗
Yichen Huang (黄溢辰)† Lin F. Yang (杨林)‡
July 28, 2025
Abstract
The International Mathematical Olympiad (IMO) poses uniquely challenging prob-
lems requiring deep insight, creativity, and formal reasoning. While Large Language
Models (LLMs) perform well on mathematical benchmarks like AIME, they struggle
with Olympiad-level tasks. We use Google’s Gemini 2.5 Pro on the newly released
IMO 2025 problems, avoiding data contamination. Using a self-verification pipeline
with careful prompt design, 5 (out of 6) problems are solved correctly. This result un-
derscores the importance of developing optimal strategies to harness the full potential
of powerful LLMs for complex reasoning tasks.
1 Introduction
The International Mathematical Olympiad (IMO) [1] is an esteemed annual competition that
convenes the world’s most talented pre-university mathematicians. Established in Romania
in 1959 with just seven participating countries, it has since expanded to include over 100
nations, each represented by a team of up to six contestants. Held annually, with the sole
exception of 1980, the IMO challenges participants with exceptionally difficult problems in
fields like algebra, geometry, number theory, and combinatorics. Contestants are given two
4.5-hour sessions over two days to solve three problems per session, each graded out of seven
points. Unlike typical mathematical exercises, IMO problems demand profound insight,
originality, and the ability to synthesize diverse mathematical concepts. This emphasis on
creative, proof-based reasoning makes the IMO a hallmark of mathematical excellence and
a vital platform for identifying future leaders in the field.
Consequently, the IMO has also become a grand challenge and a formidable benchmark
for evaluating the advanced reasoning capabilities of Artificial Intelligence, particularly Large
Language Models (LLMs), providing a rigorous test of their ability to perform complex,
multi-step logical deduction rather than rote calculation [9, 15, 3]. Traditional benchmarks
∗Code available at: https://github.com/lyang36/IMO25
†huangtbcmh@gmail.com
‡linyang@ee.ucla.edu, Department of Electrical and Computer Engineering, and Department of Com-
puter Science, UCLA
1
arXiv:2507.15855v3  [cs.AI]  25 Jul 2025

like GSM8K and MATH focus on grade-school and high-school level problems, respectively,
where LLMs have achieved high performance through pattern recognition and retrieval from
training data [6, 10]. However, IMO problems surpass these in complexity, requiring multi-
step reasoning, abstraction, and innovation akin to human expert-level cognition, thereby
exposing limitations in LLMs’ generalization and vulnerability to hallucinations or superficial
heuristics [7]. This positions the IMO as an ideal probe for assessing whether LLMs can truly
“reason” rather than merely replicate memorized solutions, addressing concerns about their
reliability in high-stakes domains like scientific discovery and formal verification [19].
The pursuit of automated mathematical reasoning has seen remarkable progress with the
advent of LLMs [4, 16]. Early successes on foundational benchmarks have rapidly escalated
to tackling complex, competition-level mathematics. This progress has been significantly
propelled by innovations such as Chain-of-Thought (CoT) prompting, which enables models
to generate intermediate reasoning steps, thereby improving performance on tasks requiring
complex logic and calculation [18]. Nevertheless, even state-of-the-art models have demon-
strated significant limitations when confronted with Olympiad-level problems. For example,
recent evaluations on problems from the USA Mathematical Olympiad (USAMO) 2025 and
IMO 2025 showed that top-tier public models still struggle to produce sound, rigorous proofs
and fail to achieve scores comparable to human medalists, often succumbing to logical falla-
cies and a lack of creative insight [13, 3]. This highlights a critical gap between generating
numerically correct answers and constructing logically sound arguments [12].
In this paper, we construct a self-verification pipeline with careful prompt design and
implemented using the Gemini 2.5 Pro model, a strong base model released by Google [ ?].
We solved 5 out of the 6 problems of IMO 2025. A persistent and critical challenge in
the evaluation of LLMs is the issue of data contamination, where test data from public
benchmarks is inadvertently included in the vast pre-training corpora, leading to inflated and
unreliable performance metrics [5]. To ensure a rigorous and uncontaminated assessment of
the model’s genuine problem-solving capabilities, this work exclusively utilizes the problems
from the most recent IMO 2025 competition. As these problems were released only days
before our evaluation, they serve as a pristine testbed, mitigating the risk of data leakage
and providing a robust measure of the model’s ability to generalize and reason on genuinely
unseen challenges. Our approach shows that strong existing models are already capable of
solving difficult math reasoning problems, but directly using them can result in poor results
as shown in [3]. Our results demonstrate a significant advance in automated mathematical
reasoning.
Concurrent with our work, other teams also reported high-level performance on the IMO
2025 problems. These include OpenAI [17], Google DeepMind [11], and ByteDance [2].
2 Methods
2.1 Pipeline
At a high level, our pipeline proceeds as follows (illustrated in Figure 1):
2

• Step 1: Initial solution generation with the prompt in Section 3.1;
• Step 2: Self-improvement;
• Step 3: Verifying the solution with the prompt in Section 3.2 and generating a bug
report; go to Step 4 or Step 6 (see below for explanations);
• Step 4: Review of the bug report (optional);
• Step 5: Correcting or improving the solution based on the bug report; go to Step 3;
• Step 6: Accept or Reject.
Step 1:
Initial solution
generation
Step 2:
Self-improvement
Step 3:
Verification
(Go to Step 4 or 6)
Step 4:
Bug report re-
view (optional)
Step 5:
Correction
Step 6:
Accept
Step 6′:
Reject
failed
consecutively passes 5 timesw/ major issue for 10 steps
Figure 1: Flow diagram of our pipeline. See the main text for detailed explanations of each
step.
We run the procedure some number of times (in parallel or in serial, independently) to
obtain a correct solution. We hope the model either outputs the correct solution, or claims
that it fails to identify the solution.
2.2 Solver
The solver prompt in Section 3.1 for Step 1 is designed to emphasize rigor rather than focus
on finding the final answer and thus matches the theme of IMO. We have randomly selected
some outputs of this step and found that the overall quality of the solutions are pretty low.
This is consistent with very recent findings of Ref. [3].
In Step 2, the model is prompted to review and try to improve its work. While Gemini 2.5
Pro is good at mathematics, as a general-purpose LLM, it is not tailored to solving especially
challenging mathematical problems. One significant constraint is the thinking budget. Note
that thinking is quite token consuming: Even a trivial fact might take a few thousand tokens
for the model to prove. The maximum number of thinking tokens of Gemini 2.5 Pro is 32768,
which is not enough for solving a typical IMO problem. We observe that in Step 1, the model
almost always uses up its thinking budget. Thus, the model does not even have the capacity
3

to fully solve the problem. This is why we choose to break down the problem solving process
into steps. Step 2 effectively injects another budget of 32768 thinking tokens to allow the
model review and continue its work. We keep monitoring the entire process and do observe
that the outputs have been noticeably improved during Step 2.
Next we will use the verifier to make iterative improvement and decide whether to accept
an improved solution.
2.3 Verifier
The verifier plays an important role in our pipeline. Its functionality is to carefully review
a solution step by step and find out issues (if any). We emphasize mathematical rigor and
classify issues into critical errors and justification gaps. Critical errors are something that
is demonstratively false or with clear logical fallacies, while justification gaps can be major
or minor. A major justification gap that cannot be repaired would crash an entire proof,
while minor justification gaps may not even be well defined: A minor gap could sometimes
be viewed as concise argument.
In Step 3, we use the verifier to generate a bug report for each solution outputted in Step
2. The bug report contains a list of issues classified as critical errors or justification gaps.
For each issue, an explanation is required. The bug report will serve as useful information for
the model to improve the solution, either fixing errors or filling gaps. Step 4 (optional) is to
carefully review each issue in the bug report. If the verifier makes a mistake and reports an
issue which is not really an issue, the issue would be deleted from the bug report. Thus, Step
4 increases the reliability of the bug report. In Step 5, the model tries to improve the solution
based on the bug report. We iterate Steps 3-5 a sufficient number of times until we decide
to accept or decline a solution. We accept a solution if it robustly passes the verification
process and decline a solution if there are always critical errors or major justification gaps
during the iterations.
We observe that the verifier is quite reliable but can make mistakes. Since our major
goal is not to benchmark the verifier, we do not have quantitative results on its effectiveness.
However, we have used this verifier for quite a while (starting from well before IMO 2025).
We have been keeping an eye on its performance and below is our qualitative observation:
• Critical errors are seldom missed by the verifier. This is consistent with the observat
