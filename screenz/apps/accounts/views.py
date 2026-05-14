from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    login_form = LoginForm()
    signup_form = SignUpForm()
    active_tab = 'login'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = LoginForm(data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                return redirect('home')
            messages.error(request, 'Invalid email or password.')
        elif action == 'signup':
            active_tab = 'signup'
            signup_form = SignUpForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)
                return redirect('home')
    return render(request, 'accounts/auth.html', {
        'login_form': login_form, 'signup_form': signup_form, 'active_tab': active_tab
    })

@login_required
def profile_view(request):
    from apps.watchlist.models import WatchlistItem, WatchedMovie
    watchlist = WatchlistItem.objects.filter(user=request.user).select_related('movie')
    watched = WatchedMovie.objects.filter(user=request.user).select_related('movie').order_by('-watched_at')[:12]
    return render(request, 'accounts/profile.html', {'watchlist': watchlist, 'watched': watched})

def logout_view(request):
    logout(request)
    return redirect('login')
