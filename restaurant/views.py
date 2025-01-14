from datetime import datetime, timedelta
from decimal import Decimal
import logging
import socket
import json
import pytz

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils import translation
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDay
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import Table, Order, Order_item, Boisson, Category, Reservation
from .forms import New_order_form, login_form, RegisterForm, PersonalReservationForm, GroupReservationForm

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from django.contrib.auth.decorators import user_passes_test

@csrf_exempt
@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_pricing(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        price_type = data.get('price_type')
        
        # 根据请求的价格类型更新价格
        orders = Order.objects.filter(status='Active')  # 获取所有活跃订单
        for order in orders:
            adults, kids, toddlers = order.adults, order.kids, order.toddlers
            
            # 设置假期和平日的价格
            holiday_prices = {'adults': 22.8, 'kids': 17.8, 'toddlers': 9.8}
            weekday_prices = {'adults': 15.8, 'kids': 12.8, 'toddlers': 9.8}
            
            if price_type == 'holiday':
                prices = holiday_prices
            elif price_type == 'weekday':
                prices = weekday_prices
            else:
                return JsonResponse({'success': False, 'error': 'Invalid price type'})
            
            # 更新订单价格
            order.prix = (
                prices['adults'] * adults +
                prices['kids'] * kids +
                prices['toddlers'] * toddlers
            )
            order.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def make_reservation(request):
    user_language = request.GET.get('lang')
    if user_language:
        translation.activate(user_language)
        request.session[settings.LANGUAGE_COOKIE_NAME] = user_language

    reservation_type = request.GET.get('reservation_type')

    if not reservation_type:
        return render(request, 'restaurant/make_reservation.html', {'user_language': translation.get_language()})

    if request.method == 'POST':
        if reservation_type == 'group':
            form = GroupReservationForm(request.POST)
        else:
            form = PersonalReservationForm(request.POST)

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            messages.success(request, _('预定成功！'))
            return redirect('reservation_success')
        else:
            messages.error(request, _('请填写所有必填字段。'))
    else:
        if reservation_type == 'group':
            form = GroupReservationForm()
        else:
            form = PersonalReservationForm()
        language_code = translation.get_language()

    return render(request, 'restaurant/make_reservation.html', {'form': form, 'user_language': language_code})

@login_required
def reservation_list(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date')
    return render(request, 'restaurant/reservation_list.html', {'reservations': reservations})



@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    print(f"Order created_at: {order.created_at}")
    print(f"Order table: {order.table}")
    
    try:
        reservation = Reservation.objects.filter(table=order.table, reservation_date=order.created_at.date()).first()
        if reservation:
            print(f"Reservation found: {reservation}")
        else:
            print("No reservation found.")
    except Reservation.DoesNotExist:
        reservation = None
        print("No reservation found for this order.")
    
    return render(request, 'restaurant/cashier_summary.html', {
        'order': order,
        'reservation': reservation
    })




def reservation_success(request):
    return render(request, 'restaurant/reservation_success.html')

def is_superuser(user):
    return user.is_superuser

@require_POST
def print_order(request):
    data = json.loads(request.body)
    order_id = data.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    boissons = Boisson.objects.all()
    order_items = Order_item.objects.filter(order=order)
    
    print_data = prepare_print_data(order, boissons, order_items)
    success = send_to_printer(print_data)
    
    if success:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
    

@user_passes_test(is_superuser)
def sales_overview(request):
    today = timezone.now()
    start_date = today - timedelta(days=7)
    previous_start_date = start_date - timedelta(days=7)

    # 当前周期数据
    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    accepted_orders = Order.objects.filter(status='Accepted', created_at__gte=start_date).count()
    completed_orders = Order.objects.filter(status='Completed', created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(status='Completed', created_at__gte=start_date).aggregate(total=Sum('prix'))['total'] or 0

    average_prep_time = Order.objects.filter(status='Completed', completed_at__isnull=False).annotate(
        prep_time=ExpressionWrapper(F('completed_at') - F('created_at'), output_field=DurationField())
    ).aggregate(avg_prep_time=Avg('prep_time'))

    # 之前周期数据
    prev_accepted_orders = Order.objects.filter(status='Accepted', created_at__gte=previous_start_date, created_at__lt=start_date).count()
    prev_total_revenue = Order.objects.filter(status='Completed', created_at__gte=previous_start_date, created_at__lt=start_date).aggregate(total=Sum('prix'))['total'] or 0
    prev_average_prep_time = Order.objects.filter(status='Completed', completed_at__isnull=False, created_at__gte=previous_start_date, created_at__lt=start_date).annotate(
        prep_time=ExpressionWrapper(F('completed_at') - F('created_at'), output_field=DurationField())
    ).aggregate(avg_prep_time=Avg('prep_time'))

    # 计算百分比变化
    accepted_orders_change = ((accepted_orders - prev_accepted_orders) / prev_accepted_orders * 100) if prev_accepted_orders else 0
    revenue_change = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue else 0
    average_prep_time_change = ((average_prep_time['avg_prep_time'] - prev_average_prep_time['avg_prep_time']).total_seconds() / prev_average_prep_time['avg_prep_time'].total_seconds() * 100) if prev_average_prep_time['avg_prep_time'] else 0

    formatted_avg_prep_time = "{:.2f} minutes".format(average_prep_time['avg_prep_time'].total_seconds() / 60 if average_prep_time['avg_prep_time'] else 0)

    daily_completed_orders = Order.objects.filter(
        status='Completed',
        completed_at__date__gte=start_date
    ).annotate(date=TruncDay('completed_at')).values('date').annotate(count=Count('id')).order_by('date')

    dates = [order['date'].strftime('%d %b') for order in daily_completed_orders]
    counts = [order['count'] for order in daily_completed_orders]

    context = {
        'total_orders': total_orders,
        'accepted_orders': accepted_orders,
        'completed_orders': completed_orders,
        'average_prep_time': formatted_avg_prep_time,
        'accepted_orders_change': accepted_orders_change,
        'average_prep_time_change': average_prep_time_change,
        'revenue': total_revenue,
        'revenue_change': revenue_change,
        'dates': json.dumps(dates),  # 使用 json.dumps 确保数据格式正确
        'counts': json.dumps(counts),  # 使用 json.dumps 确保数据格式正确
    }

    return render(request, 'sales_overview.html', context)



def get_pricing(adults, kids, toddlers):
    now = timezone.now().astimezone(pytz.timezone('Europe/Paris'))  # 转换为巴黎时间
    current_hour = now.hour
    current_weekday = now.weekday()
    current_date = now.date()
    current_year = now.year

    # 日志信息
    logging.info(f"Current datetime (Paris time): {now}")
    logging.info(f"Current hour: {current_hour}, Current weekday: {current_weekday}, Current date: {current_date}")

    # 设置假期列表
    # 设置假期列表
    vacance = [
        timezone.datetime(current_year, 2, 14, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 3, 4, tzinfo=pytz.timezone('Europe/Paris')).date(),   # 新增假期
        timezone.datetime(current_year, 3, 30, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 4, 1, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 4, 20, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 4, 21, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 5, 1, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 5, 8, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 5, 25, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期 
        timezone.datetime(current_year, 5, 29, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 更新到2025年的日期
        timezone.datetime(current_year, 6, 9, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 更新到2025年的日期
        timezone.datetime(current_year, 6, 15, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 6, 21, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 7, 14, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 8, 15, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 10, 26, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 11, 1, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 11, 11, tzinfo=pytz.timezone('Europe/Paris')).date(),
        timezone.datetime(current_year, 11, 31, tzinfo=pytz.timezone('Europe/Paris')).date(),  # 新增假期
        timezone.datetime(current_year, 12, 25, tzinfo=pytz.timezone('Europe/Paris')).date(),
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
    if current_date in vacance or (dinner_time[0] <= current_hour < dinner_time[1]) or current_weekday in weekend:
        prices = {
            'adults': 22.8,
            'kids': 17.8,
            'toddlers': 9.8
        }
        logging.info("Dinner time or vacation pricing applied")
    elif (lunch_time[0] <= current_hour < lunch_time[1]) and current_weekday not in weekend:
        # 如果不是假日但是在午餐时间段
        prices = {
            'adults': 15.8,
            'kids': 12.8,
            'toddlers': 9.8
        }
        logging.info("Lunch time pricing applied")

    # 计算总价格
    total_price = (prices['adults'] * float(adults) +
                   prices['kids'] * float(kids) +
                   prices['toddlers'] * float(toddlers))

    return total_price



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

    # 如果表单被提交
    if request.method == 'POST':
        form = New_order_form(request.POST)
        if form.is_valid():
            adults = form.cleaned_data.get('adults')
            toddlers = form.cleaned_data.get('toddlers')
            kids = form.cleaned_data.get('kids')
            prix_boisson = 0

            # 更新订单
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
                        b.quantity = quantity
                        b_old, created = boisson_ordered.get_or_create(boisson=b, defaults={'quantity': quantity}, order=order_active)
                        b_old.quantity = quantity
                        b_old.save()
                        prix_boisson += b.prix * int(quantity)
                        initial_boisson[f'boisson_{b.id}'] = quantity
                    else:
                        order_item = Order_item.objects.filter(order=order_active, boisson=b).first()
                        if order_item:
                            order_item.delete()

                # 处理自定义饮料
                custom_drinks = json.loads(request.POST.get('custom_drinks', '[]'))
                for custom_drink in custom_drinks:
                    name = custom_drink.get('name')
                    price = custom_drink.get('price')
                    if name and price:
                        custom_boisson = Boisson.objects.create(name=name, prix=Decimal(price), category=None)
                        Order_item.objects.create(order=order_active, boisson=custom_boisson, quantity=1)
                        prix_boisson += Decimal(price)

                prix_person = get_pricing(adults, kids, toddlers)
                order_active.prix = prix_person + float(prix_boisson)
                order_active.save()

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
            # 创建订单
            else:
                new_order = Order(adults=adults, kids=kids, toddlers=toddlers, table=table_this, created_at=timezone.now())
                new_order.user = request.user
                new_order.save()
                messages.success(request, 'La nouvelle commande a été créée avec succès。')

                for b in boissons:
                    quantity = form.cleaned_data.get(f'boisson_{b.id}')
                    if quantity:
                        new_order_item = Order_item(quantity=quantity, boisson=b, order=new_order)
                        new_order_item.save()
                        prix_boisson += b.prix * int(quantity)
                        b.quantity = quantity
                        initial_boisson[f'boisson_{b.id}'] = quantity
                    else:
                        b.quantity = 0
                        initial_boisson[f'boisson_{b.id}'] = 0

                # 处理自定义饮料
                custom_drinks = json.loads(request.POST.get('custom_drinks', '[]'))
                for custom_drink in custom_drinks:
                    name = custom_drink.get('name')
                    price = custom_drink.get('price')
                    if name and price:
                        custom_boisson = Boisson.objects.create(name=name, prix=Decimal(price), category=None)
                        Order_item.objects.create(order=new_order, boisson=custom_boisson, quantity=1)
                        prix_boisson += Decimal(price)

                prix_person = get_pricing(adults, kids, toddlers)
                new_order.prix = prix_person + float(prix_boisson)
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
    # 渲染页面
    else:
        # 如果订单存在直接显示
        if order_active:
            boisson_ordered = Order_item.objects.filter(order=order_active).all()
            custom_drinks = Order_item.objects.filter(order=order_active, boisson__category=None)
            for b in boissons:
                b.quantity = boisson_ordered.filter(boisson_id=b.id).values_list("quantity", flat=True).first() if boisson_ordered.filter(boisson_id=b.id).exists() else 0
                initial_boisson[f'boisson_{b.id}'] = b.quantity
            new_form = New_order_form(initial=initial_boisson)
            return render(request, 'restaurant/add_order_item.html', {
                'adults': order_active.adults,
                'kids': order_active.kids,
                'toddlers': order_active.toddlers,
                'boissons': boissons,
                'form': new_form,
                'categories': categories,
                'order': order_active,
                'custom_drinks': custom_drinks
            })
        # 创建新订单表单
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
                'order': 'null',
                'custom_drinks': []
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
@user_passes_test(is_superuser)
def checkout_all_orders(request):
    if request.method == 'POST':
        # 获取所有未结账的订单
        active_orders = Order.objects.filter(status='Active')

        # 遍历每个订单并进行结账处理
        for order in active_orders:
            order.status = 'Completed'
            order.completed_at = timezone.now()  # 设置结账时间
            order.save()

            # 可以在这里添加更多的结账逻辑，比如更新库存，生成发票等
            # 例如：prepare_print_data(order, boissons, order_items) 并发送到打印机

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
        order.completed_at = timezone.now()  # 使用 timezone.now() 代替 datetime.now()
        order.save()

        # 生成打印数据并发送到打印机
        # print_data = prepare_print_data(order, boissons, order_items)
        # send_to_printer(print_data)

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

def tag_cloud_view(request):
    # 处理标签云的数据和逻辑
    context = {}
    return render(request, 'tagcloud.html', context)

def test_view(request):
    return render(request, 'test.html')

@login_required
def quick_add_coffee(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    order = Order.objects.filter(table=table, status='Active').first()

    if not order:
        # 如果没有活跃的订单，可以选择创建一个新订单，或返回错误/警告
        messages.error(request, "No active order found to add coffee.")
        return redirect('table_list')

    coffee = Boisson.objects.get(id=7)  # 咖啡的ID为7

    # 尝试获取现有的咖啡订单项或创建一个新的
    order_item, created = Order_item.objects.get_or_create(
        order=order,
        boisson=coffee,
        defaults={'quantity': 1}
    )
    if not created:
        order_item.quantity += 1
        order_item.save()

    # 重新计算订单总价
    existing_total = Decimal(order.prix if order.prix else 0)  # 确保没有None导致的错误
    additional_price = coffee.prix
    order.prix = existing_total + additional_price
    order.save()

    messages.success(request, "Café successfully added.")
    return redirect('table_list')


def update_order_total(order):
    total_price = 0
    for item in order.order_item_set.all():
        total_price += item.boisson.prix * item.quantity
    order.prix = total_price
    order.save()


