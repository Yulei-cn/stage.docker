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
import socket,json

from datetime import datetime
from .models import Table, Order, Order_item, Boisson, Category
from .forms import New_order_form, login_form
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime

def get_pricing(adults, kids, toddlers):
    now = datetime.now()
    current_hour = now.hour
    current_weekday = now.weekday()
    current_date = datetime.now().date()
    current_year = datetime.now().year
    vacance = [
        datetime(current_year, 4, 1).date(), datetime(current_year, 5, 1).date(),
        datetime(current_year, 5, 8).date(), datetime(current_year, 5, 9).date(),
        datetime(current_year, 5, 20).date(), datetime(current_year, 7, 14).date(),
        datetime(current_year, 8, 15).date(), datetime(current_year, 11, 1).date(),
        datetime(current_year, 11, 11).date(), datetime(current_year, 12, 25).date(),
    ]
    
    # 设置午餐和晚餐的时间段    
    lunch_time = (12, 15)  # 从12点到15点
    dinner_time = (18, 23)  # 从18点到23点
    weekend = (5, 6)  # 星期六和星期日

    # 默认价格
    prices = {
        'adults': 15.8,
        'kids': 12.8,
        'toddlers': 9.8
    }

    # 首先检查是否是假日，然后再根据时间段判断
    if current_date in vacance:
        prices = {
            'adults': 22.8,
            'kids': 17.8,
            'toddlers': 9.8
        }
    elif (lunch_time[0] <= current_hour < lunch_time[1]) and current_weekday not in weekend:
        # 如果不是假日但是在午餐时间段
        prices = {
            'adults': 15.8,
            'kids': 12.8,
            'toddlers': 9.8
        }
    elif (dinner_time[0] <= current_hour < dinner_time[1]) or current_weekday in weekend:
        # 如果是晚餐时间或周末
        prices = {
            'adults': 22.8,
            'kids': 17.8,
            'toddlers': 9.8
        }

    # 计算总价格
    total_price = (prices['adults'] * float(adults) +
                   prices['kids'] * float(kids) +
                   prices['toddlers'] * float(toddlers))

    return total_price



from django.views.decorators.csrf import csrf_exempt, csrf_protect

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
    printer_ip = '192.168.1.101'
    printer_port = 9100
    cut_paper_command = b'\x1d\x56\x41\x03'  # ESC/POS 命令用于切纸
    font_size_command = b'\x1d\x21\x11'  # 设置字体为双宽双高
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((printer_ip, printer_port))
            sock.sendall(font_size_command)  # 先发送字体设置命令
            sock.sendall(data.encode('gb18030') + cut_paper_command)  # 发送数据后切纸
            return True
    except Exception as e:
        logging.error(f"Échec de l'envoi à l'imprimante : {e}")
    return False


def prepare_print_data(order, boissons, order_items):
    # Define headers and footers with proper alignment
    header = "A LA CIGOGNE\n"  # Center the restaurant name
    footer = "\n\n感谢您的光临!\nMerci de votre venue\n".center(30)  # Center the thank you note
    
    # Build the body with order details
    print_data = "Details de la commande :\n"  # Start the order details (left-aligned by default)
    table_info = order.table.name if order.table else 'Aucune'
    print_data += f"Numero de table : {table_info}\n"
    print_data += f"Adultes : {order.adults}\nEnfants : {order.kids}\nPetits enfants : {order.toddlers}\n"
    
    # Process each ordered item
    for item in order_items:
        boisson = next((b for b in boissons if b.id == item.boisson_id), None)
        if boisson:
            print_data += f"{boisson.name} x {item.quantity}\n"  # Add each item

    # Concatenate all parts to form the final print-ready data
    complete_print_data = header + print_data + footer

    return complete_print_data


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
    
    initial_boisson = {} 
    #如果表单被提交
    if request.method == 'POST':
        form = New_order_form(request.POST)
        if form.is_valid():
            adults = form.cleaned_data.get('adults')
            toddlers = form.cleaned_data.get('toddlers')
            kids = form.cleaned_data.get('kids')
            prix_boisson = 0
            #更新订单
            if order_active:
                order_active.adults = adults
                order_active.kids = kids
                order_active.toddlers = toddlers
                order_active.user = request.user
                order_active.save()
                messages.success(request, 'Commande mise à jour avec succès。')
                boisson_ordered = Order_item.objects.filter(order=order_active).all()
                for b in boissons:
                    quantity = form.cleaned_data.get(f'boisson_{b.id}')
                    if quantity:
                        b.quantity=quantity
                        b_old, created = boisson_ordered.get_or_create(boisson=b, defaults={'quantity': quantity}, order=order_active)    
                        b_old.quantity = quantity
                        b_old.save()
                        prix_boisson += b.prix * int(quantity)
                        
                        initial_boisson[f'boisson_{b.id}']=quantity
                    else:
                        order_item = Order_item.objects.filter(order=order_active, boisson=b).first()
                        if order_item:
                            order_item.delete()  # 正确的删除方法
                prix_person=get_pricing(adults,kids,toddlers)
                order_active.prix=prix_person+float(prix_boisson)
                order_active.save()
                # 生成打印数据并发送到打印机
                #print_data = prepare_print_data(order_active, boissons, boisson_ordered)
                #send_to_printer(print_data)
                new_form = New_order_form(initial=initial_boisson)
                return render(request, 'restaurant/add_order_item.html', {
                    'adults': order_active.adults,
                    'kids': order_active.kids,
                    'toddlers': order_active.toddlers,
                    'boissons': boissons,
                    'form': new_form,
                    'categories': categories,
                    'order': order_active
                })
            #创建订单
            else:
                new_order = Order(adults=adults, kids=kids, toddlers=toddlers, table=table_this)
                new_order.user = request.user
                new_order.save()
                messages.success(request, 'La nouvelle commande a été créée avec succès。')

                for b in boissons:
                    quantity = form.cleaned_data.get(f'boisson_{b.id}')
                    if quantity:
                        new_order_item = Order_item(quantity=quantity, boisson=b, order=new_order)
                        new_order_item.save()
                        prix_boisson += b.prix * int(quantity)
                        b.quantity=quantity
                        initial_boisson[f'boisson_{b.id}']=quantity
                    else:
                        b.quantity=0
                        initial_boisson[f'boisson_{b.id}']=0
                # 生成打印数据并发送到打印机
                new_boisson_ordered = Order_item.objects.filter(order=new_order).all()
                print_data = prepare_print_data(new_order, boissons, new_boisson_ordered)
                send_to_printer(print_data)
                prix_person=get_pricing(adults,kids,toddlers)
                new_order.prix=prix_person+float(prix_boisson)
                new_order.save()
                new_form = New_order_form(initial=initial_boisson)
                return render(request, 'restaurant/add_order_item.html', {
                    'adults': new_order.adults,
                    'kids': new_order.kids,
                    'toddlers': new_order.toddlers,
                    'boissons': boissons,
                    'form': new_form,
                    'categories': categories,
                    'order': new_order
                })
    #渲染页面
    else:
        #如果订单存在直接显示
        if order_active:
            boisson_ordered = Order_item.objects.filter(order=order_active).all()
            for b in boissons:
                b.quantity = boisson_ordered.filter(boisson_id=b.id).values_list("quantity", flat=True).first() if boisson_ordered.filter(boisson_id=b.id).exists() else 0
                initial_boisson[f'boisson_{b.id}']=b.quantity
            new_form=New_order_form(initial=initial_boisson)
            return render(request, 'restaurant/add_order_item.html', {
                'adults': order_active.adults,
                'kids': order_active.kids,
                'toddlers': order_active.toddlers,
                'boissons': boissons,
                'form': new_form,
                'categories': categories,
                'order': order_active
            })
        #创建新订单表单
        else:
            for b in boissons:
                b.quantity = 0
            new_form = New_order_form()
            return render(request, 'restaurant/add_order_item.html', {
                'adults': 0,
                'kids': 0,
                'toddlers': 0,
                'boissons': boissons,
                'form': new_form,
                'categories': categories,
                'order': 'null'
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
    if request.method == 'POST':
        body_str = request.body.decode('utf-8')
        data = json.loads(body_str)
        item_delete=Order_item.objects.filter(id=data.get('id_delete')).all()
        item_delete.delete()
        return JsonResponse({'success': True})
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
        #print_data = prepare_print_data(order, boissons, order_items)
        #send_to_printer(print_data)

        messages.success(request, "订单已成功结账并已准备迎接新客人La commande a été validée avec succès et est prête à accueillir de nouveaux invités")
    else:
        messages.error(request, "没有找到活跃订单")

    return redirect('table_list')

@csrf_exempt
def test_webhook(request):
    if request.method == 'GET':
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': True})

from django.views.decorators.http import require_http_methods
@require_http_methods(["GET"])
def show_books(request):
    response={}
    try:
        response['a']='a'
        response['b']='b'
    except Exception as e:
        pass
    return JsonResponse(response)