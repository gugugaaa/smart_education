"""
PDF → 图片提取工具，使用 PyMuPDF 渲染每页为 PNG。
"""
import os
from pathlib import Path


def pdf_to_images(
    pdf_path: str,
    output_dir: str,
    dpi: int = 200,
    prefix: str = "page",
    fmt: str = "png",
) -> list[str]:
    """
    将 PDF 的每一页渲染为图片。

    Args:
        pdf_path: PDF 文件路径。
        output_dir: 图片输出目录。
        dpi: 渲染分辨率，默认 200。
        prefix: 图片文件名前缀。
        fmt: 图片格式，默认 png。

    Returns:
        生成的图片路径列表，按页码排序。

    Raises:
        FileNotFoundError: PDF 文件不存在。
        RuntimeError: 渲染失败。
    """
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    os.makedirs(output_dir, exist_ok=True)

    import fitz

    image_paths = []

    try:
        doc = fitz.open(pdf_path)
        total = len(doc)

        for i in range(total):
            page = doc[i]
            # 使用 matrix 控制 DPI
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            filename = f"{prefix}_{i + 1:0{len(str(total))}d}.{fmt}"
            filepath = os.path.join(output_dir, filename)
            pix.save(filepath)
            image_paths.append(filepath)

            size_kb = os.path.getsize(filepath) / 1024
            print(f"  [{i + 1}/{total}] {filename} ({pix.width}x{pix.height}, {size_kb:.0f} KB)")

        doc.close()
        print(f"  已导出 {len(image_paths)} 张图片到: {output_dir}")
        return image_paths

    except Exception as e:
        raise RuntimeError(f"PDF→图片 转换失败: {e}") from e
