import re
from django.db import models
from login_app.models import User


def parse_skills(raw):
    return [s.strip() for s in re.split(r'[,\s]+', raw) if s.strip()]


class JobManager(models.Manager):
    def job_validator(self, postData):
        errors = {}
        if len(postData.get('title', '').strip()) < 2:
            errors['title'] = 'Title must be at least 2 characters!'
        if len(postData.get('description', '').strip()) < 10:
            errors['description'] = 'Description must be at least 10 characters!'
        if postData.get('experience_level') not in ['junior', 'mid', 'senior']:
            errors['experience_level'] = 'Please select a valid experience level!'
        skills = parse_skills(postData.get('skills_required', ''))
        if len(skills) == 0:
            errors['skills_required'] = 'Please add at least one skill!'
        else:
            for skill in skills:
                if len(skill) < 2:
                    errors['skills_required'] = 'Each skill must be at least 2 characters!'
                    break
        return errors

    def create_job(self, postData, hr):
        job = Job.objects.create(
            title=postData.get('title'),
            description=postData.get('description'),
            experience_level=postData.get('experience_level'),
            hr=hr,
        )
        for skill_name in parse_skills(postData.get('skills_required', '')):
            skill, _ = Skill.objects.get_or_create(name=skill_name) #Here
            job.skills.add(skill)
        return job

    def update_job(self, job, postData):
        job.title = postData.get('title')
        job.description = postData.get('description')
        job.experience_level = postData.get('experience_level')
        job.save()
        job.skills.clear()
        for skill_name in parse_skills(postData.get('skills_required', '')):
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            job.skills.add(skill)
        return job

    def get_hr_jobs(self, hr):
        return Job.objects.filter(hr=hr)

    def get_job_with_applications(self, job_id, hr):#Here
        return Job.objects.filter(id=job_id, hr=hr).first()


class QuestionManager(models.Manager):
    def create_questions(self, questions_list, job):
        for q in questions_list:
            if q.strip():
                Question.objects.create(question_text=q, job=job)


class ApplicationManager(models.Manager):
    def application_validator(self, postData, questions):
        errors = {}
        for question in questions:
            answer = postData.get(f'answer_{question.id}', '').strip()
            if len(answer) < 5:
                errors[f'answer_{question.id}'] = 'Answer must be at least 5 characters!'
        return errors

    def create_application(self, job, user):
        return Application.objects.create(job=job, job_seeker=user)

    def update_status(self, application, decision):
        if decision in ['accepted', 'rejected']:
            application.status = decision
            application.save()

    def get_user_applications(self, user):
        return Application.objects.filter(job_seeker=user).select_related('job')

    def get_job_applications(self, job):
        return Application.objects.filter(job=job).select_related('job_seeker')

    def already_applied(self, job, user):
        return Application.objects.filter(job=job, job_seeker=user).exists()


class AnswerManager(models.Manager):
    def create_answers(self, application, questions, postData):
        for question in questions:
            Answer.objects.create(
                application=application,
                question=question,
                answer_text=postData.get(f'answer_{question.id}', ''),
            )


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    EXPERIENCE_CHOICES = [
        ('junior', 'Junior'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name='jobs')
    experience_level = models.CharField(max_length=100, choices=EXPERIENCE_CHOICES)
    hr = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = JobManager()


class Question(models.Model):
    question_text = models.TextField()
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = QuestionManager()


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    job_seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ApplicationManager()


class Answer(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = AnswerManager()