Create a professional infographic following these specifications:

## Image Specifications

- **Type**: Infographic
- **Layout**: bento-grid
- **Style**: craft-handmade
- **Aspect Ratio**: 16:9 (landscape)
- **Language**: 简体中文

## Core Principles

- Follow the layout structure precisely for information architecture
- Apply style aesthetics consistently throughout
- If content involves sensitive or copyrighted figures, create stylistically similar alternatives
- Keep information concise, highlight keywords and core concepts
- Use ample whitespace for visual clarity
- Maintain clear visual hierarchy

## Text Requirements

- All text must match the specified style treatment
- Main titles should be prominent and readable
- Key concepts should be visually emphasized
- Labels should be clear and appropriately sized
- Use the specified language for all text content

## Layout Guidelines

# bento-grid

Modular grid layout with varied cell sizes, like a bento box.

## Structure

- Grid of rectangular cells
- Mixed cell sizes (1x1, 2x1, 1x2, 2x2)
- No strict symmetry required
- Hero cell for main point
- Supporting cells around it

## Best For

- Multiple topic overview
- Feature highlights
- Dashboard summaries
- Portfolio displays
- Mixed content types

## Visual Elements

- Clear cell boundaries
- Varied cell backgrounds
- Icons or illustrations per cell
- Consistent padding/margins
- Visual hierarchy through size

## Text Placement

- Main title at top
- Cell titles within each cell
- Brief content per cell
- Minimal text, maximum visual
- CTA or summary in prominent cell

## Recommended Pairings

- `craft-handmade`: Friendly overviews (default)
- `corporate-memphis`: Business summaries
- `pixel-art`: Retro feature grids

## Style Guidelines

# craft-handmade (DEFAULT)

Hand-drawn and paper craft aesthetic with warm, organic feel.

## Color Palette

- Primary: Warm pastels, soft saturated colors, craft paper tones
- Background: Light cream (#FFF8F0), textured paper (#F5F0E6)
- Accents: Bold highlights, construction paper colors

## Variants

| Variant | Focus | Visual Emphasis |
|---------|-------|-----------------|
| **Hand-drawn** | Cartoon illustration | Simple icons, slightly imperfect lines |
| **Paper-cutout** | Layered paper craft | Drop shadows, torn edges, texture |

## Visual Elements

- Hand-drawn or cut-paper quality
- Organic, slightly imperfect shapes
- Layered depth with shadows (paper variant)
- Simple cartoon elements and icons
- Character illustrations (people, personalities in cartoon form)
- Ample whitespace, clean composition
- Keywords and core concepts highlighted
- **Strictly hand-drawn—no realistic or photographic elements**

## Style Enforcement

- All imagery must maintain cartoon/illustrated aesthetic
- Replace real photos or realistic figures with hand-drawn equivalents
- Maintain consistent line weight and illustration style throughout

## Typography

- Hand-drawn or casual font style
- Clear, readable labels
- Keywords emphasized with larger/bolder text
- Cut-out letter style for paper variant

## Best For

Educational content, general explanations, friendly infographics, children's content, playful hierarchies

---

Generate the infographic based on the content below:

# 使用 RLVR 构建最先进的 SQL 推理模型

## 概述
本信息图展示了 Databricks Mosaic Research 如何使用强化学习与可验证奖励（RLVR）开发最先进的 SQL 推理模型，在 BIRD 基准测试中通过自一致性达到 75.68% 的准确率。

## 学习目标
观众将了解：
1. RLVR（强化学习与可验证奖励）如何用于微调文本到 SQL 任务的大型语言模型
2. 两阶段训练流程：离线 TAO 预热 followed by 在线 RLVR 训练
3. 取得的成果：在 BIRD 私有测试集上，无自一致性时准确率 73.56%，有自一致性时 75.68%

---

## 模块 1：挑战 - 企业特定知识缺口

**核心概念**：现成的大型语言模型在理解组织特定术语、概念、工具和 API 方面存在局限。

**内容**：
- "LLMs have become a fixture in a range of enterprise problems including software engineering, data science, and more recently even research itself"
- "Despite sometime impressive performance of off-the-shelf LLMs, they face limitations in doing more bespoke enterprise tasks"
- "Limitations such as unable to understand organization-specific terminology or use organization-specific concepts, tools, and APIs"
- "For example, given a user query 'show me all churned users for 2024?', the model may not know how the organization defines 'churned users'"
- "Or, the model may not be aware of certain preferences such as always sorting certain queries with a given column"
- "Unlike math problems where the training data might be more available on the internet, organizational knowledge might be more protected and less represented on the internet"

**视觉元素**：
- 类型：带问题图标的插图
- 主题：大型语言模型在理解企业特定概念（行话、API、数据位置）方面的挣扎
- 处理：手绘风格展示通用大型语言模型知识与组织特定需求之间的差距

**文本标签**：
- 标题："企业知识缺口"
- 副标题："为什么现成的大型语言模型会挣扎"
- 标签："组织特定术语"、"定制工具和 API"、"受保护的数据源"、"行业行话"

---

## 模块 2：解决方案 - RLVR 框架

**核心概念**：RLVR 是一种后训练范式，应用强化学习来微调大型语言模型，使用可验证奖励而无需参数化奖励模型。

**内容**：
- "RLVR is a post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models"
- "RLVR is particularly suited to tasks where the LLM is trying to predict facts, mathematical statements, or generating executable code, as its responses can be measured objectively given access to ground truth"
- "This contrasts with non-verifiable tasks that typically measure subjective tasks such as generating poetry, or an essay on a given topic"
- "For the task in Figure 1, we can measure if a given AI agent's SQL response is correct by matching it against the ground truth SQL response for that user query"

**视觉元素**：
- 类型：概念图
- 主题：RLVR 框架展示可验证奖励机制
- 处理：清晰的手绘流程展示查询 → SQL 生成 → 执行 → 比较 → 奖励

**文本标签**：
- 标题："强化学习与可验证奖励（RLVR）"
- 副标题："无需奖励模型的客观质量指标"
- 标签："可验证奖励"、"地面真实"、"客观测量"

---

## 模块 3：Text2SQL 任务

**核心概念**：Text2SQL 需要理解用户查询在复杂数据库结构上下文中的含义，以生成正确的 SQL 代码。

**内容**：
- "In this task, a user asks a natural language query x∈ X to access a database d∈ D"
- "An agent then generates a SQL code y∈ Y which is executed on the database and its output is returned to the user"
- "The goal of the agent is to generate a SQL code that best captures the intent of the user query"
- "The main challenge in text2sql is that it requires understanding the query in the context of the database which can be quite complex"
- "For example, the database may have many tables with many columns, column names can be ambiguous, correct column values may need to be found and tables may need to be joined to answer the user query"

**视觉元素**：
- 类型：任务流程图
- 主题：用户查询 → 数据库上下文 → SQL 生成 → 执行 → 结果
- 处理：手绘数据库架构，包含表、列和查询流程

**文本标签**：
- 标题："Text2SQL 挑战"
- 副标题："从自然语言到可执行 SQL"
- 标签："用户查询"、"数据库架构"、"SQL 代码"、"执行结果"

---

## 模块 4：两阶段训练流程

**核心概念**：该方法使用两阶段微调流程：TAO 离线强化学习预热，然后是在线 RLVR 训练。

**内容**：
- "Our approach starts by carefully selecting the model, context, and prompt"
- "The prompt can be chosen using prompt optimization approaches such as GEPA"
- "We then perform a two-stage fine-tuning of the model with the chosen context and prompt"
- "First, we warm start the model using Test-time Adaptive Optimization (TAO), an offline RL approach"
- "This is followed by fine-tuning the model using Databricks's RLVR service"
- "Our RLVR service supports popular learning approaches such as GRPO, as well as more powerful alternatives"
- "Finally, we perform self-consistency on top of the fine-tuned model at inference time"

**视觉元素**：
- 类型：流程图（基于图 1）
- 主题：两阶段流程展示 TAO → RLVR → 自一致性流
- 处理：手绘流程，清晰的阶段分离，展示奖励计算和模型更新

**文本标签**：
- 标题："两阶段训练流程"
- 阶段 1："离线 TAO 预热"
- 阶段 2："在线 RLVR 训练"
- 最终："自一致性推理"
- 标签："模型选择"、"提示优化"、"TAO 优化"、"RLVR 优化"、"可验证奖励（VR）"

---

## 模块 5：BIRD 基准测试

**核心概念**：BIRD 是一个流行的 text2sql 基准测试，用于评估模型将自然语言查询转换为 SQL 执行的能力。

**内容**：
- "We apply RLVR to a popular data science benchmark called BIRD that measures the ability of an AI agent to convert natural language query for a database to SQL executions"
- "A BIRD datapoint includes a user query, an evidence field providing additional instruction, a database containing multiple tables, and a gold SQL code denoting ground truth"
- "The BIRD dataset consists of a train set of 9,428 examples, a dev set of 1,534 examples, and a test set of 1,789 examples"
- "The test set is not publicly available allowing evaluation without dataset contamination concerns and prevents benchmark hacking"
- "The evaluation metric for BIRD is a strict 0-1 metric where given the generated SQL code, we execute both the gold SQL and the generated SQL code on the database and check if their outputs match (1) or not (0)"
- "We train the model using the train set and use the dev set performance for model and hyperparameter selection"
- "We do not use any additional training data"

**视觉元素**：
- 类型：数据集分解可视化
- 主题：BIRD 数据集组成（训练/开发/测试拆分）
- 处理：手绘条形图或模块展示数据集大小和评估指标

**文本标签**：
- 标题："BIRD 基准测试"
- 副标题："Text2SQL 评估数据集"
- 标签："训练集：9,428 个示例"、"开发集：1,534 个示例"、"测试集：1,789 个示例"、"严格 0-1 指标"

---

## 模块 6：最先进的成果

**核心概念**：RLVR 训练的模型在 BIRD 私有测试集上达到了最先进的准确率，生成的数量少于竞争方法。

**内容**：
- "With no additional training data beyond the BIRD training set and no use of proprietary models, our very first submission to the BIRD leaderboard reached state-of-the-art accuracy on the private test set: 73.56% without self-consistency and 75.68% with self-consistency"
- "In the latter case, our model also required fewer generations than the second-best approach"
- "Our RLVR-trained model already achieves state-of-the-art in single-model single-LLM call category"
- "Whereas self-consistency adds complimentary benefits and gives us the overall best single-model performance"
- "Further, our model generalizes better than other top-submissions and achieves state-of-the-art using fewer self-consistency responses than the second best result"

**视觉元素**：
- 类型：成果亮点与对比图（基于图 2）
- 主题：准确率指标展示 73.56% 和 75.68%，与其他模型对比
- 处理：手绘条形图或数字亮点，强调最先进的成果

**文本标签**：
- 标题："最先进的成果"
- 主要指标："自一致性下 75.68%"
- 次要指标："无自一致性下 73.56%"
- 标签："单模型最先进的"、"更少生成"、"更好的泛化"、"首次提交"

---

## 模块 7：更广泛的应用

**核心概念**：RLVR 框架的简洁性使其广泛适用于 BIRD 代理任务之外的企业领域。

**内容**：
- "While BIRD is only a proxy task, the simplicity of our framework makes it broadly applicable to enterprise domains such as business intelligence, data science, and coding"
- "Developing custom reasoning models via Reinforcement Learning (RL) that can incorporate organization-specific knowledge has great potential to address problems faced by enterprise customers"
- "In many of these problems, the reward function is verifiable, a setting termed RL with Verifiable Rewards (RLVR)"

**视觉元素**：
- 类型：应用图标
- 主题：企业领域（商业智能、数据科学、编码）
- 处理：手绘图标代表不同的应用领域

**文本标签**：
- 标题："更广泛的企业应用"
- 标签："商业智能"、"数据科学"、"编码"、"组织特定知识"

---

## 数据点（逐字保留）

所有统计数据、数字和引用按源文件中的确切形式呈现：

### 统计数据
- "73.56% without self-consistency and 75.68% with self-consistency"
- "BIRD dataset consists of a train set of 9,428 examples, a dev set of 1,534 examples, and a test set of 1,789 examples"
- "our very first submission to the BIRD leaderboard reached state-of-the-art accuracy on the private test set"
- "our model also required fewer generations than the second-best approach"

### 引用
- "RLVR is a post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models" — Databricks Mosaic Research
- "The evaluation metric for BIRD is a strict 0-1 metric where given the generated SQL code, we execute both the gold SQL and the generated SQL code on the database and check if their outputs match (1) or not (0)" — Databricks Mosaic Research
- "With no additional training data beyond the BIRD training set and no use of proprietary models" — Databricks Mosaic Research

### 关键术语
- **RLVR（强化学习与可验证奖励）**："A post-training paradigm of applying reinforcement learning to fine-tune a pre-trained LLM on a given task where the reward function measures an objective truth without needing any parametrized reward models"
- **TAO（测试时自适应优化）**："An offline RL approach"
- **Text2SQL**："A task where a user asks a natural language query to access a database, and an agent generates SQL code which is executed on the database"
- **BIRD 基准测试**："A popular data science benchmark that measures the ability of an AI agent to convert natural language query for a database to SQL executions"
- **自一致性**："An inference-time approach that spends more inference compute at test time to improve a model's performance"

---

## 设计说明

从用户指导提示中提取：

### 风格偏好
- 视觉风格：craft-handmade（手绘、纸艺美学）
- 详细程度：标准
- 情绪：专业但亲切，使复杂的技术内容易于理解

### 布局偏好
- 布局：bento-grid（平衡网格中的多个信息模块）
- 宽高比：landscape（16:9，横向）
- 结构：多个部分组织在网格模块中，以获得概述清晰度

### 其他要求
- 语言：简体中文（所有文本内容为简体中文）
- 目标受众：数据科学家、机器学习工程师、企业 AI 从业者（中级到专家级）
- 内容类型：流程/技术，附带支持证据
- 逐字保留所有源数据 - 不总结或改写统计数据和引用

Text labels (in 简体中文):
- 主标题："使用 RLVR 构建最先进的 SQL 推理模型"
- 模块标题："企业知识缺口"、"RLVR 框架"、"Text2SQL 挑战"、"两阶段训练流程"、"BIRD 基准测试"、"最先进的成果"、"更广泛的企业应用"
- 关键指标："75.68% 自一致性"、"73.56% 无自一致性"
- 数据集标签："训练集 9,428"、"开发集 1,534"、"测试集 1,789"
- 核心术语："RLVR"、"TAO"、"Text2SQL"、"BIRD"、"自一致性"
