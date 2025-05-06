from django.shortcuts import render
from .forms import ResumeUploadForm
from .utils import parse_resume, calculate_tfidf_score
from ml_model.services import predict_resume_success, analyze_keywords, generate_improved_resume, create_pdf_from_text
from django.http import HttpResponse
from django.http import JsonResponse

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

def generate_improved_resume_view(request):
    if request.method == 'POST':
        resume_text = request.POST.get('resume_text')
        job_description = request.POST.get('job_description')
        
        # Generate improved resume
        improved_resume, changes = generate_improved_resume(resume_text, job_description)
        
        if improved_resume is None:
            return JsonResponse({'error': changes}, status=400)
        
        # Re-analyze the improved resume
        prediction_result, error = predict_resume_success(improved_resume, job_description)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Get TF-IDF score
        tfidf_score = calculate_tfidf_score(improved_resume, job_description)
        
        # Get keyword analysis
        keyword_analysis = analyze_keywords(improved_resume, job_description)
        
        context = {
            'resume_text': improved_resume,
            'job_description': job_description,
            'prediction': prediction_result['confidence'],
            'probability': prediction_result['probability'],
            'skills_found': prediction_result['skills_found'],
            'tfidf_score': tfidf_score,
            'keyword_analysis': keyword_analysis,
            'changes': changes,
            'is_improved': True
        }
        
        return render(request, 'analyser/result.html', context)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def download_improved_resume(request):
    if request.method == 'POST':
        resume_text = request.POST.get('resume_text')
        filename = request.POST.get('filename', 'improved_resume.docx')
        
        # Create PDF
        pdf_content = create_pdf_from_text(resume_text, filename)
        
        if pdf_content is None:
            return JsonResponse({'error': 'Error creating PDF'}, status=400)
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


