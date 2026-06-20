from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
import bcrypt

def login_page(request):
    if 'user_id' in request.session:
        if request.session.get('user_role') == 'hr':
            return redirect('/dashboard/')
        return redirect('/jobs/')
    return render(request, 'login.html')

def register_page(request):
    if 'user_id' in request.session:
        if request.session.get('user_role') == 'hr':
            return redirect('/dashboard/')
        return redirect('/jobs/')
    return render(request, 'register.html')

def register(request):
    if request.method == 'POST':
        errors = User.objects.register_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            return redirect('/register/')
        
        user = User.objects.create_user(request.POST)
        request.session['user_id'] = user.id
        request.session['user_role'] = user.role

        if user.role == 'hr':
            return redirect('/dashboard/')
        return redirect('/jobs/')
    
    return redirect('/register/')

def login(request):
    if request.method == 'POST':
        errors = User.objects.login_validator(request.POST)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            return redirect('/login/')
        
        user = User.objects.filter(email=request.POST.get('email', ''))[0]
        request.session['user_id'] = user.id
        request.session['user_role'] = user.role

        if user.role == 'hr':
            return redirect('/dashboard/')
        return redirect('/jobs/')
    
    return redirect('/login/')

def logout(request):
    request.session.clear()
    return redirect('/login/')

def profile_page(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.get(id=request.session['user_id'])
    return render(request, 'profile.html', {'user': user})

def update_profile(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    if request.method == 'POST':
        user = User.objects.get(id=request.session['user_id'])
        errors = User.objects.update_profile_validator(user, request.POST, request.FILES)
        if errors:
            for msg in errors.values():
                messages.error(request, msg)
            return redirect('/profile/')
        User.objects.update_profile(user, request.POST, request.FILES)
        messages.success(request, 'Profile updated successfully!')
    return redirect('/profile/')

def about_page(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.get(id=request.session['user_id'])
    techs = ['Django', 'MySQL', 'Tailwind CSS', 'AWS EC2']
    return render(request, 'about.html', {'user': user, 'techs': techs})