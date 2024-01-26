from django import forms
from beacon.models import Search


class SearchForm(forms.ModelForm):
    class Meta:
        model = Search
        fields = [
            'name', 'ev_networks', 'plug_types', 'dc_fast', 'only_new',
            'within', 'daily_email', 'weekly_email'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        if self.user is None:
            raise ValueError('user must be provided')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        return super().save(*args, **kwargs)
