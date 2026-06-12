"""
PPTX → PDF 转换工具，使用 PowerPoint COM 自动化。
"""
import os
import time
from pathlib import Path


def pptx_to_pdf(pptx_path: str, pdf_path: str | None = None, timeout: int = 120) -> str:
    """
    将 PPTX 文件转换为 PDF。

    Args:
        pptx_path: PPTX 文件路径。
        pdf_path: 输出 PDF 路径，为 None 时自动生成（同目录同名 .pdf）。
        timeout: 转换超时秒数。

    Returns:
        生成的 PDF 文件路径。

    Raises:
        FileNotFoundError: PPTX 文件不存在。
        RuntimeError: 转换失败。
    """
    pptx_path = os.path.abspath(pptx_path)
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX 文件不存在: {pptx_path}")

    if pdf_path is None:
        pdf_path = str(Path(pptx_path).with_suffix(".pdf"))
    pdf_path = os.path.abspath(pdf_path)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(pdf_path) or ".", exist_ok=True)

    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    powerpoint = None

    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = True  # 最小化窗口

        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)

        start = time.time()
        # ppFixedFormatTypePDF = 2
        presentation.SaveAs(pdf_path, 32)
        elapsed = time.time() - start

        if elapsed > timeout:
            print(f"  警告: 转换耗时 {elapsed:.1f}s，超过预期 {timeout}s")

        presentation.Close()

        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF 输出文件未生成")

        print(f"  已生成 PDF: {pdf_path} ({os.path.getsize(pdf_path) / 1024:.0f} KB, {elapsed:.1f}s)")
        return pdf_path

    except Exception as e:
        raise RuntimeError(f"PPTX→PDF 转换失败: {e}") from e

    finally:
        if powerpoint is not None:
            try:
                powerpoint.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
