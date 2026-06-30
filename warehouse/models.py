from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from jdatetime import date as jdate


class Profile(models.Model):
    ROLE_CHOICES = (
        ("admin", "ادمین"),
        ("customer", "مشتری"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="کاربر")
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="customer", verbose_name="نقش"
    )

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Item(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="کد کالا")
    name = models.CharField(max_length=100, verbose_name="نام کالا")
    description = models.TextField(blank=True, default="", verbose_name="توضیحات")
    shelf = models.CharField(max_length=50, blank=True, default="", verbose_name="قفسه")
    manufacturer = models.CharField(
        max_length=100, blank=True, default="", verbose_name="تولیدکننده"
    )
    category = models.CharField(
        max_length=50, blank=True, default="", verbose_name="دسته‌بندی"
    )
    subcategory = models.CharField(
        max_length=50, blank=True, default="", verbose_name="زیر‌دسته"
    )
    unit = models.CharField(
        max_length=20, default="عدد", blank=True, verbose_name="واحد"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی")
    min_stock = models.PositiveIntegerField(
        default=0, blank=True, verbose_name="حداقل موجودی"
    )
    location = models.CharField(
        max_length=100, blank=True, default="", verbose_name="مکان انبار"
    )
    last_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="آخرین قیمت خرید",
    )
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="درصد سود",
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="هزینه ارسال",
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="درصد تخفیف",
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="قیمت فروش",
    )
    entry_date = models.DateField(null=True, blank=True, verbose_name="تاریخ ورود")
    supplier_code = models.CharField(
        max_length=50, blank=True, default="", verbose_name="کد تأمین‌کننده"
    )
    image = models.URLField(blank=True, default="", verbose_name="تصویر")

    class Meta:
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"
        ordering = ["-code"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if Item.objects.exclude(pk=self.pk).filter(name__iexact=self.name).exists():
            raise ValidationError({"name": "کالایی با این نام قبلاً ثبت شده است."})

    def calculate_final_price(
        self, apply_profit=True, apply_shipping=True, apply_discount=True
    ):
        price = self.sale_price if self.sale_price else self.last_price
        if price == 0:
            return 0.00
        if apply_profit and self.profit_margin:
            price += price * (self.profit_margin / 100)
        if apply_shipping and self.shipping_cost:
            price += self.shipping_cost
        if apply_discount and self.discount_percentage:
            price -= price * (self.discount_percentage / 100)
        return max(round(price, 2), 0)


class Transaction(models.Model):
    TYPE_CHOICES = (
        ("in", "ورود"),
        ("out", "خروج"),
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="کالا")
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name="نوع")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    date = models.DateField(default=timezone.now, verbose_name="تاریخ")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    notes = models.TextField(
        blank=True, default="", verbose_name="یادداشت", db_index=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="قیمت واحد",
    )
    supplier = models.CharField(
        max_length=100, blank=True, default="", verbose_name="تأمین‌کننده"
    )
    destination = models.CharField(
        max_length=100, blank=True, default="", verbose_name="مقصد"
    )

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"

    def __str__(self):
        return f"{self.item.name} - {self.get_type_display()} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.type == "out" and self.quantity > self.item.stock:
                raise ValueError(f"موجودی کافی نیست. موجودی فعلی: {self.item.stock}")
            super().save(*args, **kwargs)
            if self.type == "in":
                self.item.stock += self.quantity
            else:
                self.item.stock -= self.quantity
            self.item.save()
        else:
            super().save(*args, **kwargs)


class Invoice(models.Model):
    number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="شماره فاکتور",
        db_index=True,
    )

    # date = models.DateField(default=timezone.now, verbose_name="تاریخ")
    date = models.DateField(default=timezone.now, verbose_name="تاریخ", db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="invoices_created",
        verbose_name="ادمین",
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices_as_customer",
        verbose_name="مشتری",
    )
    company_name = models.CharField(
        max_length=100, blank=True, default="", verbose_name="نام شرکت"
    )
    company_address = models.CharField(
        max_length=200, blank=True, default="", verbose_name="آدرس شرکت"
    )
    company_phone = models.CharField(
        max_length=20, blank=True, default="", verbose_name="تلفن شرکت"
    )
    # total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="مبلغ کل")
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="مبلغ کل",
        db_index=True,
    )

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"
        ordering = ["-number"]

    def __str__(self):
        return self.number

    def calculate_total(self):
        total = sum(item.get_total for item in self.items.all())
        self.total_amount = total
        self.save()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="items", on_delete=models.CASCADE, verbose_name="فاکتور"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="کالا")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        verbose_name="قیمت واحد",
    )
    apply_profit = models.BooleanField(default=True, verbose_name="اعمال درصد سود")
    apply_shipping = models.BooleanField(default=True, verbose_name="اعمال هزینه ارسال")
    apply_discount = models.BooleanField(default=True, verbose_name="اعمال درصد تخفیف")

    class Meta:
        verbose_name = "آیتم فاکتور"
        verbose_name_plural = "آیتم‌های فاکتور"

    def __str__(self):
        return f"{self.item.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.pk is None:  # ایجاد آیتم جدید
            if self.quantity > self.item.stock:
                raise ValueError(
                    f"تعداد درخواستی ({self.quantity}) بیشتر از موجودی کالا ({self.item.stock}) است."
                )
            super().save(*args, **kwargs)
            self.item.stock -= self.quantity
            self.item.save()
        else:
            super().save(*args, **kwargs)

    @property
    def get_total(self):
        price = (
            self.unit_price
            if self.unit_price
            else self.item.calculate_final_price(
                apply_profit=self.apply_profit,
                apply_shipping=self.apply_shipping,
                apply_discount=self.apply_discount,
            )
        )
        return self.quantity * price


class Activity(models.Model):
    TYPE_CHOICES = (
        ("login", "ورود به سیستم"),
        ("logout", "خروج از سیستم"),
        ("add_item", "افزودن کالا"),
        ("edit_item", "ویرایش کالا"),
        ("delete_item", "حذف کالا"),
        ("transaction_in", "ورود کالا"),
        ("transaction_out", "خروج کالا"),
        ("create_invoice", "ایجاد فاکتور"),
        ("edit_invoice", "ویرایش فاکتور"),
        ("delete_invoice", "حذف فاکتور"),
        ("add_user", "ایجاد کاربر"),
        ("edit_user", "ویرایش کاربر"),
        ("receive_invoice", "دریافت فاکتور"),
        ("return_purchase", "بازگشت به خرید"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="نوع فعالیت"
    )
    description = models.TextField(verbose_name="توضیحات")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ و زمان")

    class Meta:
        verbose_name = "فعالیت"
        verbose_name_plural = "فعالیت‌ها"

    def __str__(self):
        return f"{self.get_type_display()} - {self.user.username} - {self.date}"


# Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={"role": "customer"})


@receiver(pre_save, sender=Item)
def set_entry_date_if_missing(sender, instance, **kwargs):
    if not instance.entry_date:
        instance.entry_date = timezone.now().date()


@receiver(pre_save, sender=Invoice)
def set_invoice_date_if_missing(sender, instance, **kwargs):
    if not instance.date:
        instance.date = timezone.now().date()
