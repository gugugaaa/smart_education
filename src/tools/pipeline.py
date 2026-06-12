"""
完整管线：PPTX/PPT/PDF → 图片 → 视觉模型 → XML。
"""
import os
import tempfile
from pathlib import Path

from .pptx_to_pdf import pptx_to_pdf
from .pdf_to_images import pdf_to_images


VISION_SYSTEM_PROMPT = """你是一个专业的流程图转译专家。你的任务是把图片中的工作流流程图，逐字逐句、忠实准确地转换为 XML。

核心原则：
1. 只描述图中实际出现的内容，不要编造或替换
2. 逐字读取图中每个节点的标题文字、描述文字
3. 按箭头方向和连线确定节点之间的连接关系
4. 变量名使用英文 snake_case

XML 格式：

<Workflow>
    <StartNode id="..." name="从图中读取的节点名称">
        <Output><Variable name="英文变量名" /></Output>
        <NextNode id="..." />
    </StartNode>

    <LLMNode id="..." name="从图中读取的节点名称">
        <Prompt>该节点的描述文字</Prompt>
        <Input><Variable name="..." /></Input>
        <Output><Variable name="..." /></Output>
        <NextNode id="..." />
    </LLMNode>

    <ConditionBranchNode id="..." name="从图中读取的节点名称">
        <Input><Variable name="..." /></Input>
        <Classes>
            <Class name="分支名">
                <Description>分支条件描述</Description>
                <NextNode id="..." />
            </Class>
        </Classes>
        <DefaultClass>
            <Name>默认分支名</Name>
            <NextNode id="..." />
        </DefaultClass>
    </ConditionBranchNode>

    <EndNode id="..." name="从图中读取的节点名称">
        <Input><Variable name="..." /></Input>
    </EndNode>
</Workflow>

输出要求：只输出 XML 文本，不要输出任何解释、说明或 markdown 标记。"""


def pptx_to_xml(
    pptx_path: str,
    work_dir: str | None = None,
    dpi: int = 150,
) -> str:
    """
    完整管线：PPTX/PPT/PDF → 图片 → 视觉模型 → XML。

    Args:
        pptx_path: PPTX、PPT 或 PDF 文件路径。
        work_dir: 工作目录（存放中间文件），默认用系统临时目录。
        dpi: 渲染 DPI，默认 150。

    Returns:
        视觉模型生成的 XML 字符串。
    """
    ext = Path(pptx_path).suffix.lower()
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="smart_edu_")
    os.makedirs(work_dir, exist_ok=True)
    print(f"工作目录: {work_dir}")

    # Step 1: → PDF（如果输入不是 PDF）
    if ext == ".pdf":
        pdf_path = pptx_path
        print(f"输入已是 PDF: {pdf_path}")
    else:
        pdf_path = pptx_to_pdf(pptx_path, os.path.join(work_dir, "output.pdf"))
        print()

    # Step 2: PDF → Images
    img_dir = os.path.join(work_dir, "images")
    image_paths = pdf_to_images(pdf_path, img_dir, dpi=dpi)
    print()

    if not image_paths:
        raise RuntimeError("未生成任何图片")

    # Step 3: Images → XML (vision model)
    from src.llm.vision_client import VisionLLMClient

    client = VisionLLMClient()
    print(f"视觉模型: {client.model}")

    if len(image_paths) == 1:
        xml = client.analyze(
            image_paths[0],
            prompt="请将这张工作流流程图转换为 XML。严格按图中文字，不要编造内容。",
            system_prompt=VISION_SYSTEM_PROMPT,
        )
    else:
        xml = client.analyze_multiple(
            image_paths,
            prompt="请按图片顺序分析这些工作流流程图页面，将其合并转换为一个完整的 XML。严格按图中文字。",
            system_prompt=VISION_SYSTEM_PROMPT,
        )

    # Save XML
    xml_path = os.path.join(work_dir, "workflow.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"\nXML 已保存: {xml_path}")

    return xml
