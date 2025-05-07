from django import forms

class ResumeUploadForm(forms.Form):
    resume = forms.FileField(
        label='Upload Resume',
        help_text='Upload your resume in PDF, DOCX, or TXT format',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx,.txt'
        })
    )
    job_description = forms.CharField(
        label='Job Description',
        help_text='Paste the job description here',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter the job description...'
        })
    )
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if not resume.name.endswith(('.pdf', '.docx', '.txt')):
                raise forms.ValidationError('Please upload a PDF, DOCX, or TXT file.')
            if resume.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be less than 5MB.')
        return resume
    
    def clean_job_description(self):
        job_description = self.cleaned_data.get('job_description')
        if not job_description or not job_description.strip():
            raise forms.ValidationError('Please enter a job description.')
        return job_description.strip()
