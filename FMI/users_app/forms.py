from django import forms
from users_app.models import LogMessage

class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    street = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    housenumber = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    zip = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}), required=False)    
    is_active = forms.BooleanField(widget=forms.TextInput(attrs={'class':'form-control'}))
    is_admin = forms.BooleanField(widget=forms.TextInput(attrs={'class':'form-control'}))
    date_of_birth = forms.DateField(widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    date_joined = forms.DateField(widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    last_login = forms.DateField(widget=forms.TextInput(attrs={'class':'form-control'}), required=False)


class LogMessageForm(forms.ModelForm):
    class Meta:
        model = LogMessage
        fields = ("message",)   # NOTE: the trailing comma is required