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
    # Preprocess input
    features = pd.DataFrame({
        'skills': [resume_text],
        'experience': [0],  # These would need to be extracted from the resume
        'projects': [0],    # These would need to be extracted from the resume
        'salary': [0]       # These would need to be extracted from the resume
    })
    
    # Make prediction
    prediction = model.predict_proba(features)[0]
    return prediction[1]  # Return probability of positive class 