import os
import logging
from typing import Optional
from PyPDF2 import PdfReader
import docx

logger = logging.getLogger("resume_parser")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

def extract_text_from_pdf(file_path: str) -> str:
    logger.info(f"Attempting to extract text from PDF file: {file_path}")
    text = []
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            logger.info(f"PDF opened successfully. Total pages found: {len(reader.pages)}")
            for idx, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
                    logger.info(f"Extracted {len(page_text) if page_text else 0} characters from page {idx + 1}")
                except Exception as page_err:
                    logger.error(f"Error extracting text from page {idx + 1}: {page_err}")
    except Exception as e:
        logger.error(f"Failed to extract PDF text from {file_path}: {e}", exc_info=True)
        return ""
    return '\n'.join(text)


def extract_text_from_docx(file_path: str) -> str:
    logger.info(f"Attempting to extract text from DOCX file: {file_path}")
    try:
        document = docx.Document(file_path)
        paragraphs = [p.text for p in document.paragraphs if p.text]
        logger.info(f"DOCX opened successfully. Extracted {len(paragraphs)} paragraphs.")
        return '\n'.join(paragraphs)
    except Exception as e:
        logger.error(f"Failed to extract DOCX text from {file_path}: {e}", exc_info=True)
        return ""


def parse_resume(file_path: str) -> Optional[str]:
    if not os.path.exists(file_path):
        logger.error(f"File path does not exist: {file_path}")
        return ""
        
    extension = os.path.splitext(file_path)[1].lower()
    logger.info(f"Detecting file type for parser: extension='{extension}'")
    
    extracted_text = ""
    if extension == '.pdf':
        extracted_text = extract_text_from_pdf(file_path)
    elif extension in ['.docx', '.doc']:
        extracted_text = extract_text_from_docx(file_path)
    else:
        logger.info(f"Treating file as plain text: '{file_path}'")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                extracted_text = file.read()
        except Exception as e:
            logger.error(f"Failed to read plain text file {file_path}: {e}", exc_info=True)
            extracted_text = ""
            
    if not extracted_text.strip():
        logger.warning(f"Resume text extraction returned empty content for: {file_path}")
    else:
        logger.info(f"Successfully extracted {len(extracted_text)} characters of resume content.")
        
    return extracted_text
