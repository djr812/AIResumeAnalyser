from django.db import models
import joblib
import os
from django.conf import settings

# Create your models here.

class ResumePredictor(models.Model):
    name = models.CharField(max_length=100)
    model_file = models.FileField(upload_to='ml_models/')
    created_at = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"

    def get_model(self):
        """Load the trained model from the file."""
        if not self.model_file:
            return None
        model_path = os.path.join(settings.MEDIA_ROOT, self.model_file.name)
        return joblib.load(model_path)

    class Meta:
        ordering = ['-created_at']
