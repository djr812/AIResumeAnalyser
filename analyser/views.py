from django.shortcuts import render
from .forms import ResumeUploadForm
from .utils import parse_resume, calculate_tfidf_score
from ml_model.services import predict_resume_success, analyze_keywords

def index(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume']
            job_description = form.cleaned_data['job_description']
            
            # Parse resume
            resume_text = parse_resume(resume_file)
            
            # Calculate TF-IDF score
            tfidf_score = calculate_tfidf_score(resume_text, job_description)
            
            # Get ML prediction
            prediction_result, error = predict_resume_success(resume_text, job_description)
            if error:
                return render(request, 'analyser/index.html', {
                    'form': form,
                    'error': error
                })
            
            # Get keyword analysis
            keyword_analysis = analyze_keywords(resume_text, job_description)
            
            context = {
                'form': form,
                'resume_text': resume_text,
                'job_description': job_description,
                'tfidf_score': tfidf_score,
                'prediction': prediction_result['confidence'],
                'probability': prediction_result['probability'],
                'skills_found': prediction_result['skills_found'],
                'keyword_analysis': keyword_analysis
            }
            return render(request, 'analyser/result.html', context)
    else:
        form = ResumeUploadForm()
    
    return render(request, 'analyser/index.html', {'form': form})


