from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('generate-improved/', views.generate_improved_resume_view, name='generate_improved'),
    path('download-improved/', views.download_improved_resume, name='download_improved'),
]
