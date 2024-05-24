from django import forms
from .models import Table, Order, Order_item, Boisson, Category
from django.db import models
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class Delete_item(forms.Form):
    id_delete=forms.IntegerField(label='id_delete')

class New_order_form(forms.Form):
    created_at = models.DateTimeField(auto_now_add=True)  # 添加时间戳字段
    adults = forms.IntegerField(label='adults', initial=0, widget=forms.HiddenInput())
    kids = forms.IntegerField(label='kids', initial=0, widget=forms.HiddenInput())
    toddlers = forms.IntegerField(label='toddlers', initial=0, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Category.objects.prefetch_related('boissons').all()
        for category in categories:
            for boisson in category.boissons.all():
                self.fields[f'boisson_{boisson.id}'] = forms.IntegerField(
                    label=f'{category.name} - {boisson.name}', 
                    initial=0,
                    widget=forms.HiddenInput(),
                    required=False
                )            


class login_form(AuthenticationForm):
    username= forms.CharField(label='username' ,widget=forms.TextInput(attrs={'class':'form-control','required':''}))
    password= forms.CharField(label='password' ,widget=forms.PasswordInput(attrs={'class':'form-control','required':''}))