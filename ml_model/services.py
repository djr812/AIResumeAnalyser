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
        
        return {
            'probability': probability,
            'confidence': 'High' if probability > 0.7 else 'Medium' if probability > 0.4 else 'Low',
            'skills_found': skills
        }, None
        
    except Exception as e:
        return None, f"Error making prediction: {str(e)}" 