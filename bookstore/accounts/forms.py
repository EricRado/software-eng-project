import re

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django import forms
from .models import User, Address


class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email_address = forms.EmailField(max_length=254, required=True)

    class Meta:
        fields = ("nickname","email_address", 'first_name', 'last_name', "password1","password2")
        model = get_user_model()

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["email_address"].label = "Email Address"
        self.fields["first_name"].label = "First Name"
        self.fields["last_name"].label = "Last Name"

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']

        if not re.search(r'^\w+$', nickname):
            raise forms.ValidationError('Nickname can only contain alphanumeric characters and underscore.')

        try:
            User.objects.get(nickname=nickname)

        except User.DoesNotExist:
            return nickname

        raise forms.ValidationError('Nickname already exists.')

    def clean_password2(self):
        if 'password1' in self.cleaned_data:
            password1 = self.cleaned_data['password1']
            password2 = self.cleaned_data['password2']
            if password1 == password2:
                return password2

            raise forms.ValidationError('Password do not match!')

    def clean_email_address(self):
        email = self.cleaned_data['email_address']

        # check if email address is valid
        if not re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email):
            raise forms.ValidationError('Email Address is invalid format.')

        # check if email address already exits
        try:
            User.objects.get(email_address=email)
        except User.DoesNotExist:
            return email

        raise forms.ValidationError('Email Address already exists.')


class EditUserProfileForm(ModelForm):
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    nickname = forms.CharField(label='Nickname')
    email_address = forms.EmailField(label="Email Address")

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']

        # check if nickname submitted is the same as the current user online
        if nickname == self.instance.nickname:
            return nickname

        # username is different from previous, check if it already exists
        try:
            User.objects.exclude(pk=self.instance.user_id).get(nickname=nickname)
        except User.DoesNotExist:
            return nickname

        raise forms.ValidationError('Nickname already exists.')

    def clean_email_address(self):
        email_address = self.cleaned_data['email_address']

        # check if email address is missing
        if not email_address:
            raise forms.ValidationError('Email Address is missing.')

        # check if email address submitted is the same as the current user online
        if email_address == self.instance.email_address:
            return email_address

        # email address is different from previous, check if it already exits
        try:
            User.objects.exclude(pk=self.instance.user_id).get(email_address=email_address)
        except User.DoesNotExist:
            return email_address

        raise forms.ValidationError('Email Address already exists')

    class Meta:
        model = User
        fields = ['first_name', 'last_name','nickname','email_address']


class AddressForm(ModelForm):
    street_address = forms.CharField(max_length=255, label="Street Address")
    city = forms.CharField(max_length=50, label="City")
    state = forms.CharField(max_length=2, label="State")
    zip_code = forms.CharField(max_length=5, label="Zip Code")

    def clean_zip_code(self):
        zip_code = self.cleaned_data['zip_code']
        if not zip_code.isdigit():
            raise forms.ValidationError('Zip Code can only contains numbers.')

        if len(zip_code) != 5:
            raise forms.ValidationError('Zip Code must have length of 5 digits.')

        return zip_code

    def clean_state(self):
        state = self.cleaned_data['state']
        if not state.isalpha():
            raise forms.ValidationError('State can only contain letters.')

        return state

    class Meta:
        model = Address
        fields = ['street_address', 'city', 'state', 'zip_code']


