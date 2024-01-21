from django.core.paginator import Paginator
from django.contrib.syndication.views import Feed
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.sites.models import Site
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Hidden

from app.models import Station, Update
from app.renderer import get_changes
from app.constants import LOOKUPS
from app.forms import ProfileForm, ChangeEmailForm, decode_email_change_key, DeleteAccountForm


def index(request):
    return render(request, 'app/index.html', get_updates_context(request))


def updates_partial(request):
    return render(request, 'app/updates_body.html', get_updates_context(request))


def station(request, beacon_name):
    item = Station.objects.get(beacon_name=beacon_name)
    return render(request, 'app/station.html', {
        'base_uri': f'{request.scheme}://{request.get_host()}',
        'station': item,
        'updates': item.updates.all(),
    })


def get_updates_context(request):
    feed_kwargs = {
        'station': None,
    }
    if selected_networks := get_param(request, 'ev_network'):
        feed_kwargs['ev_networks'] = selected_networks
    if selected_states := get_param(request, 'ev_state'):
        feed_kwargs['states'] = selected_states
    if selected_plug_types := get_param(request, 'plug_types'):
        feed_kwargs['ev_connector_types'] = selected_plug_types

    queryset = Update.objects.feed(**feed_kwargs)

    if request.GET.get('dc_fast', None) == 'true':
        queryset = queryset.filter(station__ev_dc_fast_num__gt=0)

    if request.GET.get('only_new', None) == 'true':
        queryset = queryset.filter(is_creation=True)

    paginator = Paginator(queryset, 25)
    base_uri = f'{request.scheme}://{request.get_host()}'
    ctx = {
        'base_uri': base_uri,
        'queryset': queryset,
        'updates': paginator.get_page(request.GET.get('page', '1')),
        'networks': Station.objects.all_networks(),
        'selected_networks': selected_networks,
        'states': Station.objects.all_states(),
        'selected_states': selected_states,
        'plug_types': LOOKUPS['ev_connector_types'],
        'selected_plug_types': selected_plug_types,
        'feed_url': f'{base_uri}{reverse("updates-feed")}?{request.GET.urlencode()}',
    }

    return ctx


def get_param(request, name) -> list[str]:
    return list(filter(bool, request.GET.getlist(name)))


class CustomFeed(Feed):
    title = "EV Charging Stations"
    link = "/updates/"
    description_template = 'app/station_card_feed.html'

    def get_object(self, request, *args, **kwargs):
        ctx = get_updates_context(request)
        return ctx

    def items(self, obj):
        return obj['queryset'][:100]

    def link(self, obj):
        return obj['feed_url']

    def item_title(self, item):
        return f"{item.station.station_name} ({item.station.ev_network})"

    def get_context_data(self, item, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['station'] = item.station
        ctx['new'] = item.is_creation
        ctx['timestamp'] = item.created_at
        ctx['changes'] = get_changes(item)
        return ctx

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created_at


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
                change_email_form.cleaned_data['email'],
                request.scheme,
                Site.objects.get_current(request),
            )
            messages.add_message(request, messages.INFO, _('Check your email for a confirmation link'))
            return redirect('profile')
    else:
        change_email_form = ChangeEmailForm(user=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'password_change':
        password_change_form = PasswordChangeForm(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.add_message(request, messages.INFO, _('Your password has been changed'))
            return redirect('profile')
    else:
        password_change_form = PasswordChangeForm(request.user)

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
