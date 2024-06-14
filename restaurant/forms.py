from django import forms
from .models import Table, Order, Order_item, Boisson, Category, Reservation
from django.db import models
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import Reservation, Table
from django.utils.translation import gettext_lazy as _

class PersonalReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),  
        input_formats=['%Y-%m-%d'],  
        label=_('预定日期') 
    )
    reservation_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),  
        input_formats=['%H:%M'],  
        label=_('预定时间') 
    )
    reservation_type = forms.ChoiceField(
        choices=Reservation.RESERVATION_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label=_('预定类型')
    )
    name = forms.CharField(max_length=100, required=True, label=_('姓名'))
    phone = forms.CharField(max_length=15, required=True, label=_('电话'))
    table = forms.ModelChoiceField(queryset=Table.objects.all(), label=_('桌子'))
    guests = forms.IntegerField(min_value=1, label=_('人数'))

    class Meta:
        model = Reservation
        fields = ['table', 'reservation_date', 'reservation_time', 'guests', 'reservation_type', 'name', 'phone']

class GroupReservationForm(forms.ModelForm):
    company_name = forms.CharField(max_length=100, label=_('公司名称'))
    email = forms.EmailField(label=_('邮箱'))
    number_of_people = forms.IntegerField(label=_('人数'))
    group_type = forms.ChoiceField(choices=[('group_dinner', _('团体餐')), ('buffet', _('自助'))], label=_('团体餐还是自助'))
    reservation_time = forms.DateTimeField(label=_('预定时间'))

    class Meta:
        model = Reservation
        fields = ['company_name', 'email', 'number_of_people', 'group_type', 'reservation_time']
        labels = {
            'company_name': _('公司名称'),
            'email': _('邮箱'),
            'number_of_people': _('人数'),
            'group_type': _('团体餐还是自助'),
            'reservation_time': _('预定时间')
        }



class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")
        labels = {
            'username': _('Username'),
            'password1': _('Password'),
            'password2': _('Password confirmation'),
        }


class DeleteItemForm(forms.Form):
    id_delete = forms.IntegerField(label=_('ID to delete'))


class New_order_form(forms.Form):
    created_at = models.DateTimeField(auto_now_add=True)  # 添加时间戳字段
    adults = forms.IntegerField(label=_('Adults'), initial=0, widget=forms.HiddenInput())
    kids = forms.IntegerField(label=_('Kids'), initial=0, widget=forms.HiddenInput())
    toddlers = forms.IntegerField(label=_('Toddlers'), initial=0, widget=forms.HiddenInput())

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
    username = forms.CharField(label=_('Username'), widget=forms.TextInput(attrs={'class': 'form-control', 'required': ''}))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': ''}))
