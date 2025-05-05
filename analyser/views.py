import pdfplumber
import docx
from django.shortcuts import render
from .forms import ResumeForm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Parse PDF resume
def parse_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ' '.join([page.extract_text() for page in pdf.pages])
    return text

# Parse DOCX resume
def parse_docx(file):
    doc = docx.Document(file)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

# View to handle form and processing
def index(request):
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume']
            job_description = form.cleaned_data['job_description']
            
            # Parse the resume based on file type
            if resume_file.name.endswith('.pdf'):
                resume_text = parse_pdf(resume_file)
            elif resume_file.name.endswith('.docx'):
                resume_text = parse_docx(resume_file)
            else:
                return render(request, 'analyser/index.html', {'form': form, 'error': 'Unsupported file format'})
            
            # Perform TF-IDF comparison
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform([resume_text, job_description])
            score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            # Here you can add logic for keyword extraction, suggestions, etc.
            return render(request, 'analyser/result.html', {'score': score, 'resume_text': resume_text, 'job_description': job_description})
    else:
        form = ResumeForm()
    
    return render(request, 'analyser/index.html', {'form': form})


