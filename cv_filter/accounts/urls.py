from django.urls import path

from .views import LoginPageView, LoginView, RegisterPageView, RegisterView

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),
]
