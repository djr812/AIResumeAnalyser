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
        return {'error': "No active model found. Please train the model first."}
    
    try:
        # Extract skills from resume text
        skills = extract_skills_from_text(resume_text)
        
        # Get the model
        model = model_record.get_model()
        if not model:
            return {'error': "Error loading model."}
        
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
        
        # Generate section evaluations
        prompt = f"""As an expert resume writer, analyze this resume and job description, then provide a comprehensive evaluation of each section.

        Original Resume:
        {resume_text}
        
        Job Description:
        {job_description}
        
        Please provide your response in EXACTLY the following format, with each section having its own strengths, improvements, and recommendations:

        SECTION EVALUATION:
        Summary/Objective (Score: X/10):
        - Strengths: 
          * [First strength]
          * [Second strength]
          * [Third strength]
        - Areas for Improvement: 
          * [First improvement]
          * [Second improvement]
          * [Third improvement]
        - Recommendations: 
          * [First recommendation]
          * [Second recommendation]
          * [Third recommendation]
        
        Experience (Score: X/10):
        - Strengths: 
          * [First strength]
          * [Second strength]
          * [Third strength]
        - Areas for Improvement: 
          * [First improvement]
          * [Second improvement]
          * [Third improvement]
        - Recommendations: 
          * [First recommendation]
          * [Second recommendation]
          * [Third recommendation]
        
        Skills (Score: X/10):
        - Strengths: 
          * [First strength]
          * [Second strength]
          * [Third strength]
        - Areas for Improvement: 
          * [First improvement]
          * [Second improvement]
          * [Third improvement]
        - Recommendations: 
          * [First recommendation]
          * [Second recommendation]
          * [Third recommendation]
        
        Education (Score: X/10):
        - Strengths: 
          * [First strength]
          * [Second strength]
          * [Third strength]
        - Areas for Improvement: 
          * [First improvement]
          * [Second improvement]
          * [Third improvement]
        - Recommendations: 
          * [First recommendation]
          * [Second recommendation]
          * [Third recommendation]
        
        Projects/Achievements (Score: X/10):
        - Strengths: 
          * [First strength]
          * [Second strength]
          * [Third strength]
        - Areas for Improvement: 
          * [First improvement]
          * [Second improvement]
          * [Third improvement]
        - Recommendations: 
          * [First recommendation]
          * [Second recommendation]
          * [Third recommendation]
        
        Overall Resume Score: X/10"""
        
        # Call Ollama API for section evaluations
        response = requests.post(
            'http://10.1.1.126:11434/api/generate',
            json={
                'model': 'llama3.1',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 4000
                }
            }
        )
        
        if response.status_code != 200:
            return {'error': f"Error from Ollama API: {response.text}"}
        
        # Parse the response
        result = response.json()
        content = result['response']
        
        print("\n=== API Response ===")
        print(content)
        print("=== End API Response ===\n")
        
        # Parse section evaluations
        section_evaluations = {}
        current_section = None
        current_evaluation = None
        current_category = None
        
        # Split content into sections first
        sections = content.split('\n\n')
        print("\n=== Processing Sections ===")
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            print(f"\nProcessing section:\n{section}")
            
            # Check for section headers with scores
            if '**' in section and '(' in section and 'Score:' in section:
                section_name = section.split('(')[0].strip()
                score = section.split('(')[1].split('/')[0].strip()
                current_section = section_name
                current_evaluation = {
                    'score': score,
                    'strengths': [],
                    'improvements': [],
                    'recommendations': []
                }
                section_evaluations[section_name] = current_evaluation
                print(f"\nFound section: {section_name} with score {score}")
                continue
            elif 'Overall Resume Score:' in section:
                # Handle overall score section
                score = section.split(':')[1].strip()
                current_section = 'Overall Resume Score'
                current_evaluation = {
                    'score': score,
                    'strengths': [],
                    'improvements': [],
                    'recommendations': []
                }
                section_evaluations[current_section] = current_evaluation
                print(f"\nFound section: {current_section} with score {score}")
                continue
            
            # Process the section content
            lines = section.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                print(f"\nProcessing line: {line}")
                
                # Check for category headers
                if 'Strengths:' in line:
                    current_category = 'strengths'
                    print("Found Strengths category")
                    continue
                elif 'Areas for Improvement:' in line:
                    current_category = 'improvements'
                    print("Found Improvements category")
                    continue
                elif 'Recommendations:' in line:
                    current_category = 'recommendations'
                    print("Found Recommendations category")
                    continue
                
                # Add content to current category if we have one
                if current_category and current_evaluation and line:
                    # Remove any leading dashes, asterisks, or numbers
                    line = re.sub(r'^[-•*\d\.\s+]+', '', line).strip()
                    if line and not line.startswith('[') and not line.endswith(']'):  # Only add non-empty, non-template lines
                        if current_category == 'strengths':
                            current_evaluation['strengths'].append(line)
                        elif current_category == 'improvements':
                            current_evaluation['improvements'].append(line)
                        elif current_category == 'recommendations':
                            current_evaluation['recommendations'].append(line)
                        print(f"Added to {current_category}: {line}")
        
        print("\n=== Final Section Evaluations ===")
        print(json.dumps(section_evaluations, indent=2))
        print("=== End Final Section Evaluations ===\n")
        
        return {
            'prediction': probability,
            'confidence': confidence,
            'skills_found': skills_list,
            'section_evaluations': section_evaluations
        }
        
    except Exception as e:
        print("Error in predict_resume_success:", str(e))  # Debug print
        return {'error': f"Error making prediction: {str(e)}"}

def analyze_keywords(resume_text, job_description):
    """
    Analyze keywords in resume and job description to generate detailed matching analysis.
    Returns a dictionary with keyword relevance scores, section analysis, and matching details.
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
    
    # Track matched and missing keywords
    matched_keywords = []
    missing_keywords = []
    
    # Analyze each section
    for section, content in resume_sections.items():
        section_text = ' '.join(content)
        section_keywords = extract_keywords(section_text)
        
        # Find matching keywords
        matching_keywords = []
        for keyword in job_keywords:
            if keyword in section_keywords:
                count = section_keywords.count(keyword)
                matching_keywords.append({
                    'keyword': keyword,
                    'count': count,
                    'relevance': 1.0  # Full relevance for exact matches
                })
                
                # Add to matched keywords if not already there
                if not any(k['keyword'] == keyword for k in matched_keywords):
                    matched_keywords.append({
                        'keyword': keyword,
                        'sections': [{
                            'name': section,
                            'count': count
                        }]
                    })
                else:
                    # Add section to existing matched keyword
                    for k in matched_keywords:
                        if k['keyword'] == keyword:
                            k['sections'].append({
                                'name': section,
                                'count': count
                            })
        
        # Calculate section score
        section_score = len(matching_keywords) / len(job_keywords) if job_keywords else 0
        
        if section in section_data:
            section_data[section]['keywords'] = matching_keywords
            section_data[section]['score'] = section_score
    
    # Find missing keywords
    missing_keywords = [keyword for keyword in job_keywords 
                       if not any(k['keyword'] == keyword for k in matched_keywords)]
    
    # Calculate overall match percentage
    match_percentage = (len(matched_keywords) / len(job_keywords) * 100) if job_keywords else 0
    
    return {
        'section_analysis': section_data,
        'matched_keywords': matched_keywords,
        'missing_keywords': missing_keywords,
        'match_percentage': round(match_percentage, 1),
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
    Generate an improved version of the resume using Ollama's Llama3.1 model.
    Returns the improved resume text, changes made, and section evaluations.
    """
    prompt = f"""As an expert resume writer, analyze this resume and job description, then provide a comprehensive evaluation and improved version.

    Original Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Please provide your response in EXACTLY the following format:

    === SECTION EVALUATION ===
    **Summary/Objective (Score: X/10)**
    - Strengths: 
      * [First strength]
      * [Second strength]
    - Areas for Improvement: 
      * [First improvement]
      * [Second improvement]
    - Recommendations: 
      * [First recommendation]
      * [Second recommendation]
    
    **Experience (Score: X/10)**
    - Strengths: 
      * [First strength]
      * [Second strength]
    - Areas for Improvement: 
      * [First improvement]
      * [Second improvement]
    - Recommendations: 
      * [First recommendation]
      * [Second recommendation]
    
    **Skills (Score: X/10)**
    - Strengths: 
      * [First strength]
      * [Second strength]
    - Areas for Improvement: 
      * [First improvement]
      * [Second improvement]
    - Recommendations: 
      * [First recommendation]
      * [Second recommendation]
    
    **Education (Score: X/10)**
    - Strengths: 
      * [First strength]
      * [Second strength]
    - Areas for Improvement: 
      * [First improvement]
      * [Second improvement]
    - Recommendations: 
      * [First recommendation]
      * [Second recommendation]
    
    **Projects/Achievements (Score: X/10)**
    - Strengths: 
      * [First strength]
      * [Second strength]
    - Areas for Improvement: 
      * [First improvement]
      * [Second improvement]
    - Recommendations: 
      * [First recommendation]
      * [Second recommendation]
    
    Overall Resume Score: X/10

    === CHANGES MADE ===
    Please list at least 5 specific changes that should be made to improve the resume for this job:
    1. [First specific change]
    2. [Second specific change]
    3. [Third specific change]
    4. [Fourth specific change]
    5. [Fifth specific change]

    === IMPROVED RESUME ===
    [Provide a complete, improved version of the resume that addresses the recommendations above. Include all sections: Profile, Experience, Education, Skills, and any other relevant sections. Make sure to tailor the content to match the job description requirements.]

    === EXPLANATION ===
    [Explain why these changes improve the match with the job description and how they address the identified areas for improvement]
    """
    
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
                    'num_predict': 4000  # Increased for more detailed response
                }
            }
        )
        
        if response.status_code != 200:
            return None, f"Error from Ollama API: {response.text}"
        
        # Parse the response
        result = response.json()
        content = result['response']
        
        print("\n=== API Response ===")
        print(content)
        print("=== End API Response ===\n")
        
        # Split the response into sections
        sections = content.split('===')
        improved_resume = ""
        changes = []
        section_evaluations = {}
        current_section = None
        current_evaluation = {}
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            if 'SECTION EVALUATION' in section:
                # Parse section evaluations
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if '**' in line and '(' in line:
                        # Extract section name and score
                        section_name = line.split('(')[0].strip()
                        section_name = section_name.replace('**', '').strip()
                        score = line.split('(')[1].split('/')[0].strip()
                        current_section = section_name
                        current_evaluation = {
                            'score': score,
                            'strengths': [],
                            'improvements': [],
                            'recommendations': []
                        }
                        section_evaluations[current_section] = current_evaluation
                    elif '- Strengths:' in line:
                        current_category = 'strengths'
                    elif '- Areas for Improvement:' in line:
                        current_category = 'improvements'
                    elif '- Recommendations:' in line:
                        current_category = 'recommendations'
                    elif line.startswith('*'):
                        content = re.sub(r'^\*\s*', '', line).strip()
                        if content and not content.startswith('[') and not content.endswith(']'):
                            if current_section and current_category:
                                current_evaluation[current_category].append(content)
            elif 'CHANGES MADE' in section:
                # Process changes section
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                        change = re.sub(r'^\d+\.\s*', '', line).strip()
                        if change and not change.startswith('[') and not change.endswith(']'):
                            changes.append(change)
            elif 'IMPROVED RESUME' in section:
                # Extract improved resume
                improved_resume = section.replace('IMPROVED RESUME', '').strip()
            elif 'EXPLANATION' in section:
                # Add explanation as additional context
                explanation = section.replace('EXPLANATION', '').strip()
                if explanation and not explanation.startswith('[') and not explanation.endswith(']'):
                    changes.append(explanation)
        
        if not improved_resume:
            return None, "Failed to generate improved resume"
            
        print("\n=== Final Section Evaluations ===")
        print(json.dumps(section_evaluations, indent=2))
        print("=== End Final Section Evaluations ===\n")
        
        print("\n=== Final Changes ===")
        print(json.dumps(changes, indent=2))
        print("=== End Final Changes ===\n")
        
        return {
            'improved_resume': improved_resume.strip(),
            'changes': changes,
            'section_evaluations': section_evaluations
        }
        
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