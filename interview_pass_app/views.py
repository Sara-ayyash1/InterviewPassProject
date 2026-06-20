from functools import wraps
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from login_app.models import User
from .models import Job, Question, Application, Answer
from .services import ai_services

# ==========================================
# CUSTOM ROLE-BASED DECORATORS
# ==========================================

def hr_required(view_func):
    """
    Decorator to ensure the user is logged in and possesses the 'hr' role.
    If unauthorized, redirects to the login page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session or request.session.get('user_role') != 'hr':
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def jobseeker_required(view_func):
    """
    Decorator to ensure the user is logged in and possesses the 'jobseeker' role.
    Handles standard page redirects and gracefully returns JSON 401 errors for AJAX/API requests.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session or request.session.get('user_role') != 'jobseeker':
            # Dynamically return JSON response if it's an API route, otherwise redirect to login
            if request.path.startswith('/api/') or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Unauthorized access. Please login as a jobseeker.'}, status=401)
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==========================================
# AI-POWERED FEATURES (HR side)
# ==========================================

@hr_required
def ai_analyze_cv(request, applicant_id):
    """
    AJAX endpoint for the "Analyze CV" button on the applicant_profile page.
    Looks up the application (scoped to this HR's own jobs, same security
    pattern as applicant_decision), grabs the applicant's resume text, and
    sends it to Claude for scoring against the job's requirements.
    """
    user = get_user(request)

    # SECURITY CHECK: same pattern as applicant_decision — ensures this HR
    # can only analyze applicants who applied to THEIR jobs (prevents IDOR)
    application = get_object_or_404(Application, id=applicant_id, job__hr=user)

    resume_text = application.job_seeker.resume
    if not resume_text:
        return JsonResponse({'error': 'This applicant has no resume on file.'}, status=400)

    result = ai_services.analyze_cv(resume_text, application.job)
    return JsonResponse(result)


@hr_required
def ai_generate_questions(request):
    """
    AJAX endpoint for the "Generate Questions" button on create_job/edit_job.
    Takes the job title/skills/experience level currently typed into the form
    (not yet saved to the DB) and asks Claude to suggest interview questions.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    result = ai_services.generate_questions(
        request.POST.get('title', ''),
        request.POST.get('skills_required', ''),
        request.POST.get('experience_level', ''),
    )
    return JsonResponse(result)


@hr_required
def ai_generate_description(request):
    """
    AJAX endpoint for the "Generate Description" button on create_job/edit_job.
    Same idea as ai_generate_questions, but returns a description string
    instead of a list of questions.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        description = ai_services.generate_description(
            request.POST.get('title', ''),
            request.POST.get('skills_required', ''),
            request.POST.get('experience_level', ''),
        )
        
        # التأكد من أن النتيجة نص صحيح
        if description and "Error" not in description:
            return JsonResponse({'description': description})
        else:
            return JsonResponse({'error': 'Could not generate description.'}, status=500)

    except Exception as e:
        error_msg = str(e)
        # التحقق من نوع الخطأ (Quota)
        if "RESOURCE_EXHAUSTED" in error_msg:
            return JsonResponse({'error': 'Daily limit reached. Please try again tomorrow.'}, status=429)
        
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_user(request):
    """
    Helper function to fetch the currently logged-in user instance using the session user_id.
    """
    return User.objects.get(id=request.session['user_id'])


# ==========================================
# HR (RECRUITER) VIEWS
# ==========================================

@hr_required
def hr_dashboard(request):
    user = get_user(request)
    
    # DATABASE QUERY: Fetch all jobs created specifically by this HR user using a custom Manager
    jobs = Job.objects.get_hr_jobs(user)
    
    # METRICS AGGREGATION: Count the total number of applications received for all jobs posted by this HR
    all_applications = Application.objects.filter(job__hr=user)
    recent_applications = all_applications.select_related('job_seeker', 'job').order_by('-applied_at')[:5]
   
    return render(request, 'hr/dashboard.html', {
        'user': user,
        'jobs': jobs,
        'total_jobs': jobs.count(),
        'total_applications':  all_applications.count(),
        'pending_count': all_applications.filter(status='pending').count(),
        'accepted_count': all_applications.filter(status='accepted').count(),
        'rejected_count': all_applications.filter(status='rejected').count(),
        'recent_applications': recent_applications,
    })


@hr_required
def create_job(request):
    user = get_user(request)
    
    if request.method == 'POST':
        # VALIDATION: Validate incoming form data using a custom validator inside JobManager
        errors = Job.objects.job_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg) # Inject error messages into the Django messages framework
            return redirect('create_job')
            
        # DATA PERSISTENCE: Create the job record and its associated screening questions
        job = Job.objects.create_job(request.POST, user)
        Question.objects.create_questions(request.POST.getlist('questions'), job)
        return redirect('hr_dashboard')
        
    return render(request, 'hr/create_job.html', {'user': user})


@hr_required
def job_info(request, job_id):
    user = get_user(request)
    
    # SECURITY & ACCESS CONTROL: Ensure the job exists AND belongs to the requesting HR user
    job = get_object_or_404(Job, id=job_id, hr=user)
    
    # DATABASE QUERY: Retrieve all applications submitted for this specific job
    applications = Application.objects.get_job_applications(job)
    
    return render(request, 'hr/job_info.html', {
        'user': user,
        'job': job,
        'applications': applications,
    })


@hr_required
def edit_job(request, job_id):
    user = get_user(request)
    # DATABASE LOOKUP: Fetch the application instance or return a standard HTTP 404 Error 
    # if the record does not exist, replacing the need for explicit try/except blocks.
    job = get_object_or_404(Job, id=job_id, hr=user)
    
    if request.method == 'POST':
        # VALIDATION: Validate the updated fields before saving
        errors = Job.objects.job_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            return redirect('edit_job', job_id=job_id)
            
        # DATA UPDATE: Execute update operation on the model instance
        Job.objects.update_job(job, request.POST)
        return redirect('job_info', job_id=job_id)
        
    return render(request, 'hr/edit_job.html', {'user': user, 'job': job})


@hr_required
def delete_job(request, job_id):
    user = get_user(request)
    job = get_object_or_404(Job, id=job_id, hr=user)
    
    # DATABASE OPERATION: Permanently remove the job record from the database
    job.delete()
    return redirect('hr_dashboard')


@hr_required
def applicant_profile(request, applicant_id):
    user = get_user(request)
    
    # SECURITY CHECK: Ensure the application belongs to a job hosted by this specific HR
    application = get_object_or_404(Application, id=applicant_id, job__hr=user)
    
    return render(request, 'hr/applicant_profile.html', {
        'user': user,
        'application': application,
    })


@hr_required
def applicant_decision(request, applicant_id):
    user = get_user(request)
    # SECURE LOOKUP (Prevents IDOR): Use Django ORM double underscore (__) to span relationships.
    # This traverses from the Application model, through the 'job' foreign key, 
    # into the Job model's 'hr' field to ensure the application belongs to a job owned by the logged-in HR.
    application = get_object_or_404(Application, id=applicant_id, job__hr=user)

    if request.method == 'POST':
        # STATUS UPDATE: Update the applicant's status (e.g., 'accepted' or 'rejected') via the Manager
        Application.objects.update_status(application, request.POST.get('decision'))
        
    return redirect('job_info', job_id=application.job.id)


# ==========================================
# JOB SEEKER VIEWS
# ==========================================

@jobseeker_required
def jobs_list(request):
    user = get_user(request)
    
    # SEARCH FILTERING: Capture fallback search parameter from traditional GET requests
    query = request.GET.get('q', '')
    jobs = Job.objects.filter(title__icontains=query) if query else Job.objects.all()
    
    # ORM OPTIMIZATION: Extract raw flat array of job IDs already applied to by this user.
    applied_job_ids = list(Application.objects.filter(job_seeker=user).values_list('job_id', flat=True)) 
    
    return render(request, 'jobseeker/jobs_list.html', {
        'user': user,
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'query': query,
    })


@jobseeker_required
def job_detail(request, job_id):
    user = get_user(request)
    job = get_object_or_404(Job, id=job_id)
    
    # CONDITION CHECK: Verify if the user has already submitted an application for this specific opening
    already_applied = Application.objects.already_applied(job, user)
    
    return render(request, 'jobseeker/job_detail.html', {
        'user': user,
        'job': job,
        'already_applied': already_applied,
    })


@jobseeker_required
def apply_job(request, job_id):
    user = get_user(request)
    job = get_object_or_404(Job, id=job_id)
    
    # IDEMPOTENCY CHECK: Prevent duplicate submissions for the same position
    if Application.objects.already_applied(job, user):
        return redirect('jobs_list')
        
    if request.method == 'POST':
        questions = job.questions.all()
        
        # VALIDATION: Ensure all mandatory screening questions are answered
        errors = Application.objects.application_validator(request.POST, questions)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            return redirect('job_detail', job_id=job_id)
            
        # DATA PERSISTENCE: Save application record and store answers mapping back to the questions
        application = Application.objects.create_application(job, user)
        Answer.objects.create_answers(application, questions, request.POST)
        return redirect('jobs_list')
        
    return redirect('job_detail', job_id=job_id)


# ==========================================
# API ENDPOINTS (AJAX/FETCH BACKEND)
# ==========================================

@jobseeker_required
def api_jobs(request):
    # DYNAMIC SEARCH QUERY: Capture text queries passed asynchronously via JavaScript fetch parameters
    query = request.GET.get('q', '').strip()
    
    # PERFORMANCE OPTIMIZATION: Use 'prefetch_related' on Many-to-Many 'skills' relationship 
    # to avoid the N+1 database query problem during loop serialization.
    if query:
        # MULTI-FIELD SEARCH: Use Q objects to search across both job title AND related skill names.
        # 'distinct()' prevents duplicate job rows when multiple skills match the same query.
        jobs = Job.objects.filter(
            Q(title__icontains=query) | Q(skills__name__icontains=query)
        ).distinct().prefetch_related('skills')
    else:
        jobs = Job.objects.prefetch_related('skills').all()
        
    result = []
    # MANUAL SERIALIZATION: Convert complex model objects into standard Python dictionaries for JSON conversion
    for job in jobs:
        # DATA DENORMALIZATION: Combine related skill object strings into a single clean text format space-separated
        skills_list = [skill.name for skill in job.skills.all()]
        skills_string = " ".join(skills_list)
        
        result.append({
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'experience_level': job.get_experience_level_display(),
            'skills_required': skills_string,
        })
        
    # HTTP RESPONSE: Return raw JSON payload with 'safe=False' to allow top-level serialized arrays
    return JsonResponse(result, safe=False)