from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm,
    UserProfileForm
)
from .models import UserProfile

def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматический вход после регистрации
            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    """Вход в систему"""
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')

@login_required
def profile_view(request):
    """Просмотр профиля пользователя"""
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    return render(request, 'auth/profile.html', {
        'user': user,
        'profile': profile
    })

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'auth/profile_edit.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        user = self.request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile
    
    def get_initial(self):
        initial = super().get_initial()
        initial['username'] = self.request.user.username
        initial['email'] = self.request.user.email
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        return initial
    
    def form_valid(self, form):
        # Обновляем данные пользователя
        user = self.request.user
        user.email = self.request.POST.get('email', user.email)
        user.first_name = self.request.POST.get('first_name', user.first_name)
        user.last_name = self.request.POST.get('last_name', user.last_name)
        user.save()
        
        messages.success(self.request, 'Профиль успешно обновлен.')
        return super().form_valid(form)