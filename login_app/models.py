from django.db import models
import re, bcrypt
from PIL import Image

class UserManager(models.Manager):
    def register_validator(self, postData):
        errors = {}

        if len(postData.get('first_name', '').strip()) < 2:
            errors['first_name'] = 'First name must be at least 2 characters!'

        if len(postData.get('last_name', '').strip()) < 2:
            errors['last_name'] = 'Last name must be at least 2 characters!'

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', postData.get('email', '')):
            errors['email'] = 'Invalid email format!'
        elif User.objects.filter(email=postData['email']).exists():
            errors['email'] = 'Email already exists!'

        if len(postData.get('password', '')) < 8:
            errors['password'] = 'Password must be at least 8 characters!'
        elif postData.get('password') != postData.get('confirm_pw'):
            errors['password'] = 'Passwords do not match!'

        if postData.get('role') not in ['hr', 'jobseeker']:
            errors['role'] = 'Please select a valid role!'

        return errors

    def login_validator(self, postData):
        errors = {}

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', postData.get('email', '')):
            errors['email'] = 'Invalid email format!'
        else:
            user = User.objects.filter(email=postData.get('email', ''))
            if not user:
                errors['email'] = 'Invalid email or password!'
            elif not bcrypt.checkpw(postData.get('password', '').encode(), user[0].password_hash.encode()):
                errors['password'] = 'Invalid email or password!'

        return errors

    def create_user(self, postData):
        hash_pw = bcrypt.hashpw(postData.get('password', '').encode(), bcrypt.gensalt()).decode()
        return User.objects.create(
            first_name=postData.get('first_name', ''),
            last_name=postData.get('last_name', ''),
            email=postData.get('email', ''),
            password_hash=hash_pw,
            role=postData.get('role', ''),
        )
    
 

    def update_profile_validator(self, user, postData, files):
        errors = {}

        email = postData.get('email', '').strip()
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Invalid email format!'
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors['email'] = 'This email is already in use by another account!'

        profile_pic = files.get('profile_pic')
        if profile_pic:
            max_size = 5 * 1024 * 1024  # 5MB
            if profile_pic.size > max_size:
                errors['profile_pic'] = 'Profile picture must be smaller than 5MB!'
            else:
                try:
                    img = Image.open(profile_pic)
                    img.verify()  # يتحقق إنه فعلاً صورة صحيحة، مش ملف مزيف
                    if img.format not in ['JPEG', 'PNG', 'WEBP', 'GIF']:
                        errors['profile_pic'] = 'Profile picture must be a JPEG, PNG, WEBP, or GIF image!'
                except Exception:
                    errors['profile_pic'] = 'Uploaded file is not a valid image!'
                finally:
                    profile_pic.seek(0)  # لازم نرجع المؤشر لبداية الملف، لأنه .verify() بيقرأه

        return errors
   
    def update_profile(self, user, postData, files):
        user.email = postData.get('email', user.email).strip()
        user.linkedin_url = postData.get('linkedin_url', '').strip()
        user.github_url = postData.get('github_url', '').strip()
        user.resume = postData.get('resume', '').strip()
        if files.get('profile_pic'):
            user.profile_pic = files['profile_pic']
        user.save()
        return user

class User(models.Model):
    ROLE_CHOICES = [('hr', 'HR Manager'), ('jobseeker', 'Job Seeker')]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    github_url = models.CharField(max_length=255, blank=True, null=True)
    linkedin_url = models.CharField(max_length=255, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    resume = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()