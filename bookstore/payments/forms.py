import datetime

from django.forms import ModelForm
from django import forms
from .models import CreditCard

PROVIDERS = [('Visa', 'Visa'), ('MasterCard', 'MasterCard'), ('Discovery','Discovery')]


class CreditCardForm(ModelForm):
    name_on_card = forms.CharField(widget=forms.TextInput())
    cc_number = forms.CharField(label='Card Number', max_length=16)
    security_code = forms.CharField(label='Security Code', max_length=3)
    expiration = forms.DateField(label='Expiration Date')
    provider = forms.ChoiceField(choices=PROVIDERS, widget=forms.RadioSelect)

    def clean_cc_number(self):
        cc_number = self.cleaned_data['cc_number']
        if not cc_number.isdigit():
            raise forms.ValidationError('Invalid Credit Card number, cannot contain letters or special characters.')

        if len(cc_number) != 16:
            raise forms.ValidationError('Invalid Credit Card number, must contain 16 digits.')

        return cc_number

    def clean_security_code(self):
        security_code = self.cleaned_data['security_code']
        if not security_code.isdigit():
            raise forms.ValidationError('Invalid Security Code, cannot contain letters or special characters.')

        if len(security_code) != 3:
            raise forms.ValidationError('Invalid Security Code, must contain 3 digits.')

        return security_code

    def clean_expiration(self):
        expiration_date = self.cleaned_data['expiration']
        today = datetime.date.today()

        if expiration_date < today:
            raise forms.ValidationError('Card is expired.')

        return expiration_date

    class Meta:
        model = CreditCard
        fields = ['name_on_card', 'cc_number', 'security_code', 'expiration', 'provider']



