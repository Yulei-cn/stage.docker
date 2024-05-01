from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from decimal import Decimal
import logging
import socket

from .models import Table, Order, Order_item, Boisson, Category
from .forms import New_order_form, login_form
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

def is_superuser(user):
    return user.is_superuser  # 可以根据需要扩展更多的条件，例如检查用户是否属于某个特定组

@login_required
@user_passes_test(is_superuser)
def clear_all_orders(request):
    if request.method == 'POST':
        # 执行清空所有订单的操作
        # 注意：这里要确保操作安全性，避免误操作
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 可选：注册后直接登录
            return redirect('table_list')  # 修改为适当的重定向目标
    else:
        form = RegisterForm()
    return render(request, 'restaurant/register.html', {'form': form})

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_to_printer(data):
    printer_ip = '192.168.1.100'
    printer_port = 9100
    cut_paper_command = b'\x1d\x56\x41\x03'  # ESC/POS 命令用于切纸
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((printer_ip, printer_port))
            sock.sendall(data.encode('gb18030') + cut_paper_command)  # 发送数据后切纸
            return True
    except Exception as e:
        logging.error(f"Échec de l'envoi à l'imprimante : {e}")
    return False



def prepare_print_data(order, boissons, order_items):
    """ Préparer les données d'impression pour la commande """
    print_data = f"Détails de la commande :\nNuméro de table : {order.table.name if order.table else 'Aucune'}\n"
    print_data += f"Adultes : {order.adults}, Enfants : {order.kids}, Petits enfants : {order.toddlers}\n"
    for item in order_items:
        boisson = next((b for b in boissons if b.id == item.boisson_id), None)
        if boisson:
            print_data += f"{boisson.name} x {item.quantity}\n"
    return print_data


@login_required(redirect_field_name="login_view")
def table_list(request):
    table_list = Table.objects.all()
    for t in table_list:
        order_active=t.orders.all().filter(status='Active').first()
        t.active=order_active.id if order_active else None
    return render(request, 'restaurant/table_list.html', {'tables': table_list})

def add_table(request):
    if request.method == 'POST':
        # 在这里处理添加新桌子的逻辑
        new_table = Table()  # 假设 'tables' 是你的桌子模型
        new_table.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def base(request):
    pass

@login_required(redirect_field_name="login_view")
def table_detail(request, table_id):
    pass

@login_required(redirect_field_name="login")
def add_order_item(request):
    table_id = request.GET.get('table_id')
    table_this = Table.objects.get(id=table_id)
    order_active = Table.objects.get(id=table_id).orders.all().filter(status='Active').first()
    categories = Category.objects.all()
    boissons = Boisson.objects.all()
    new_form = New_order_form()

    if request.method == 'POST':
        form = New_order_form(request.POST)
        if form.is_valid():
            adults = form.cleaned_data.get('adults')
            toddlers = form.cleaned_data.get('toddlers')
            kids = form.cleaned_data.get('kids')
            prix_boisson = 0

            if order_active:
                order_active.adults = adults
                order_active.kids = kids
                order_active.toddlers = toddlers
                order_active.user = request.user
                order_active.save()

                boisson_ordered = Order_item.objects.filter(order=order_active).all()
                for b in boissons:
                    quantity = form.cleaned_data.get(f'boisson_{b.id}')
                    if quantity:
                        b_old, created = boisson_ordered.get_or_create(boisson=b, defaults={'quantity': quantity}, order=order_active)
                        b_old.quantity = quantity
                        b_old.save()
                        prix_boisson += b.prix * int(quantity)

                # 生成打印数据并发送到打印机
                print_data = prepare_print_data(order_active, boissons, boisson_ordered)
                send_to_printer(print_data)

                return render(request, 'restaurant/add_order_item.html', {
                    'adults': order_active.adults,
                    'kids': order_active.kids,
                    'toddlers': order_active.toddlers,
                    'boissons': boissons,
                    'form': new_form,
                    'categories': categories,
                    'order': order_active
                })

            else:
                new_order = Order(adults=adults, kids=kids, toddlers=toddlers, table=table_this)
                new_order.user = request.user
                new_order.save()

                for b in boissons:
                    quantity = form.cleaned_data.get(f'boisson_{b.id}')
                    if quantity:
                        new_order_item = Order_item(quantity=quantity, boisson=b, order=new_order)
                        new_order_item.save()
                        prix_boisson += b.prix * int(quantity)

                # 生成打印数据并发送到打印机
                new_boisson_ordered = Order_item.objects.filter(order=new_order).all()
                print_data = prepare_print_data(new_order, boissons, new_boisson_ordered)
                send_to_printer(print_data)

                return render(request, 'restaurant/add_order_item.html', {
                    'adults': new_order.adults,
                    'kids': new_order.kids,
                    'toddlers': new_order.toddlers,
                    'boissons': boissons,
                    'form': new_form,
                    'categories': categories,
                    'order': new_order
                })
    else:
        if order_active:
            boisson_ordered = Order_item.objects.filter(order=order_active).all()
            for b in boissons:
                b.quantity = boisson_ordered.filter(boisson_id=b.id).values_list("quantity", flat=True).first() if boisson_ordered.filter(boisson_id=b.id).exists() else 0
            return render(request, 'restaurant/add_order_item.html', {
                'adults': order_active.adults,
                'kids': order_active.kids,
                'toddlers': order_active.toddlers,
                'boissons': boissons,
                'form': new_form,
                'categories': categories,
                'order': order_active
            })
        else:
            for b in boissons:
                b.quantity = 0
            return render(request, 'restaurant/add_order_item.html', {
                'adults': 0,
                'kids': 0,
                'toddlers': 0,
                'boissons': boissons,
                'form': new_form,
                'categories': categories,
                'order': None
            })



@login_required(redirect_field_name="login")    
def some_view(request):
    total_orders = Order.objects.count()  # 获取所有订单的总数
    accepted_orders = Order.objects.filter(status='Active').count()  # 获取状态为"Active"的订单总数

    context = {
        'total_orders': total_orders,
        'accepted_orders': accepted_orders,
    }
    return render(request, 'restaurant/cashier_summary.html', context)

@login_required(redirect_field_name="login")
def cashier_summary(request):
    total_orders = Order.objects.count()  # 获取所有订单的总数
    accepted_orders = Order.objects.filter(status='Active').count()  # 获取状态为"Active"的订单总数
    active_orders = Order.objects.filter(status='Active').prefetch_related('order_item_set__boisson').order_by('-updated_at')
    
    # 使用请求头部替代 is_ajax()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': order.id,
            'updated_at': order.updated_at.strftime('%d %b %Y at %H:%M'),
            'table': order.table.name if order.table else 'No table',
            'adults': order.adults,
            'kids': order.kids,
            'toddlers': order.toddlers,
            'items': [{'name': item.boisson.name, 'quantity': item.quantity} for item in order.order_item_set.all()],
            'total_price': float(sum(item.boisson.prix * item.quantity for item in order.order_item_set.all()) + 
                               Decimal(order.adults) * Decimal('15.8') +
                               Decimal(order.kids) * Decimal('12.8') +
                               Decimal(order.toddlers) * Decimal('9.8')),
            'username': order.user.username if order.user else 'Anonymous'
        } for order in active_orders]
        return JsonResponse(data, safe=False)

    return render(request, 'restaurant/cashier_summary.html', {
        'total_orders': total_orders,
        'accepted_orders': accepted_orders,
        'orders': active_orders  # 确保这个也被传递
    })



def login_view(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        print(user)
        if user is not None:
            login(request, user)
            return redirect('table_list')
        else:
            form = login_form()
            return render(request, 'restaurant/login.html', {'form': form})
    else:
        form = login_form()
        return render(request, 'restaurant/login.html', {'form': form})
    
    
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(redirect_field_name="login")
def clear_all_orders(request):
    if request.method == 'POST':
        # 获取所有订单
        orders = Order.objects.all()

        # 首先删除所有相关的订单项
        for order in orders:
            Order_item.objects.filter(order=order).delete()

        # 然后删除所有订单
        orders.delete()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
    
@login_required
def checkout_and_reset_table(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    order = table.orders.filter(status='Active').first()

    if order:
        # 获取订单相关的饮品和订单项
        boissons = Boisson.objects.all()
        order_items = Order_item.objects.filter(order=order)

        # 更新订单状态为已完成
        order.status = 'Completed'
        order.save()

        # 生成打印数据并发送到打印机
        print_data = prepare_print_data(order, boissons, order_items)
        send_to_printer(print_data)

        messages.success(request, "订单已成功结账并已准备迎接新客人")
    else:
        messages.error(request, "没有找到活跃订单")

    return redirect('table_list')

