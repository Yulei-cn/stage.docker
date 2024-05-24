from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Boisson(models.Model):
    name = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=5, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='boissons')

    def __str__(self):
        return self.name


class Table(models.Model):
    name=models.CharField(max_length=20,null=True)


class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, related_name='orders', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    adults = models.IntegerField(default=0)
    kids = models.IntegerField(default=0)
    toddlers = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='Active')
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    status = models.CharField(max_length=20, default='Active')  # 新增字段用于标记订单状态

class Order_item(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    boisson = models.ForeignKey(Boisson,on_delete=models.CASCADE)
    quantity = models.IntegerField()

