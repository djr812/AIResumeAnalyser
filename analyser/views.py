from django.shortcuts import render
from .forms import ResumeUploadForm
from .utils import parse_resume, calculate_tfidf_score
from ml_model.services import predict_resume_success, analyze_keywords, generate_improved_resume, create_pdf_from_text
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

def index(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the uploaded file
            resume_file = request.FILES['resume']
            job_description = form.cleaned_data['job_description']
            
            # Save the file temporarily
            fs = FileSystemStorage()
            filename = fs.save(resume_file.name, resume_file)
            file_path = fs.path(filename)
            
            try:
                # Extract text from the resume
                resume_text = parse_resume(file_path)
                
                # Get prediction and section evaluations
                prediction_result = predict_resume_success(resume_text, job_description)
                
                if 'error' in prediction_result:
                    messages.error(request, prediction_result['error'])
                    return redirect('index')
                
                # Get keyword analysis
                keyword_analysis = analyze_keywords(resume_text, job_description)
                
                # Debug print
                print("\n=== Prediction Result ===")
                print(prediction_result)
                print("=== End Prediction Result ===\n")
                
                # Prepare context with all necessary data
                context = {
                    'resume_text': resume_text,
                    'job_description': job_description,
                    'prediction': {
                        'prediction': prediction_result['prediction'],
                        'confidence': prediction_result['confidence'],
                        'skills_found': prediction_result['skills_found']
                    },
                    'keyword_analysis': keyword_analysis,
                    'section_evaluations': prediction_result.get('section_evaluations', {}),
                    'debug': True  # Enable debug mode
                }
                
                # Debug print
                print("\n=== Context ===")
                print(context)
                print("=== End Context ===\n")
                
                # Clean up the uploaded file
                fs.delete(filename)
                
                return render(request, 'analyser/result.html', context)
                
            except Exception as e:
                messages.error(request, f'Error processing resume: {str(e)}')
                if fs.exists(filename):
                    fs.delete(filename)
                return redirect('index')
    else:
        form = ResumeUploadForm()
    
    return render(request, 'analyser/index.html', {'form': form})

def generate_improved_resume_view(request):
    """View for generating an improved version of the resume."""
    if request.method == 'POST':
        resume_text = request.POST.get('resume_text', '')
        job_description = request.POST.get('job_description', '')
        
        if not resume_text or not job_description:
            return JsonResponse({'error': 'Resume text and job description are required'})
        
        # Generate improved resume
        result = generate_improved_resume(resume_text, job_description)
        if isinstance(result, tuple) and result[0] is None:
            return JsonResponse({'error': result[1]})
        
        # Re-analyze the improved resume
        prediction_result, error = predict_resume_success(result['improved_resume'], job_description)
        if error:
            return JsonResponse({'error': error})
        
        # Get keyword analysis
        keyword_analysis = analyze_keywords(result['improved_resume'], job_description)
        
        context = {
            'resume_text': result['improved_resume'],
            'job_description': job_description,
            'prediction': prediction_result,
            'keyword_analysis': keyword_analysis,
            'changes_made': result['changes'],
            'section_evaluations': result['section_evaluations']
        }
        
        return render(request, 'analyser/result.html', context)
    
    return JsonResponse({'error': 'Invalid request method'})

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


