from django.contrib import admin
from django.urls import path
from vending import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('purchase/', views.purchase_form, name='purchase_form'),  # <-- form to insert denominations
    path('buy/<int:product_id>/', views.purchase_product, name='purchase_product'),  # quick buy
]
