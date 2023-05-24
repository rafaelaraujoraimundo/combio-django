from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.forms.widgets import CheckboxSelectMultiple
from .models import User


class CustomUserCreationForm(UserCreationForm):
    usuario_datasul = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'teste'})
    )

    class Meta:
        model = User
        fields = ('email', 'usuario_datasul', 'usuario_fluig', )
        widget = {
            'usuario_datasul':
            forms.TextInput(attrs={'class': 'teste'})

        }


class CustomUserChangeForm(UserChangeForm):

    usuario_datasul = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Groups"
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(codename__icontains='combio'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Permissions"
    )

    class Meta:
        model = User
        fields = ('email', 'usuario_datasul', 'usuario_fluig',
                  'groups', 'user_permissions', 'is_active')

        widgets = {
            'usuario_fluig': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
        }
