from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Item, Transaction, Invoice, InvoiceItem, Activity, Profile
from jdatetime import datetime as jdatetime, date as jdate
import pytz

TEHRAN_TZ = pytz.timezone("Asia/Tehran")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    search_fields = ("user__username",)
    list_filter = ("role",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "stock",
        "min_stock",
        "unit",
        "category",
        "subcategory",
        "sale_price",
        "last_price",
        "profit_margin",
        "shipping_cost",
        "discount_percentage",
        "formatted_entry_date",
        "supplier_code",
        "manufacturer",
        "shelf",
        "location",
    )
    search_fields = (
        "name",
        "code",
        "category",
        "subcategory",
        "supplier_code",
        "manufacturer",
        "description",
        "shelf",
        "location",
    )
    list_filter = ("category", "subcategory", "unit", "entry_date")
    list_editable = ("stock", "min_stock", "sale_price")
    list_per_page = 20
    ordering = ("-entry_date",)
    readonly_fields = ("formatted_entry_date",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def formatted_entry_date(self, obj):
        if obj.entry_date:
            j_date = jdate.fromgregorian(date=obj.entry_date)
            return f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
        return "-"

    formatted_entry_date.short_description = "تاریخ ورود"
    formatted_entry_date.admin_order_field = "entry_date"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "type",
        "quantity",
        "price",
        "formatted_date",
        "user",
        "supplier",
        "destination",
        "notes",
    )
    search_fields = (
        "item__name",
        "item__code",
        "user__username",
        "supplier",
        "destination",
        "notes",
    )
    list_filter = ("type", "date", "supplier")
    list_per_page = 20
    raw_id_fields = ("item", "user")
    ordering = ("-date",)
    readonly_fields = ("formatted_date",)

    def formatted_date(self, obj):
        if obj.date:
            j_date = jdate.fromgregorian(date=obj.date)
            return f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
        return "-"

    formatted_date.short_description = "تاریخ"
    formatted_date.admin_order_field = "date"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "formatted_date",
        "total_amount",
        "user",
        "customer",
        "company_name",
        "company_phone",
        "company_address",
    )
    search_fields = (
        "number",
        "company_name",
        "company_phone",
        "company_address",
        "user__username",
        "customer__username",
    )
    list_filter = ("date", "user", "customer")
    list_per_page = 20
    raw_id_fields = ("user", "customer")
    ordering = ("-date",)
    readonly_fields = ("formatted_date",)

    def formatted_date(self, obj):
        if obj.date:
            j_date = jdate.fromgregorian(date=obj.date)
            return f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
        return "-"

    formatted_date.short_description = "تاریخ"
    formatted_date.admin_order_field = "date"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "item",
        "quantity",
        "unit_price",
        "get_total_price",
        "apply_profit",
        "apply_shipping",
        "apply_discount",
    )
    search_fields = ("invoice__number", "item__name", "item__code")
    list_filter = ("invoice__date", "apply_profit", "apply_shipping", "apply_discount")
    list_per_page = 20
    raw_id_fields = ("invoice", "item")
    ordering = ("-invoice__date",)

    def get_total_price(self, obj):
        return obj.get_total

    get_total_price.short_description = "جمع کل"
    get_total_price.admin_order_field = "quantity"


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "description", "formatted_date")
    search_fields = ("user__username", "description", "type")
    list_filter = ("type", "date")
    list_per_page = 20
    raw_id_fields = ("user",)
    ordering = ("-date",)
    readonly_fields = ("formatted_date",)

    def formatted_date(self, obj):
        if obj.date:
            local_dt = timezone.localtime(obj.date, TEHRAN_TZ)
            jdt = jdatetime.fromgregorian(
                year=local_dt.year,
                month=local_dt.month,
                day=local_dt.day,
                hour=local_dt.hour,
                minute=local_dt.minute,
                second=local_dt.second,
            )
            return f"{jdt.year}/{jdt.month:02d}/{jdt.day:02d} {jdt.hour:02d}:{jdt.minute:02d}"
        return "-"

    formatted_date.short_description = "تاریخ و زمان"
    formatted_date.admin_order_field = "date"
