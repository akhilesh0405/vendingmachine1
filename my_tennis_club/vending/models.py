from django.db import models
from django.utils import timezone

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('cake', 'Cake'),
        ('drink', 'Soft Drink'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    price = models.FloatField()
    quantity_left = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.category})"


class TransactionLog(models.Model):
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    amount_inserted = models.DecimalField(max_digits=10, decimal_places=2)
    inserted_details = models.CharField(max_length=255)
    change_returned = models.DecimalField(max_digits=10, decimal_places=2)
    change_details = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date} - {self.amount_inserted} -> Change: {self.change_returned}"
