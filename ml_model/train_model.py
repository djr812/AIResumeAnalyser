import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
import joblib
import os
from django.conf import settings
from .utils import extract_skills_from_text

def preprocess_data(df):
    """Preprocess the dataset for training."""
    # Convert skills to string and handle NaN values
    df['Skills'] = df['Skills'].fillna('')
    
    # Convert target variable to binary
    df['Target'] = (df['Recruiter Decision'] == 'Hire').astype(int)
    
    # Create feature set
    features = pd.DataFrame()
    
    # Text features
    features['skills'] = df['Skills']
    
    # Numerical features
    features['experience'] = df['Experience (Years)']
    features['projects'] = df['Projects Count']
    features['salary'] = df['Salary Expectation ($)']
    
    # Handle missing values in numerical features
    features['experience'] = features['experience'].fillna(features['experience'].median())
    features['projects'] = features['projects'].fillna(features['projects'].median())
    features['salary'] = features['salary'].fillna(features['salary'].median())
    
    return features, df['Target']

def train_model(dataset_path):
    """Train the model using the dataset."""
    # Load and preprocess data
    df = pd.read_csv(dataset_path)
    X, y = preprocess_data(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create preprocessing steps
    text_features = ['skills']
    numeric_features = ['experience', 'projects', 'salary']
    
    # Create column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('text', TfidfVectorizer(max_features=1000), 'skills'),
            ('num', StandardScaler(), numeric_features)
        ])
    
    # Create pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Train model
    pipeline.fit(X_train, y_train)
    
    # Calculate accuracy
    accuracy = pipeline.score(X_test, y_test)
    
    # Save model
    model_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'resume_predictor.joblib')
    joblib.dump(pipeline, model_path)
    
    return accuracy, model_path

def predict_resume_match(resume_text, job_description, model):
    """Predict if a resume matches a job description."""
    # Extract skills from both resume and job description
    resume_skills = extract_skills_from_text(resume_text)
    job_skills = extract_skills_from_text(job_description)
    
    # Calculate skill match percentage
    resume_skill_list = set(resume_skills.lower().split(', '))
    job_skill_list = set(job_skills.lower().split(', '))
    
    # Calculate how many required skills are present
    matching_skills = resume_skill_list.intersection(job_skill_list)
    skill_match_ratio = len(matching_skills) / len(job_skill_list) if job_skill_list else 0
    
    # Preprocess input
    features = pd.DataFrame({
        'skills': [resume_skills],
        'experience': [len(resume_text.split()) / 100],  # Rough estimate based on text length
        'projects': [resume_text.lower().count('project')],  # Count project mentions
        'salary': [0]  # This would need to be extracted from the resume
    })
    
    # Make prediction
    prediction = model.predict_proba(features)[0]
    
    # Combine model prediction with skill match ratio
    final_probability = (prediction[1] + skill_match_ratio) / 2
    
    return final_probability  # Return combined probability 