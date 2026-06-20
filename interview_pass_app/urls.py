from django.urls import path
from . import views

urlpatterns = [
    # HR
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/<int:job_id>/', views.job_info, name='job_info'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    path('applicants/<int:applicant_id>/', views.applicant_profile, name='applicant_profile'),
    path('applicants/<int:applicant_id>/decision/', views.applicant_decision, name='applicant_decision'),

    # Job Seeker
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('jobs/<int:job_id>/view/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),

    # API
    path('api/jobs/', views.api_jobs, name='api_jobs'),

    # AI feature endpoints — all scoped under hr/ since only HR uses them
    path('hr/jobs/ai/generate-description/', views.ai_generate_description, name='ai_generate_description'),
    path('hr/jobs/ai/generate-questions/', views.ai_generate_questions, name='ai_generate_questions'),
    path('hr/applicants/<int:applicant_id>/analyze-cv/', views.ai_analyze_cv, name='ai_analyze_cv'),
]