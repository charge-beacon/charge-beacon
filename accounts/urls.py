from django.urls import path, include
from django.contrib.auth import views as auth_views
from django_registration.backends.activation import views as reg_views
from django.views.generic.base import TemplateView
from accounts.views import (
    CustomRegistrationView, CustomLoginView, CustomPasswordResetView, CustomPasswordChangeView,
    CustomPasswordResetConfirmView, profile, confirm_change_email
)

urlpatterns = [
    # profile
    path('profile', profile, name='profile'),
    path('profile/change_email/<slug:username>/<str:activation_key>', confirm_change_email,
         name='confirm_change_email'),

    # registration
    path('accounts/register', CustomRegistrationView.as_view(), name='django_registration_register'),
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
    path('accounts/login', CustomLoginView.as_view(), name='login'),
    path('accounts/logout', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset', CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/password_change', CustomPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/reset/<uidb64>/<token>', CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/reset/done', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
