from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
import requests

@login_required
def profile(request):
    social = request.user.social_auth.get(provider='github')
    access_token = social.extra_data['access_token']

    # Fetch GitHub profile data
    headers = {'Authorization': f'token {access_token}'}
    profile_response = requests.get('https://api.github.com/user', headers=headers)
    profile_data = profile_response.json()

    context = {
        'github_data': profile_data,
    }
    return render(request, 'auth_app/profile.html', context)

def login(request):
    return render(request, 'auth_app/login.html')

@login_required
def home(request):
    return render(request, 'auth_app/home.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def repositories(request):
    social = request.user.social_auth.get(provider='github')
    access_token = social.extra_data['access_token']

    # Fetch GitHub repositories data
    headers = {'Authorization': f'token {access_token}'}
    repos_response = requests.get('https://api.github.com/user/repos?sort=updated&per_page=100', headers=headers)
    repos_data = repos_response.json()

    context = {
        'repositories': repos_data,
    }
    return render(request, 'auth_app/repositories.html', context)
