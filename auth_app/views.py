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
    """Public search entry point.

    - If called without query params, show the search form.
    - If called with ?username=..., fetch the public GitHub profile and recent public repos
      and render the profile page (no OAuth required).
    """
    username = request.GET.get('username', '').strip()
    if username:
        error = None
        github_data = None
        repositories = []

        # Fetch public profile
        profile_url = f'https://api.github.com/users/{username}'
        repos_url = f'https://api.github.com/users/{username}/repos?sort=updated&per_page=100'
        try:
            profile_resp = requests.get(profile_url, timeout=10)
        except requests.RequestException as exc:
            error = f'Network error when contacting GitHub: {exc}'
            profile_resp = None

        if profile_resp is not None:
            if profile_resp.status_code == 200:
                try:
                    github_data = profile_resp.json()
                except ValueError:
                    error = 'Invalid JSON received from GitHub for profile.'
            elif profile_resp.status_code == 404:
                error = 'GitHub user not found.'
            elif profile_resp.status_code == 403:
                error = 'GitHub API rate limit exceeded or access forbidden. Try again later.'
            else:
                error = f'GitHub API error when fetching profile: {profile_resp.status_code}'

        # If profile fetched successfully, fetch repos
        if github_data and not error:
            try:
                repos_resp = requests.get(repos_url, timeout=10)
            except requests.RequestException as exc:
                error = f'Network error when contacting GitHub for repos: {exc}'
                repos_resp = None

            if repos_resp is not None:
                if repos_resp.status_code == 200:
                    try:
                        repositories = repos_resp.json()
                    except ValueError:
                        error = 'Invalid JSON received from GitHub for repositories.'
                elif repos_resp.status_code == 403:
                    error = 'GitHub API rate limit exceeded or access forbidden. Try again later.'
                else:
                    # If user has no repos, the API still returns 200 with an empty list.
                    error = f'GitHub API error when fetching repositories: {repos_resp.status_code}'

        if error:
            # Render the login/search page with the error message
            return render(request, 'auth_app/login.html', {'error': error, 'search_username': username})

        # Render the public profile using the same template as the authenticated profile.
        context = {
            'github_data': github_data,
            'repositories': repositories,
            'search_username': username,
        }
        return render(request, 'auth_app/profile.html', context)

    # No username provided - just render the search/login page
    return render(request, 'auth_app/login.html')

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

def search_repositories(request):
    """Public search for a GitHub user's public repositories.

    Usage: GET /repositories/search/?username=githubusername
    If `username` is provided, this view queries the GitHub public API
    and returns the user's public repositories (no login required).

    Notes:
    - The unauthenticated GitHub API rate limit is low (60 requests/hour per IP).
    - If the API returns 403 you likely hit the rate limit; consider adding app credentials
      or trying again later.
    """
    username = request.GET.get('username', '').strip()
    repositories = []
    error = None

    if username:
        url = f'https://api.github.com/users/{username}/repos?sort=updated&per_page=100'
        try:
            resp = requests.get(url, timeout=10)
        except requests.RequestException as exc:
            error = f'Network error when contacting GitHub: {exc}'
            resp = None

        if resp is not None:
            if resp.status_code == 200:
                try:
                    repositories = resp.json()
                except ValueError:
                    error = 'Invalid JSON received from GitHub.'
            elif resp.status_code == 404:
                error = 'GitHub user not found.'
            elif resp.status_code == 403:
                # Rate limit or forbidden
                error = 'GitHub API rate limit exceeded or access forbidden. Try again later.'
            else:
                error = f'GitHub API error: {resp.status_code}'

    context = {
        'repositories': repositories,
        'search_username': username,
        'error': error,
    }
    return render(request, 'auth_app/repositories.html', context)
