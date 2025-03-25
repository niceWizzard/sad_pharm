from django.contrib import admin

from .models import InventoryItem, InventoryStock, InventoryTransaction, StockRecord

# Register your models here.
@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["stocks"] + [field.name for field in InventoryItem._meta.fields] 
admin.site.register(
    InventoryTransaction,
)

admin.site.register(
    StockRecord
)

@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    list_display = ("item", "expiration_date", "quantity", "date_of_delivery")
    list_filter = ("expiration_date",)
    search_fields = ("item__name",)
