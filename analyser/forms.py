from django import forms

class ResumeForm(forms.Form):
    resume = forms.FileField(label='Upload your Resume (PDF or DOCX)')
    job_description = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}), label="Job Description")
