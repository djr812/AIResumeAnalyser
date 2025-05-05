from django import forms

class ResumeUploadForm(forms.Form):
    resume = forms.FileField(
        label='Upload Resume',
        help_text='Upload your resume in PDF or DOCX format',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx'
        })
    )
    job_description = forms.CharField(
        label='Job Description',
        help_text='Paste the job description here',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste the job description here...'
        })
    )
