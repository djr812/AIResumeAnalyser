from .models import ResumePredictor
from .train_model import predict_resume_match
import re

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
        
        return {
            'probability': probability,
            'confidence': confidence,
            'skills_found': skills
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
    
    # Extract keywords from job description
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
        'job_keywords': job_keywords
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
    stop_words = set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of', 'a', 'an'])
    words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top keywords (words that appear more than once)
    return [word for word, freq in word_freq.items() if freq > 1] 