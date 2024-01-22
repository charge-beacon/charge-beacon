"""
URL configuration for charging project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django_registration.backends.activation import views as reg_views
from django.views.generic.base import TemplateView
from charging import views

urlpatterns = [
    path('', include('app.urls')),

    # registration
    path('accounts/register', views.CustomRegistrationView.as_view(), name='django_registration_register'),
    path('accounts/register/complete', TemplateView.as_view(
        template_name="django_registration/registration_complete.html"
    ), name='django_registration_complete'),
    path('accounts/register/closed', TemplateView.as_view(
        template_name="django_registration/registration_closed.html"
    ), name='django_registration_disallowed'),
    path('accounts/activate/complete', TemplateView.as_view(
        template_name="django_registration/activation_complete.html"
    ), name='django_registration_activation_complete'),
    path('accounts/activate/<str:activation_key>', reg_views.ActivationView.as_view(),
         name='django_registration_activate'),

    # auth
    path('accounts/login', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/password_change', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/reset/<uidb64>/<token>', views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/reset/done', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('admin/', admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
]
