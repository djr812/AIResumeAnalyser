import os
import docx
import PyPDF2
from django.core.files.storage import FileSystemStorage

def parse_resume(file_path):
    """
    Parse resume content from various file formats (PDF, DOCX, TXT)
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return parse_pdf(file_path)
        elif file_extension == '.docx':
            return parse_docx(file_path)
        elif file_extension == '.txt':
            return parse_txt(file_path)
        else:
            raise ValueError(f'Unsupported file format: {file_extension}')
            
    except Exception as e:
        raise Exception(f'Error parsing resume: {str(e)}')

def parse_pdf(file_path):
    """Parse PDF file content"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text.strip()
    except Exception as e:
        raise Exception(f'Error parsing PDF: {str(e)}')

def parse_docx(file_path):
    """Parse DOCX file content"""
    try:
        doc = docx.Document(file_path)
        text = ''
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
        return text.strip()
    except Exception as e:
        raise Exception(f'Error parsing DOCX: {str(e)}')

def parse_txt(file_path):
    """Parse TXT file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        raise Exception(f'Error parsing TXT: {str(e)}')

def calculate_tfidf_score(resume_text, job_description):
    """
    Calculate TF-IDF score between resume and job description
    """
    # This is a placeholder for the actual TF-IDF calculation
    # You would typically use scikit-learn or similar for this
    return 0.75  # Placeholder score 