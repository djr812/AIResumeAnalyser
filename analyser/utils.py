import pdfplumber
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def parse_resume(file):
    """Parse resume based on file type."""
    if file.name.endswith('.pdf'):
        return parse_pdf(file)
    elif file.name.endswith('.docx'):
        return parse_docx(file)
    else:
        raise ValueError('Unsupported file format. Please upload a PDF or DOCX file.')

def parse_pdf(file):
    """Parse PDF resume."""
    with pdfplumber.open(file) as pdf:
        text = ' '.join([page.extract_text() for page in pdf.pages])
    return text

def parse_docx(file):
    """Parse DOCX resume."""
    doc = docx.Document(file)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def calculate_tfidf_score(resume_text, job_description):
    """Calculate TF-IDF similarity score between resume and job description."""
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([resume_text, job_description])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return score 