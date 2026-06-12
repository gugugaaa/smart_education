# Draw2XML

将流程图 PPT/PPTX/PDF 自动转换为工作流 XML。

## 触发条件

用户要求将流程图、PPT、PPTX 或 PDF 中的工作流图表"转换为 XML"、"提取为工作流"、"解析流程图"时触发。

## 使用方式

```python
from src.tools import pptx_to_xml

xml = pptx_to_xml(
    "input.pptx",           # 支持 .pptx / .ppt / .pdf
    work_dir="output/",     # 中间产物目录
    dpi=150                 # 渲染分辨率
)
```

环境要求详见本文末尾。

## 执行流程

```
PPTX ──[PowerPoint COM]──→ PDF ──[PyMuPDF]──→ PNG ──[Vision LLM]──→ XML
```

1. **PPTX → PDF**：调用 PowerPoint COM 自动化打印为 PDF（Windows only）
2. **PDF → PNG**：PyMuPDF 逐页渲染为图片（默认 150 DPI）
3. **PNG → XML**：视觉模型分析流程图，按规范输出 XML（图片超过 2048px 自动缩放）

中间产物（PDF、PNG）保留在 `work_dir` 便于检查。

## 分步调用

```python
from src.tools import pptx_to_pdf, pdf_to_images
from src.llm.vision_client import VisionLLMClient

# 1. 转 PDF
pdf = pptx_to_pdf("input.pptx", "output.pdf")

# 2. 渲染图片
images = pdf_to_images(pdf, "images/", dpi=150)

# 3. 视觉分析
client = VisionLLMClient()
xml = client.analyze(images[0], prompt="...", system_prompt="...")
```

## XML 输出格式

视觉模型按以下 schema 输出，支持 4 种节点类型：

```xml
<Workflow>
    <!-- 开始节点 -->
    <StartNode id="start" name="节点名称">
        <Output><Variable name="变量名" /></Output>
        <NextNode id="下一节点ID" />
    </StartNode>

    <!-- LLM 交互节点 -->
    <LLMNode id="llm_1" name="节点名称">
        <Prompt>系统提示词，使用 {变量名} 引用上下文</Prompt>
        <Input><Variable name="输入变量" /></Input>
        <Output><Variable name="输出变量" /></Output>
        <NextNode id="下一节点ID" />
    </LLMNode>

    <!-- 条件分支（菱形决策节点） -->
    <ConditionBranchNode id="branch" name="节点名称">
        <Input><Variable name="输入变量" /></Input>
        <Classes>
            <Class name="分支名">
                <Description>匹配条件描述</Description>
                <NextNode id="匹配时跳转ID" />
            </Class>
        </Classes>
        <DefaultClass>
            <Name>默认分支名</Name>
            <NextNode id="兜底跳转ID" />
        </DefaultClass>
    </ConditionBranchNode>

    <!-- 结束节点 -->
    <EndNode id="end" name="节点名称">
        <Input><Variable name="结果变量" /></Input>
    </EndNode>
</Workflow>
```

所有节点必需属性：`id`（唯一标识）、`name`（显示名称）。

## 视觉模型 Prompt

```python
SYSTEM_PROMPT = """你是一个专业的流程图转译专家。将图片中的工作流流程图逐字逐句转换为 XML。

规则：
1. 只描述图中实际内容，不编造
2. 逐字读取节点文字
3. 按箭头/连线确定连接关系
4. 变量名使用英文 snake_case
5. 只输出 XML，不要解释"""
```

## 环境依赖

**.env 配置：**

```env
VISION_LLM_PROVIDER=openai
VISION_LLM_API_KEY=
VISION_LLM_BASE_URL=https://api-inference.modelscope.cn/v1
VISION_LLM_MODEL=Qwen/Qwen3-VL-235B-A22B-Instruct
```

**Python 依赖：**

```
openai>=1.0.0
PyMuPDF>=1.24.0
python-pptx>=1.0.0
pywin32>=300
Pillow
socksio
```

安装：`uv pip install <packages>`
