from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Hidden
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordChangeView
from django.contrib.sites.models import Site
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django_registration.backends.activation.views import RegistrationView
from app.events import APP_SIGNUP
from accounts.forms import ProfileForm, ChangeEmailForm, decode_email_change_key, DeleteAccountForm, ChangePasswordForm


@login_required
def profile(request):
    if request.method == 'POST' and request.POST.get('action') == 'profile':
        profile_form = ProfileForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
    else:
        profile_form = ProfileForm(instance=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'change_email':
        change_email_form = ChangeEmailForm(request.POST, user=request.user)
        if change_email_form.is_valid():
            change_email_form.send_confirmation_email(
                request.user,
                request.scheme,
                Site.objects.get_current(request),
            )
            messages.add_message(request, messages.INFO, _('Check your email for a confirmation link'))
            return redirect('profile')
    else:
        change_email_form = ChangeEmailForm(user=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'password_change':
        password_change_form = ChangePasswordForm(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.add_message(request, messages.INFO, _('Your password has been changed'))
            return redirect('profile')
    else:
        password_change_form = ChangePasswordForm(request.user)

    if request.method == 'POST' and request.POST.get('action') == 'delete_account':
        delete_account_form = DeleteAccountForm(request.user, request.POST)
        if delete_account_form.is_valid():
            request.user.delete()
            messages.add_message(request, messages.INFO, _('Your account has been deleted'))
            return redirect('index')
    else:
        delete_account_form = DeleteAccountForm(request.user)

    profile_helper = FormHelper()
    profile_helper.form_id = 'profile_form'
    profile_helper.add_input(Submit('submit', 'Save'))
    profile_helper.add_input(Hidden('action', 'profile'))

    change_email_helper = FormHelper()
    change_email_helper.form_id = 'change_email_form'
    change_email_helper.add_input(Submit('submit', 'Change Email'))
    change_email_helper.add_input(Hidden('action', 'change_email'))

    password_change_helper = FormHelper()
    password_change_helper.form_id = 'password_change_form'
    password_change_helper.add_input(Submit('submit', 'Change Password'))
    password_change_helper.add_input(Hidden('action', 'password_change'))

    delete_account_helper = FormHelper()
    delete_account_helper.form_id = 'delete_account_form'
    delete_account_helper.add_input(Submit('submit', 'Delete Account', css_class='btn-danger'))
    delete_account_helper.add_input(Hidden('action', 'delete_account'))

    ctx = {
        'profile_form': profile_form,
        'profile_helper': profile_helper,
        'change_email_form': change_email_form,
        'change_email_helper': change_email_helper,
        'password_change_form': password_change_form,
        'password_change_helper': password_change_helper,
        'delete_account_form': delete_account_form,
        'delete_account_helper': delete_account_helper,
    }

    return render(request, 'app/profile.html', ctx)


@login_required
def confirm_change_email(request, username, activation_key):
    new_email = decode_email_change_key(username, activation_key)
    request.user.email = new_email
    request.user.save()
    messages.add_message(request, messages.INFO, _('Your email has been updated'))
    return redirect('profile')


class CustomRegistrationView(RegistrationView):
    email_body_html_template = 'django_registration/activation_email_body.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = FormHelper()
        helper.form_id = 'registration_form'
        helper.add_input(Submit('submit', 'Register'))
        context['helper'] = helper
        return context

    def send_activation_email(self, user):
        """
        Send the activation email. The activation key is the username,
        signed using TimestampSigner.

        """
        activation_key = self.get_activation_key(user)
        context = self.get_email_context(activation_key)
        context["user"] = user
        subject = render_to_string(
            template_name=self.email_subject_template,
            context=context,
            request=self.request,
        )
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = "".join(subject.splitlines())
        message = render_to_string(
            template_name=self.email_body_template,
            context=context,
            request=self.request,
        )
        message_html = render_to_string(
            template_name=self.email_body_html_template,
            context=context,
            request=self.request
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=f'{context["site"].name} <{settings.DEFAULT_FROM_EMAIL}>',
            to=[user.email],
        )
        email.attach_alternative(message_html, "text/html")
        email.send()

        APP_SIGNUP.send('New account creation', {'username': user.get_username()})


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
    html_email_template_name = 'registration/password_reset_email.html'
    email_template_name = 'registration/password_reset_email.txt'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = Site.objects.get_current()
        self.from_email = f'{site.name} <{settings.DEFAULT_FROM_EMAIL}>'

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
