from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.contrib.auth import get_user_model
User = get_user_model()

class UserDeleteForm(forms.Form):
    """
    Simple form that provides a checkbox that signals deletion.
    """
    password = forms.CharField(required=True)

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="メールアドレス", required=True)
    username = forms.CharField(label='名字', required=True)
    
    class Meta:
        model = User
        fields = ("email", "username")

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["username"]
         
        if commit:
            user.save()
        return user