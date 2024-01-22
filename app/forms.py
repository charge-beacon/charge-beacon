from datetime import timedelta
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core import signing
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name']


class ChangeEmailForm(forms.Form):
    email = forms.EmailField(label=_('New email'))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is None:
            raise ValueError('Must provide a user to init ChangeEmailForm')
        self.user = user

    def clean_email(self):
        if self.cleaned_data['email'].lower() == self.user.email.lower():
            raise forms.ValidationError(_('That is already your email.'))
        users = get_user_model().objects.filter(email__iexact=self.cleaned_data['email'])
        if users.count() > 0:
            raise forms.ValidationError(_('There is already a user with that email.'))
        return self.cleaned_data['email']

    def send_confirmation_email(self, user, email, scheme, site):
        context = {
            'scheme': scheme,
            'key': get_email_change_key(user, email),
            'user': user,
            'email': email,
            'site': site,
            'expiry': timezone.now() + change_email_expiry_duration
        }
        subject = render_to_string(
            template_name='emails/change_email_subject.txt',
            context=context,
        )
        # join subject lines to avoid header injection issues
        subject = ''.join(subject.splitlines())
        body = render_to_string(
            template_name='emails/change_email_body.html',
            context=context,
        )
        send_mail(subject, body, None, [email])


change_email_expiry_duration = timedelta(days=1, minutes=1)


def get_email_change_key(user, email):
    return signing.dumps(f'{user.pk}:{email}', salt=user.username)


def decode_email_change_key(username, key):
    val = signing.loads(key, salt=username, max_age=change_email_expiry_duration.total_seconds())
    parts = val.split(':')
    if len(parts) == 2:
        return parts[-1]
    raise ValueError('Invalid signing string')


class DeleteAccountForm(forms.Form):
    password = forms.CharField(label=_('Current Password'), widget=forms.PasswordInput, required=True)
    confirm = forms.BooleanField(label=_('Confirm'), required=True,
                                 help_text=_('I understand that this will delete my account and all associated data. '
                                             'This cannot be undone.'))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        """
        Validate that the old_password field is correct.
        """
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise ValidationError(_('Password incorrect'), code="password_incorrect",)
        return password


class ChangePasswordForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['autofocus'] = False
