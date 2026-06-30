from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Item, Invoice, InvoiceItem, Profile
from jdatetime import date as jdate
from datetime import datetime
from django.utils import timezone
import re


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="نام کاربری",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "نام کاربری"}
        ),
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "رمز عبور"}
        ),
    )


class ItemForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label="تعداد اولیه",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        min_value=0,
    )
    price = forms.DecimalField(
        label="قیمت خرید",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_digits=10,
        decimal_places=2,
        initial=0.00,
    )
    supplier = forms.CharField(
        label="تأمین‌کننده",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    entry_date = forms.CharField(
        label="تاریخ ورود",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "YYYY/MM/DD"}
        ),
        help_text="تاریخ را به فرمت شمسی وارد کنید (مثال: 1404/05/25)",
    )

    class Meta:
        model = Item
        fields = [
            "code",
            "name",
            "description",
            "shelf",
            "manufacturer",
            "category",
            "subcategory",
            "unit",
            "min_stock",
            "location",
            "last_price",
            "profit_margin",
            "shipping_cost",
            "discount_percentage",
            "sale_price",
            "entry_date",
            "supplier_code",
            "image",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "shelf": forms.TextInput(attrs={"class": "form-control"}),
            "manufacturer": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "subcategory": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "min_stock": forms.NumberInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "last_price": forms.NumberInput(attrs={"class": "form-control"}),
            "profit_margin": forms.NumberInput(attrs={"class": "form-control"}),
            "shipping_cost": forms.NumberInput(attrs={"class": "form-control"}),
            "discount_percentage": forms.NumberInput(attrs={"class": "form-control"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control"}),
            "supplier_code": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.URLInput(attrs={"class": "form-control"}),
        }
        labels = {
            "code": "کد کالا",
            "name": "نام کالا",
            "description": "توضیحات",
            "shelf": "قفسه",
            "manufacturer": "تولیدکننده",
            "category": "دسته‌بندی",
            "subcategory": "زیر‌دسته",
            "unit": "واحد",
            "min_stock": "حداقل موجودی",
            "location": "مکان انبار",
            "last_price": "آخرین قیمت خرید",
            "profit_margin": "درصد سود",
            "shipping_cost": "هزینه ارسال",
            "discount_percentage": "درصد تخفیف",
            "sale_price": "قیمت فروش",
            "entry_date": "تاریخ ورود",
            "supplier_code": "کد تأمین‌کننده",
            "image": "تصویر",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code"].required = False  # کد اختیاری برای تولید خودکار
        self.fields["name"].required = True
        self.fields["description"].required = False
        self.fields["shelf"].required = False
        self.fields["manufacturer"].required = False
        self.fields["category"].required = False
        self.fields["subcategory"].required = False
        self.fields["unit"].required = False
        self.fields["min_stock"].required = False
        self.fields["location"].required = False
        self.fields["last_price"].required = False
        self.fields["profit_margin"].required = False
        self.fields["shipping_cost"].required = False
        self.fields["discount_percentage"].required = False
        self.fields["sale_price"].required = False
        self.fields["entry_date"].required = False
        self.fields["supplier_code"].required = False
        self.fields["image"].required = False
        if self.instance and self.instance.entry_date:
            j_date = jdate.fromgregorian(date=self.instance.entry_date)
            self.initial["entry_date"] = (
                f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
            )
        if not self.instance.pk:  # تولید کد خودکار برای کالاهای جدید
            self.initial["code"] = str(Item.objects.count() + 1)  # کد به صورت عدد ساده

    def clean_entry_date(self):
        entry_date = self.cleaned_data.get("entry_date")
        if entry_date:
            try:
                year, month, day = map(int, entry_date.split("/"))
                j_date = jdate(year, month, day)
                return j_date.togregorian()
            except (ValueError, IndexError):
                raise forms.ValidationError(
                    "فرمت تاریخ نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید."
                )
        return None  # اجازه می‌دهیم None باشد، زیرا سیگنال مدل تاریخ را تنظیم می‌کند

    def clean_code(self):
        code = self.cleaned_data.get("code")
        if not code:
            code = str(Item.objects.count() + 1)  # تولید کد به صورت عدد ساده
        if (
            Item.objects.filter(code=code)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise forms.ValidationError("این کد کالا قبلاً استفاده شده است.")
        return code

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None:
            return 0.00
        return price

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity") or 0
        min_stock = cleaned_data.get("min_stock") or 0
        if min_stock > quantity:
            raise forms.ValidationError(
                {"min_stock": "حداقل موجودی نمی‌تواند بیشتر از تعداد اولیه باشد."}
            )
        return cleaned_data


class UserCreationForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        label="نقش",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="رمز عبور",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="تکرار رمز عبور",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "role" not in self.data:
            self.fields["role"].initial = "customer"
        if (
            self.data.get("role") == "customer"
            or self.initial.get("role") == "customer"
        ):
            self.fields["username"].required = False
            self.fields["first_name"].required = True
            self.fields["last_name"].required = True
            self.fields["username"].widget.attrs.pop("required", None)
        else:
            self.fields["username"].required = True
            self.fields["first_name"].required = False
            self.fields["last_name"].required = False

    def clean_username(self):
        username = self.cleaned_data.get("username")
        role = (
            self.cleaned_data.get("role")
            if "role" in self.cleaned_data
            else self.data.get("role", "customer")
        )
        if role == "customer" and not username:
            first_name = self.cleaned_data.get("first_name") or self.data.get(
                "first_name", ""
            )
            last_name = self.cleaned_data.get("last_name") or self.data.get(
                "last_name", ""
            )
            if first_name and last_name:
                username = f"{first_name.strip()} {last_name.strip()}".replace(" ", "_")
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
            else:
                raise forms.ValidationError(
                    "نام و نام خانوادگی باید وارد شوند تا نام کاربری تولید شود."
                )
        if (
            username
            and User.objects.filter(username=username)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise forms.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1") or "1234"
        password2 = self.cleaned_data.get("password2") or "1234"
        if password1 != password2:
            raise forms.ValidationError("رمزهای عبور مطابقت ندارند.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role") or self.data.get("role", "customer")
        if role == "customer":
            cleaned_data["password1"] = cleaned_data.get("password1") or "1234"
            cleaned_data["password2"] = cleaned_data.get("password2") or "1234"
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1") or "1234"
        user.set_password(password)
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user, defaults={"role": self.cleaned_data["role"]}
            )
        return user


class InvoiceForm(forms.ModelForm):
    date = forms.CharField(
        label="تاریخ",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "YYYY/MM/DD"}
        ),
        help_text="تاریخ را به فرمت شمسی وارد کنید (مثال: 1404/05/25)",
    )
    number = forms.CharField(
        label="شماره فاکتور",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )

    class Meta:
        model = Invoice
        fields = [
            "number",
            "date",
            "customer",
            "company_name",
            "company_address",
            "company_phone",
        ]
        widgets = {
            "number": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "customer": forms.Select(attrs={"class": "form-control"}),
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "company_address": forms.TextInput(attrs={"class": "form-control"}),
            "company_phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.date:
            j_date = jdate.fromgregorian(date=self.instance.date)
            self.initial["date"] = f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"

    def clean_date(self):
        date_str = self.cleaned_data.get("date")
        if date_str:
            try:
                year, month, day = map(int, date_str.split("/"))
                j_date = jdate(year, month, day)
                return j_date.togregorian()
            except (ValueError, IndexError):
                raise forms.ValidationError(
                    "فرمت تاریخ نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید."
                )
        return timezone.now().date()

    def clean_number(self):
        number = self.cleaned_data.get("number")
        if self.instance and self.instance.pk:
            return self.instance.number
        return number or str(Invoice.objects.count() + 1)


class InvoiceItemForm(forms.ModelForm):
    apply_profit = forms.BooleanField(
        label="اعمال درصد سود",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    apply_shipping = forms.BooleanField(
        label="اعمال هزینه ارسال",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    apply_discount = forms.BooleanField(
        label="اعمال درصد تخفیف",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "item",
            "quantity",
            "unit_price",
            "apply_profit",
            "apply_shipping",
            "apply_discount",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "item": "کالا",
            "quantity": "تعداد",
            "unit_price": "قیمت واحد",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].required = True
        self.fields["quantity"].required = True
        self.fields["unit_price"].required = False
        self.fields["apply_profit"].initial = True
        self.fields["apply_shipping"].initial = True
        self.fields["apply_discount"].initial = True

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get("item")
        quantity = cleaned_data.get("quantity")
        if item and quantity:
            if quantity > item.stock:
                raise forms.ValidationError(
                    f"تعداد درخواستی ({quantity}) بیشتر از موجودی کالا ({item.stock}) است."
                )
        return cleaned_data


InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class ReturnPurchaseForm(forms.Form):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.all(),
        label="فاکتور",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_invoice"}),
    )
    reason = forms.CharField(
        label="دلیل بازگشت",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4, "id": "id_reason"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invoice"].required = True
        self.fields["reason"].required = False
