# CLAUDE.md

Smart Education 多 Agent 工作流框架的 AI 协作文档。

## 环境

```bash
uv venv
uv pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填入 API Key：

- `TEXT_LLM_*` — 主力文本模型（DeepSeek / OpenAI 兼容）
- `VISION_LLM_*` — 视觉模型（Qwen-VL / GPT-4o 等，用于图片分析）

```bash
.venv\Scripts\python.exe <script>.py     # Windows
.venv/bin/python <script>.py             # macOS / Linux
```

## 项目架构

```
src/
├── config.py              # 从 .env 加载两套 LLM 配置
├── workflow/
│   ├── base.py            # BaseNode 抽象类 + WorkflowContext
│   ├── engine.py          # Workflow 执行器（线性+条件分支）
│   └── nodes/             # 节点实现
│       ├── start_node.py
│       ├── end_node.py
│       ├── llm_node.py
│       ├── input_node.py
│       ├── conditional_branch_node.py
│       ├── json_extractor_node.py
│       ├── subworkflow_node.py
│       └── iterative_workflow_node.py
├── llm/
│   ├── base_client.py     # BaseLLMClient 抽象类
│   ├── openai_client.py   # OpenAI 客户端
│   ├── deepseek_client.py # DeepSeek 客户端（OpenAI 兼容）
│   ├── vision_client.py   # 视觉模型客户端（图片→文本）
│   └── fake_client.py     # 测试用假客户端
└── tools/
    ├── pptx_to_pdf.py     # PPTX→PDF（PowerPoint COM）
    ├── pdf_to_images.py   # PDF→PNG（PyMuPDF）
    └── pipeline.py        # 串联管线：PPTX→PDF→Images→Vision→XML
```

## 核心概念

### WorkflowContext

`dict[str, Any]`，节点间通过它在键值对传递数据。

### 节点类型速查

所有节点继承 `BaseNode`，实现 `execute(context) -> context`。

#### StartNode

```python
StartNode(
    node_id="start", node_name="Start",
    output_variable_names=["user_query"],  # 期望的初始变量
    next_node_id="llm_1"                   # 可选，指定下一节点
)
```

#### LLMNode

```python
LLMNode(
    node_id="llm_1", node_name="LLM",
    system_prompt_template="回答: {user_query}",  # {var} 从上下文注入
    output_variable_name="answer",
    llm_client=llm_client,
    stream=True, stream_callback=callback,         # 可选流式
    next_node_id="end"
)
```

#### EndNode

```python
EndNode(
    node_id="end", node_name="End",
    input_variable_names=["answer"]  # 提取的结果变量
)
```

#### ConditionalBranchNode

使用 LLM 对输入分类，自动路由到不同分支：

```python
from src.workflow.nodes.conditional_branch_node import (
    ConditionalBranchNode, ClassDefinition
)

ConditionalBranchNode(
    node_id="branch", node_name="Branch",
    classes=[
        ClassDefinition(name="A", description="...",
                        next_node_id="handler_a",
                        examples=["例子1"]),
    ],
    input_variable_name="text_to_classify",
    llm_client=llm_client,
    default_class=ClassDefinition(name="default", ...),  # 兜底
    output_reason=True
)
```

#### JSONExtractorNode

从 LLM 响应中提取 JSON，可选 schema 验证：

```python
JSONExtractorNode(
    node_id="extract", node_name="Extract",
    input_variable_name="raw_text",
    output_variable_name="parsed_json",
    schema={"type": "object", "properties": {...}},  # 可选
    default_value={}, raise_on_error=False
)
```

#### SubWorkflowNode

封装独立子工作流，支持变量映射：

```python
SubWorkflowNode(
    node_id="sub", node_name="Sub",
    nodes=[inner_start, inner_llm, inner_end],
    input_mapping={"main_var": "sub_var"},
    output_mapping={"sub_result": "main_result"},
    entry_node_id="inner_start",   # 可选
    exit_node_id="inner_end",      # 可选
    next_node_id="next_after_sub"
)
```

#### IterativeWorkflowNode

重复执行子工作流直到条件满足：

```python
IterativeWorkflowNode(
    node_id="iter", node_name="Iter",
    nodes=[...],
    condition_function=lambda ctx: ctx.get("score", 0) < 0.8,
    max_iterations=10,
    input_mapping={"initial": "current"},
    output_mapping={"final": "result"},
    iteration_mapping={"improved": "current"},  # 迭代间传递
    result_collection_mode="append",            # replace/append/merge
    result_variable="history"
)
```

#### InputNode

暂停工作流获取用户输入：

```python
InputNode(
    node_id="input", node_name="Input",
    prompt_text="请输入: ",
    output_variable_name="user_response",
    default_value="默认值",
    validation_func=lambda x: len(x) > 0
)
```

### 工作流组装

```python
from src.workflow.engine import Workflow

workflow = Workflow([start, llm, branch, handler_a, handler_b, end])
final_context = workflow.run({"user_query": "什么是AI?"})
```

## LLM 客户端

### 工厂函数（推荐）

```python
from src.config import create_text_llm_client, create_vision_llm_client

text_llm = create_text_llm_client()
vision = create_vision_llm_client()
```

### 手动创建

```python
from src.llm import DeepSeekClient, OpenAIClient, FakeLLMClient

llm = DeepSeekClient(api_key="sk-xxx", model="deepseek-chat")
```

## PPTX → XML 管线

将 PPT 流程图自动转换为工作流 XML：

```python
from src.tools import pptx_to_xml

xml = pptx_to_xml("workflow.pptx", work_dir="output/")
# 中间产物: output/output.pdf, output/images/*.png
# 最终结果: output/workflow.xml
```

分步使用：

```python
from src.tools import pptx_to_pdf, pdf_to_images

pdf = pptx_to_pdf("input.pptx", "output.pdf")
images = pdf_to_images(pdf, "images/", dpi=150)
```

## 配置参考

```python
from src.config import get_config, get_text_llm_config, get_vision_llm_config

cfg = get_config()
print(cfg.text_llm.model)      # deepseek-v4-flash
print(cfg.vision_llm.model)    # Qwen/Qwen3-VL-235B-A22B-Instruct
print(cfg.temp_dir)            # ./tmp
```

## XML 工作流格式

视觉模型输出的 XML 遵循此格式：

```xml
<Workflow>
    <StartNode id="start" name="StartNode">
        <Output><Variable name="user_query" /></Output>
        <NextNode id="llm_1" />
    </StartNode>

    <LLMNode id="llm_1" name="Query Analyzer">
        <Prompt>分析问题: {user_query}</Prompt>
        <Input><Variable name="user_query" /></Input>
        <Output><Variable name="analysis" /></Output>
        <NextNode id="branch" />
    </LLMNode>

    <ConditionBranchNode id="branch" name="Route">
        <Input><Variable name="analysis" /></Input>
        <Classes>
            <Class name="Simple">
                <Description>简单问题</Description>
                <NextNode id="simple_handler" />
            </Class>
        </Classes>
        <DefaultClass>
            <Name>Complex</Name>
            <NextNode id="complex_handler" />
        </DefaultClass>
    </ConditionBranchNode>

    <EndNode id="end" name="EndNode">
        <Input><Variable name="final_answer" /></Input>
    </EndNode>
</Workflow>
```

## 测试

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

## 注意事项

- PowerPoint COM 自动化仅 Windows 可用；跨平台可改用 LibreOffice
- 视觉模型 API 有图片尺寸限制（ModelScope 限制 2048×2048），`VisionLLMClient` 会自动缩放
- `.env` 和 `tmp/` 已在 `.gitignore` 中排除
- 所有示例代码使用 `sys.path.insert(0, ...)` 确保从项目根导入
