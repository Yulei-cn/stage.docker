from django.urls import path
from . import views

from django.contrib import admin
urlpatterns = [
    path(r'^admin/', admin.site.urls),
    path('', views.table_list, name='table_list'),
    path('register/', views.register, name='register'),
    path('base/', views.base, name='base'),
    path('add_order_item/', views.add_order_item, name='add_order_item'),
    path('add_table/', views.add_table, name='add_table'),
    path('table/<int:table_id>/add_order_item/<int:order_id>/', views.add_order_item, name='add_order_item_with_order'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('checkout-all-orders/', views.checkout_all_orders, name='checkout_all_orders'),
    path('cashier_summary/', views.cashier_summary, name='cashier_summary'),
    path('table/<int:table_id>/checkout/', views.checkout_and_reset_table, name='checkout_and_reset_table'),
    path('test_webhook/',views.test_webhook,name="test_webhook"),
    path('show_books/',views.show_books,name='show_books'),
    path('tag-cloud/', views.tag_cloud_view, name='tag_cloud'),
    path('test/', views.test_view, name='test'),
    path('table/<int:table_id>/quick_add_coffee/', views.quick_add_coffee, name='quick_add_coffee'),
    path('sales-overview/', views.sales_overview, name='sales-overview'),
    path('print_order/', views.print_order, name='print_order'),
]
