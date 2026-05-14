from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from watchlist.models import WatchlistItem


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
        else:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            messages.success(request, f'Welcome to Screenz, {user.display_name}!')
            return redirect('home')

    return render(request, 'users/signup.html', {'active_tab': ''})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'users/login.html', {'active_tab': ''})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    watched = WatchlistItem.objects.filter(user=user, status='watched').select_related('movie').prefetch_related('movie__genres', 'movie__platforms')
    watchlist = WatchlistItem.objects.filter(user=user, status='want_to_watch').select_related('movie').prefetch_related('movie__genres', 'movie__platforms')

    # Favorite genres — top 3 from watched movies
    from django.db.models import Count
    fav_genres = (
        WatchlistItem.objects.filter(user=user, status='watched')
        .values('movie__genres__name')
        .annotate(count=Count('movie__genres__name'))
        .order_by('-count')[:3]
    )

    context = {
        'watched': watched,
        'watchlist': watchlist,
        'watched_count': watched.count(),
        'watchlist_count': watchlist.count(),
        'fav_genres': fav_genres,
        'active_tab': 'profile',
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.bio = request.POST.get('bio', '').strip()
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()
        messages.success(request, 'Profile updated!')
        return redirect('profile')
    return render(request, 'users/edit_profile.html', {'active_tab': 'profile'})
