import os
from typing import Optional
from PyPDF2 import PdfReader
import docx


def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return '\n'.join(text)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return '\n'.join(paragraph.text for paragraph in doc.paragraphs)


def parse_resume(file_path: str) -> Optional[str]:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == '.pdf':
        return extract_text_from_pdf(file_path)
    if extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()
