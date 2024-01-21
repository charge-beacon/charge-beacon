from django.contrib.auth.views import (
    LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
)
from django_registration.backends.activation.views import RegistrationView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Hidden


class CustomRegistrationView(RegistrationView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'registration_form'
        helper.add_input(Submit('submit', 'Register'))
        context['helper'] = helper
        return context


class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'login_form'
        helper.add_input(Submit('submit', 'Login'))
        helper.add_input(Hidden('next', self.request.GET.get('next', '')))
        context['helper'] = helper
        return context


class CustomPasswordResetView(PasswordResetView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'password_reset_form'
        helper.add_input(Submit('submit', 'Reset Password'))
        context['helper'] = helper
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'password_reset_confirm_form'
        helper.add_input(Submit('submit', 'Confirm Password Reset'))
        context['helper'] = helper
        return context


class CustomPasswordChangeView(PasswordChangeView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'password_change_form'
        helper.add_input(Submit('submit', 'Change Password'))
        context['helper'] = helper
        return context
