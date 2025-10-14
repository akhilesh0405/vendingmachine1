from django.contrib import admin
from .models import Product, TransactionLog  

admin.site.register(Product)
admin.site.register(TransactionLog)
