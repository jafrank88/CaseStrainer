import os
import logging

logger = logging.getLogger(__name__)

try:
    from pdf_handler import extract_text_from_pdf
except ImportError:
    extract_text_from_pdf = None


def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    logger.info(f"Extracting text from file: {file_path}")
    file_ext = os.path.splitext(file_path)[1].lower()
    try:
        if file_ext == ".pdf":
            if extract_text_from_pdf:
                return extract_text_from_pdf(file_path)
            else:
                try:
                    import PyPDF2

                    with open(file_path, "rb") as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                    logger.info("Successfully extracted text using PyPDF2")
                    return text
                except ImportError:
                    logger.error("PyPDF2 not installed")
                    return "Error: PyPDF2 not installed. Cannot extract text from PDF."
        elif file_ext in [".doc", ".docx"]:
            try:
                import docx

                doc = docx.Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error(
                    "python-docx not installed. Cannot extract text from Word documents."
                )
                return "Error: python-docx not installed. Cannot extract text from Word documents."
        elif file_ext == ".rtf":
            try:
                from striprtf.striprtf import rtf_to_text

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    return rtf_to_text(file.read())
            except ImportError:
                logger.error(
                    "striprtf not installed. Cannot extract text from RTF documents."
                )
                return "Error: striprtf not installed. Cannot extract text from RTF documents."
        elif file_ext in [".html", ".htm"]:
            try:
                from bs4 import BeautifulSoup

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file.read(), "html.parser")
                    return soup.get_text()
            except ImportError:
                logger.error(
                    "BeautifulSoup not installed. Cannot extract text from HTML documents."
                )
                return "Error: BeautifulSoup not installed. Cannot extract text from HTML documents."
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as file:
                    return file.read()
    except Exception as e:
        logger.error(f"Error extracting text from file: {e}")
        return ""
