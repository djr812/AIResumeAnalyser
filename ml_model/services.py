from .models import ResumePredictor
from .train_model import predict_resume_match
import re
import os
import openai
from docx import Document
from docx.shared import Inches
import io
import requests
import json

def extract_skills_from_text(text):
    """Extract skills from text using common patterns."""
    # Common programming languages and technologies
    common_skills = [
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php',
        'html', 'css', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'react', 'angular',
        'vue', 'node', 'django', 'flask', 'spring', 'tensorflow', 'pytorch',
        'machine learning', 'deep learning', 'ai', 'artificial intelligence',
        'data science', 'big data', 'hadoop', 'spark', 'scala', 'r',
        'git', 'agile', 'scrum', 'devops', 'ci/cd', 'jenkins', 'linux',
        'unix', 'windows', 'macos', 'ios', 'android', 'mobile development',
        'web development', 'frontend', 'backend', 'full stack', 'cloud',
        'security', 'cybersecurity', 'networking', 'blockchain', 'iot'
    ]
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Find all skills in the text
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill)
    
    return ', '.join(found_skills)

def predict_resume_success(resume_text, job_description):
    """Predict if a resume will be successful for a given job description."""
    # Get the active model
    model_record = ResumePredictor.objects.filter(is_active=True).first()
    if not model_record:
        return None, "No active model found. Please train the model first."
    
    try:
        # Extract skills from resume text
        skills = extract_skills_from_text(resume_text)
        
        # Get the model
        model = model_record.get_model()
        if not model:
            return None, "Error loading model."
        
        # Make prediction
        probability = predict_resume_match(skills, job_description, model)
        
        # Determine confidence level
        if probability > 0.7:
            confidence = 'High'
        elif probability > 0.4:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        # Convert skills string to list and clean up
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        return {
            'probability': probability,
            'confidence': confidence,
            'skills_found': skills_list
        }, None
        
    except Exception as e:
        return None, f"Error making prediction: {str(e)}"

def analyze_keywords(resume_text, job_description):
    """
    Analyze keywords in resume and job description to generate heatmap data.
    Returns a dictionary with keyword relevance scores and section analysis.
    """
    # Common resume sections to look for
    sections = {
        'summary': ['summary', 'profile', 'objective'],
        'experience': ['experience', 'work history', 'employment'],
        'education': ['education', 'academic', 'qualification'],
        'skills': ['skills', 'technical skills', 'competencies'],
        'projects': ['projects', 'portfolio', 'achievements']
    }
    
    # Extract keywords from both texts
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)
    
    # Initialize section data
    section_data = {section: {'keywords': [], 'score': 0} for section in sections}
    
    # Split resume into sections
    resume_sections = {}
    current_section = 'other'
    lines = resume_text.lower().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line indicates a new section
        for section, keywords in sections.items():
            if any(keyword in line for keyword in keywords):
                current_section = section
                break
        
        if current_section not in resume_sections:
            resume_sections[current_section] = []
        resume_sections[current_section].append(line)
    
    # Analyze each section
    for section, content in resume_sections.items():
        section_text = ' '.join(content)
        section_keywords = extract_keywords(section_text)
        
        # Find matching keywords
        matching_keywords = []
        for keyword in job_keywords:
            if keyword in section_keywords:
                matching_keywords.append({
                    'keyword': keyword,
                    'count': section_keywords.count(keyword),
                    'relevance': 1.0  # Full relevance for exact matches
                })
        
        # Calculate section score
        section_score = len(matching_keywords) / len(job_keywords) if job_keywords else 0
        
        if section in section_data:
            section_data[section]['keywords'] = matching_keywords
            section_data[section]['score'] = section_score
    
    # Generate overall keyword relevance
    keyword_relevance = []
    for keyword in job_keywords:
        relevance = {
            'keyword': keyword,
            'found': False,
            'sections': []
        }
        
        for section, data in section_data.items():
            if any(k['keyword'] == keyword for k in data['keywords']):
                relevance['found'] = True
                relevance['sections'].append({
                    'name': section,
                    'count': next(k['count'] for k in data['keywords'] if k['keyword'] == keyword)
                })
        
        keyword_relevance.append(relevance)
    
    return {
        'section_analysis': section_data,
        'keyword_relevance': keyword_relevance,
        'resume_keywords': {k: resume_keywords.count(k) for k in set(resume_keywords)},
        'job_keywords': {k: job_keywords.count(k) for k in set(job_keywords)}
    }

def extract_keywords(text):
    """
    Extract important keywords from text.
    """
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split into words and remove common words
    words = text.split()
    stop_words = set([
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of', 'a', 'an',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
        'mine', 'yours', 'hers', 'ours', 'theirs', 'who', 'whom', 'whose', 'which', 'what',
        'where', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    ])
    
    # Filter out stop words and short words
    words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top keywords (words that appear more than once)
    return [word for word, freq in word_freq.items() if freq > 1]

def generate_improved_resume(resume_text, job_description):
    """
    Generate an improved version of the resume using Ollama's Llama3.3 model.
    Returns the improved resume text and a list of changes made.
    """
    prompt = f"""As an expert resume writer, analyze this resume and job description, then create an improved version of the resume that better matches the job requirements. 
    Focus on:
    1. Highlighting relevant skills and experiences
    2. Using keywords from the job description
    3. Improving the overall structure and impact
    4. Maintaining the original information but presenting it more effectively
    
    Original Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Please provide your response in the following format:
    
    IMPROVED RESUME:
    [Your improved resume text here]
    
    CHANGES MADE:
    1. [First change]
    2. [Second change]
    3. [Third change]
    
    EXPLANATION:
    [Your explanation of why these changes improve the match with the job description]"""
    
    try:
        # Call Ollama API
        response = requests.post(
            'http://10.1.1.126:11434/api/generate',
            json={
                'model': 'llama3.1',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 2000
                }
            }
        )
        
        if response.status_code != 200:
            return None, f"Error from Ollama API: {response.text}"
        
        # Parse the response
        result = response.json()
        content = result['response']
        
        # Split the response into sections
        sections = content.split('\n\n')
        improved_resume = ""
        changes = []
        
        current_section = None
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if section.startswith('IMPROVED RESUME:'):
                current_section = 'resume'
                continue
            elif section.startswith('CHANGES MADE:'):
                current_section = 'changes'
                continue
            elif section.startswith('EXPLANATION:'):
                current_section = 'explanation'
                continue
                
            if current_section == 'resume':
                improved_resume += section + '\n\n'
            elif current_section == 'changes':
                # Extract numbered changes
                if section.startswith(('1.', '2.', '3.', '4.', '5.')):
                    changes.append(section[2:].strip())
            elif current_section == 'explanation':
                changes.append(section)
        
        if not improved_resume:
            return None, "Failed to generate improved resume"
            
        return improved_resume.strip(), changes
        
    except Exception as e:
        return None, f"Error generating improved resume: {str(e)}"

def create_pdf_from_text(text, filename):
    """
    Create a PDF file from the given text.
    Returns the PDF file as bytes.
    """
    try:
        # Create a new Word document
        doc = Document()
        
        # Add the text
        doc.add_paragraph(text)
        
        # Save to a bytes buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except Exception as e:
        return None, f"Error creating PDF: {str(e)}" 