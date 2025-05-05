from django.core.management.base import BaseCommand
from django.conf import settings
import os
from ml_model.models import ResumePredictor
from ml_model.train_model import train_model

class Command(BaseCommand):
    help = 'Train the resume prediction model using the dataset'

    def handle(self, *args, **options):
        dataset_path = os.path.join(settings.BASE_DIR, 'AI_Resume_Screening.csv')
        
        if not os.path.exists(dataset_path):
            self.stdout.write(self.style.ERROR(f'Dataset not found at {dataset_path}'))
            return
        
        self.stdout.write('Training model...')
        try:
            accuracy, model_path = train_model(dataset_path)
            
            # Create or update the model record
            model, created = ResumePredictor.objects.get_or_create(
                name='Resume Predictor v1',
                defaults={
                    'model_file': os.path.relpath(model_path, settings.MEDIA_ROOT),
                    'accuracy': accuracy,
                    'is_active': True
                }
            )
            
            if not created:
                model.model_file = os.path.relpath(model_path, settings.MEDIA_ROOT)
                model.accuracy = accuracy
                model.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Model trained successfully! Accuracy: {accuracy:.2%}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error training model: {str(e)}')) 