from __future__ import annotations

from io import BytesIO
from typing import List
from zipfile import BadZipFile

from docx import Document
from pypdf import PdfReader


class ResumeFileParserService:
    def extract_text(self, filename: str, content: bytes) -> str:
        normalized = (filename or "").strip().lower()
        if normalized.endswith(".pdf"):
            return self._extract_pdf_text(content)
        if normalized.endswith(".docx"):
            return self._extract_docx_text(content)
        raise ValueError("仅支持 PDF 或 DOCX 简历文件")

    def _extract_pdf_text(self, content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        texts: List[str] = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        combined = "\n".join(texts).strip()
        if not combined:
            raise ValueError("PDF 未提取到可用文本，请尝试内容更清晰的文件")
        return combined

    def _extract_docx_text(self, content: bytes) -> str:
        try:
            document = Document(BytesIO(content))
        except BadZipFile:
            raise ValueError("DOCX 文件无法解析，请确认文件未损坏")
        lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        combined = "\n".join(lines).strip()
        if not combined:
            raise ValueError("DOCX 未提取到可用文本，请确认文件包含正文")
        return combined
