from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, F, Case, When, IntegerField, Value
from django.db.models.functions import Cast
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from .forms import *
from .models import *
from jdatetime import date as jdate


def check_admin(user):
    """Check if the user is an admin or superuser."""
    return user.is_superuser or (
        hasattr(user, "profile") and user.profile.role == "admin"
    )


def login_view(request):
    """Handle user login with admin role check."""
    if request.user.is_authenticated and check_admin(request.user):
        return redirect("warehouse:dashboard")
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if check_admin(user):
                login(request, user)
                Activity.objects.create(
                    user=user, type="login", description="کاربر وارد سیستم شد"
                )
                return redirect("warehouse:dashboard")
            messages.error(request, "فقط ادمین‌ها می‌توانند وارد سیستم شوند.")
        else:
            messages.error(request, "نام کاربری یا رمز عبور اشتباه است.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    """Handle user logout."""
    if request.user.is_authenticated:
        Activity.objects.create(
            user=request.user, type="logout", description="کاربر از سیستم خارج شد"
        )
    logout(request)
    return redirect("warehouse:login")


@login_required
def dashboard(request):
    """Display dashboard with basic statistics."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند به داشبورد دسترسی داشته باشند.")
        return redirect("warehouse:login")
    items_count = Item.objects.count()
    invoices_count = Invoice.objects.count()
    low_stock_count = Item.objects.filter(stock__lte=F("min_stock")).count()
    return render(
        request,
        "dashboard.html",
        {
            "items_count": items_count,
            "invoices_count": invoices_count,
            "low_stock_count": low_stock_count,
        },
    )


@login_required
def items_list(request):
    """List all items with advanced search, filtering, and pagination."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند کالاها را مشاهده کنند.")
        return redirect("warehouse:dashboard")

    items = Item.objects.all().order_by("-code")

    query = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    min_stock = request.GET.get("min_stock")
    category = request.GET.get("category", "").strip()
    entry_date_from = request.GET.get("entry_date_from")
    entry_date_to = request.GET.get("entry_date_to")

    if query:
        q_objects = (
            Q(code__icontains=query)
            | Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(shelf__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(category__icontains=query)
            | Q(subcategory__icontains=query)
            | Q(unit__icontains=query)
            | Q(location__icontains=query)
            | Q(supplier_code__icontains=query)
        )
        items = items.filter(q_objects).distinct()

        if "/" in query and len(query.split("/")) == 3:
            try:
                y, m, d = map(int, query.split("/"))
                g_date = jdate(y, m, d).togregorian()
                items = items.filter(entry_date=g_date)
            except:
                pass

    try:
        if min_price:
            min_price = float(min_price)
            items = items.filter(sale_price__gte=min_price)
        if max_price:
            max_price = float(max_price)
            items = items.filter(sale_price__lte=max_price)
    except (ValueError, TypeError):
        pass

    try:
        if min_stock:
            min_stock = int(min_stock)
            items = items.filter(stock__gte=min_stock)
    except (ValueError, TypeError):
        pass

    if category:
        items = items.filter(category__icontains=category)

    if entry_date_from:
        try:
            y, m, d = map(int, entry_date_from.split("/"))
            g_date = jdate(y, m, d).togregorian()
            items = items.filter(entry_date__gte=g_date)
        except:
            pass
    if entry_date_to:
        try:
            y, m, d = map(int, entry_date_to.split("/"))
            g_date = jdate(y, m, d).togregorian()
            items = items.filter(entry_date__lte=g_date)
        except:
            pass

    paginator = Paginator(items, 20)
    page_number = request.GET.get("page")
    items_page = paginator.get_page(page_number)

    return render(
        request,
        "items/list.html",
        {
            "items": items_page,
            "filters": request.GET,
            "total_count": paginator.count,
        },
    )


@login_required
def item_create(request):
    """Create a new item with optional initial transaction."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند کالا اضافه کنند.")
        return redirect("warehouse:dashboard")
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    item = form.save(commit=False)
                    quantity = form.cleaned_data.get("quantity", 0)
                    if any(
                        form.cleaned_data.get(key)
                        for key in [
                            "profit_margin",
                            "shipping_cost",
                            "discount_percentage",
                        ]
                    ):
                        item.sale_price = item.calculate_final_price()
                    item.save()
                    if quantity > 0:
                        Transaction.objects.create(
                            item=item,
                            type="in",
                            quantity=quantity,
                            date=form.cleaned_data.get("entry_date")
                            or timezone.now().date(),
                            user=request.user,
                            price=form.cleaned_data.get(
                                "price", item.sale_price or item.last_price or 0.00
                            ),
                            supplier=form.cleaned_data.get("supplier", ""),
                            notes=f"ورود اولیه کالا {item.name} هنگام افزودن",
                        )
                        Activity.objects.create(
                            user=request.user,
                            type="transaction_in",
                            description=f"ورود {quantity} واحد از {item.name}",
                        )
                    Activity.objects.create(
                        user=request.user,
                        type="add_item",
                        description=f"کالا {item.name} اضافه شد",
                    )
                messages.success(request, "کالا و تراکنش ورود با موفقیت ثبت شد.")
                return redirect("warehouse:items_list")
            except ValueError as e:
                messages.error(request, f"خطا در ثبت کالا: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f"خطا در فیلد {form.fields[field].label}: {error}"
                    )
    else:
        form = ItemForm()
    return render(request, "items/create.html", {"form": form})


@login_required
def item_edit(request, item_id):
    """Edit an existing item and update stock if necessary."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند کالا را ویرایش کنند.")
        return redirect("warehouse:dashboard")
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            try:
                with transaction.atomic():
                    old_stock = item.stock
                    item = form.save(commit=False)
                    if any(
                        form.cleaned_data.get(key)
                        for key in [
                            "profit_margin",
                            "shipping_cost",
                            "discount_percentage",
                        ]
                    ):
                        item.sale_price = item.calculate_final_price()
                    item.save()
                    new_quantity = form.cleaned_data.get("quantity", 0)
                    if new_quantity != old_stock:
                        quantity_diff = new_quantity - old_stock
                        if quantity_diff != 0:
                            transaction_type = "in" if quantity_diff > 0 else "out"
                            transaction_price = form.cleaned_data.get(
                                "price", item.sale_price or item.last_price or 0.00
                            )
                            if transaction_price is None:
                                transaction_price = (
                                    item.sale_price or item.last_price or 0.00
                                )
                            Transaction.objects.create(
                                item=item,
                                type=transaction_type,
                                quantity=abs(quantity_diff),
                                date=form.cleaned_data.get("entry_date")
                                or timezone.now().date(),
                                user=request.user,
                                price=transaction_price,
                                supplier=form.cleaned_data.get(
                                    "supplier", item.supplier_code or ""
                                ),
                                notes=f"تغییر موجودی کالا {item.name} در ویرایش (تفاوت: {quantity_diff})",
                            )
                            Activity.objects.create(
                                user=request.user,
                                type=f"transaction_{transaction_type}",
                                description=f"{transaction_type.capitalize()} {abs(quantity_diff)} واحد از {item.name} در ویرایش",
                            )
                    Activity.objects.create(
                        user=request.user,
                        type="edit_item",
                        description=f"کالا {item.name} ویرایش شد",
                    )
                    messages.success(request, "کالا با موفقیت ویرایش شد.")
                    return redirect("warehouse:items_list")
            except ValueError as e:
                messages.error(request, f"خطا در ویرایش کالا: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f"خطا در فیلد {form.fields[field].label}: {error}"
                    )
    else:
        initial_data = {"quantity": item.stock, "price": item.last_price}
        if item.entry_date:
            j_date = jdate.fromgregorian(date=item.entry_date)
            initial_data["entry_date"] = (
                f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
            )
        form = ItemForm(instance=item, initial=initial_data)
    return render(request, "items/edit.html", {"form": form, "item": item})


@login_required
def item_delete(request, item_id):
    """Delete an item."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند کالا را حذف کنند.")
        return redirect("warehouse:dashboard")
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST":
        try:
            item_name = item.name
            item.delete()
            Activity.objects.create(
                user=request.user,
                type="delete_item",
                description=f"کالا {item_name} حذف شد",
            )
            messages.success(request, "کالا با موفقیت حذف شد.")
            return redirect("warehouse:items_list")
        except Exception as e:
            messages.error(request, f"خطا در حذف کالا: {str(e)}")
    return render(request, "items/delete_confirm.html", {"item": item})


@login_required
def invoices_list(request):
    """List all invoices with advanced filtering and proper sorting."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند فاکتورها را مشاهده کنند.")
        return redirect("warehouse:dashboard")

    invoices = (
        Invoice.objects.select_related("user", "customer")
        .annotate(
            is_numeric=Case(
                When(number__regex=r"^[0-9]+$", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            numeric_value=Case(
                When(number__regex=r"^[0-9]+$", then=Cast("number", IntegerField())),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by("-is_numeric", "-numeric_value", "-date")
    )

    # فیلترهای جستجو
    query = request.GET.get("q", "").strip()
    min_amount = request.GET.get("min_amount")
    max_amount = request.GET.get("max_amount")
    customer_query = request.GET.get("customer", "").strip()
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    has_return = request.GET.get("has_return")

    if query:
        q_objects = (
            Q(number__icontains=query)
            | Q(company_name__icontains=query)
            | Q(company_address__icontains=query)
            | Q(company_phone__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(customer__username__icontains=query)
            | Q(customer__first_name__icontains=query)
            | Q(customer__last_name__icontains=query)
            | Q(items__item__name__icontains=query)
        )
        role_mapping = dict(Profile.ROLE_CHOICES)
        reverse_role_mapping = {v: k for k, v in role_mapping.items()}
        if query in reverse_role_mapping:
            q_objects |= Q(user__profile__role=reverse_role_mapping[query]) | Q(
                customer__profile__role=reverse_role_mapping[query]
            )
        elif query.lower() in role_mapping:
            q_objects |= Q(user__profile__role=query.lower()) | Q(
                customer__profile__role=query.lower()
            )
        invoices = invoices.filter(q_objects).distinct()

        if "/" in query and len(query.split("/")) == 3:
            try:
                y, m, d = map(int, query.split("/"))
                g_date = jdate(y, m, d).togregorian()
                invoices = invoices.filter(date=g_date)
            except:
                pass

    # فیلتر مبلغ
    try:
        if min_amount:
            min_amount = float(min_amount)
            invoices = invoices.filter(total_amount__gte=min_amount)
        if max_amount:
            max_amount = float(max_amount)
            invoices = invoices.filter(total_amount__lte=max_amount)
    except (ValueError, TypeError):
        pass

    if customer_query:
        invoices = invoices.filter(
            Q(customer__username__icontains=customer_query)
            | Q(customer__first_name__icontains=customer_query)
            | Q(customer__last_name__icontains=customer_query)
            | Q(company_name__icontains=customer_query)
        ).distinct()

    if date_from:
        try:
            y, m, d = map(int, date_from.split("/"))
            g_date = jdate(y, m, d).togregorian()
            invoices = invoices.filter(date__gte=g_date)
        except:
            pass
    if date_to:
        try:
            y, m, d = map(int, date_to.split("/"))
            g_date = jdate(y, m, d).togregorian()
            invoices = invoices.filter(date__lte=g_date)
        except:
            pass

    all_invoices = list(invoices)
    invoice_data = []

    for invoice in all_invoices:
        has_return_flag = Transaction.objects.filter(
            type="in", notes__icontains=f"بازگشت کالا برای فاکتور {invoice.number}"
        ).exists()
        invoice_data.append({"invoice": invoice, "has_return": has_return_flag})

    if has_return == "yes":
        invoice_data = [d for d in invoice_data if d["has_return"]]
    elif has_return == "no":
        invoice_data = [d for d in invoice_data if not d["has_return"]]

    return render(
        request,
        "invoices/list.html",
        {"invoice_data": invoice_data, "filters": request.GET},
    )


@login_required
def invoice_create(request):
    """Create a new invoice with associated items."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند فاکتور ایجاد کنند.")
        return redirect("warehouse:dashboard")
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix="items")
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save(commit=False)
                    invoice.user = request.user
                    invoice.save()
                    formset.instance = invoice
                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get(
                            "DELETE", False
                        ):
                            invoice_item = form.save(commit=False)
                            invoice_item.invoice = invoice
                            if not invoice_item.unit_price:
                                invoice_item.unit_price = (
                                    invoice_item.item.calculate_final_price(
                                        apply_profit=invoice_item.apply_profit,
                                        apply_shipping=invoice_item.apply_shipping,
                                        apply_discount=invoice_item.apply_discount,
                                    )
                                )
                            if invoice_item.quantity > invoice_item.item.stock:
                                raise ValueError(
                                    f"تعداد درخواستی ({invoice_item.quantity}) بیشتر از موجودی کالا ({invoice_item.item.stock}) است."
                                )
                            invoice_item.save()
                            Transaction.objects.create(
                                item=invoice_item.item,
                                type="out",
                                quantity=invoice_item.quantity,
                                date=invoice.date,
                                user=invoice.user,
                                price=invoice_item.unit_price,
                                destination=(
                                    invoice.customer.username
                                    if invoice.customer
                                    else invoice.company_name or "-"
                                ),
                                notes=f"خروج برای فاکتور {invoice.number}",
                            )
                            Activity.objects.create(
                                user=request.user,
                                type="transaction_out",
                                description=f"خروج {invoice_item.quantity} واحد از {invoice_item.item.name} برای فاکتور {invoice.number}",
                            )
                    invoice.calculate_total()
                    Activity.objects.create(
                        user=request.user,
                        type="create_invoice",
                        description=f"فاکتور {invoice.number} ایجاد شد",
                    )
                    if invoice.customer:
                        Activity.objects.create(
                            user=invoice.customer,
                            type="receive_invoice",
                            description=f"فاکتور {invoice.number} برای {invoice.customer.username} صادر شد",
                        )
                messages.success(request, "فاکتور با موفقیت ایجاد شد.")
                return redirect("warehouse:invoices_list")
            except ValueError as e:
                messages.error(request, f"خطا در ایجاد فاکتور: {str(e)}")
            except Exception as e:
                messages.error(request, f"خطای غیرمنتظره: {str(e)}")
        else:
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"خطا در آیتم فاکتور: {error}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f"خطا در فیلد {form.fields[field].label}: {error}"
                    )
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet(prefix="items")
    return render(request, "invoices/create.html", {"form": form, "formset": formset})


@login_required
def invoice_edit(request, invoice_id):
    """Edit an existing invoice and update associated items."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند فاکتور را ویرایش کنند.")
        return redirect("warehouse:dashboard")
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix="items")
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    old_items = {item.id: item.quantity for item in invoice.items.all()}
                    Transaction.objects.filter(
                        notes__contains=f"خروج برای فاکتور {invoice.number}"
                    ).delete()
                    for item in invoice.items.all():
                        item.item.stock += item.quantity
                        item.item.save()
                    # Save new invoice data
                    invoice = form.save()
                    # Save new items
                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get(
                            "DELETE", False
                        ):
                            invoice_item = form.save(commit=False)
                            invoice_item.invoice = invoice
                            if not invoice_item.unit_price:
                                invoice_item.unit_price = (
                                    invoice_item.item.calculate_final_price(
                                        apply_profit=invoice_item.apply_profit,
                                        apply_shipping=invoice_item.apply_shipping,
                                        apply_discount=invoice_item.apply_discount,
                                    )
                                )
                            if invoice_item.quantity > invoice_item.item.stock:
                                raise ValueError(
                                    f"تعداد درخواستی ({invoice_item.quantity}) بیشتر از موجودی کالا ({invoice_item.item.stock}) است."
                                )
                            invoice_item.save()
                            Transaction.objects.create(
                                item=invoice_item.item,
                                type="out",
                                quantity=invoice_item.quantity,
                                date=invoice.date,
                                user=invoice.user,
                                price=invoice_item.unit_price,
                                destination=(
                                    invoice.customer.username
                                    if invoice.customer
                                    else invoice.company_name or "-"
                                ),
                                notes=f"خروج برای فاکتور {invoice.number}",
                            )
                            Activity.objects.create(
                                user=request.user,
                                type="transaction_out",
                                description=f"خروج {invoice_item.quantity} واحد از {invoice_item.item.name} برای فاکتور {invoice.number}",
                            )
                    # Handle deleted items
                    formset.save()
                    invoice.calculate_total()
                    Activity.objects.create(
                        user=request.user,
                        type="edit_invoice",
                        description=f"فاکتور {invoice.number} ویرایش شد",
                    )
                    if invoice.customer:
                        Activity.objects.create(
                            user=invoice.customer,
                            type="receive_invoice",
                            description=f"فاکتور {invoice.number} برای {invoice.customer.username} ویرایش شد",
                        )
                messages.success(request, "فاکتور با موفقیت ویرایش شد.")
                return redirect("warehouse:invoices_list")
            except ValueError as e:
                messages.error(request, f"خطا در ویرایش فاکتور: {str(e)}")
            except Exception as e:
                messages.error(request, f"خطای غیرمنتظره: {str(e)}")
        else:
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"خطا در آیتم فاکتور: {error}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f"خطا در فیلد {form.fields[field].label}: {error}"
                    )
    else:
        initial_data = {}
        if invoice.date:
            j_date = jdate.fromgregorian(date=invoice.date)
            initial_data["date"] = f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
        form = InvoiceForm(instance=invoice, initial=initial_data)
        formset = InvoiceItemFormSet(instance=invoice, prefix="items")
    return render(
        request,
        "invoices/edit.html",
        {"form": form, "formset": formset, "invoice": invoice},
    )


@login_required
def invoice_delete(request, invoice_id):
    """Delete an invoice and restore stock."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند فاکتور را حذف کنند.")
        return redirect("warehouse:dashboard")
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        try:
            with transaction.atomic():
                invoice_number = invoice.number
                customer = invoice.customer
                Transaction.objects.filter(
                    notes__contains=f"خروج برای فاکتور {invoice_number}"
                ).delete()
                for item in invoice.items.all():
                    item.item.stock += item.quantity
                    item.item.save()
                invoice.delete()
                Activity.objects.create(
                    user=request.user,
                    type="delete_invoice",
                    description=f"فاکتور {invoice_number} حذف شد",
                )
                if customer:
                    Activity.objects.create(
                        user=customer,
                        type="delete_invoice",
                        description=f"فاکتور {invoice_number} برای {customer.username} حذف شد",
                    )
            messages.success(request, "فاکتور با موفقیت حذف شد.")
            return redirect("warehouse:invoices_list")
        except Exception as e:
            messages.error(request, f"خطا در حذف فاکتور: {str(e)}")
    return render(request, "invoices/delete_confirm.html", {"invoice": invoice})


@login_required
def invoice_detail(request, invoice_id):
    """Display invoice details."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند جزئیات فاکتور را مشاهده کنند.")
        return redirect("warehouse:dashboard")
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, "invoices/detail.html", {"invoice": invoice})


@login_required
def invoice_print(request, invoice_id):
    """Display invoice for printing."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند فاکتور را چاپ کنند.")
        return redirect("warehouse:dashboard")
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, "invoices/print.html", {"invoice": invoice})


@login_required
def return_purchase(request):
    """ثبت بازگشت کامل تمام کالاهای یک فاکتور."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند بازگشت کالا را ثبت کنند.")
        return redirect("warehouse:dashboard")

    if request.method == "POST":
        form = ReturnPurchaseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.cleaned_data["invoice"]
                    reason = form.cleaned_data["reason"] or "بدون دلیل"

                    invoice_items = InvoiceItem.objects.filter(invoice=invoice)
                    if not invoice_items.exists():
                        raise ValueError("این فاکتور شامل هیچ کالایی نیست.")

                    for invoice_item in invoice_items:
                        Transaction.objects.create(
                            item=invoice_item.item,
                            type="in",
                            quantity=invoice_item.quantity,
                            date=timezone.now().date(),
                            user=request.user,
                            price=invoice_item.unit_price,
                            supplier=(
                                invoice.customer.username
                                if invoice.customer
                                else invoice.company_name or "-"
                            ),
                            notes=f"بازگشت کالا برای فاکتور {invoice.number}: {reason}",
                        )

                    Activity.objects.create(
                        user=request.user,
                        type="return_purchase",
                        description=f"بازگشت کامل فاکتور {invoice.number} شامل {invoice_items.count()} کالا (دلیل: {reason})",
                    )
                    if invoice.customer:
                        Activity.objects.create(
                            user=invoice.customer,
                            type="return_purchase",
                            description=f"بازگشت کامل فاکتور {invoice.number}",
                        )

                messages.success(
                    request, f"بازگشت کامل فاکتور {invoice.number} با موفقیت ثبت شد."
                )
                return redirect("warehouse:invoices_list")

            except Exception as e:
                messages.error(request, f"خطا در ثبت بازگشت: {str(e)}")
    else:
        form = ReturnPurchaseForm()

    return render(request, "returns/return_purchase.html", {"form": form})


@login_required
def reports(request):
    """Display paginated recent transactions and activities."""
    if not check_admin(request.user):
        messages.error(request, "فقط ادمین‌ها می‌توانند گزارشات را مشاهده کنند.")
        return redirect("warehouse:dashboard")

    items_per_page = 20

    incoming_list = (
        Transaction.objects.filter(type="in")
        .select_related("item", "user")
        .order_by("-date")
    )
    incoming_paginator = Paginator(incoming_list, items_per_page)
    incoming_page_number = request.GET.get("incoming_page")
    recent_incoming = incoming_paginator.get_page(incoming_page_number)

    outgoing_list = (
        Transaction.objects.filter(type="out")
        .select_related("item", "user")
        .order_by("-date")
    )
    outgoing_paginator = Paginator(outgoing_list, items_per_page)
    outgoing_page_number = request.GET.get("outgoing_page")
    recent_outgoing = outgoing_paginator.get_page(outgoing_page_number)

    activities_list = Activity.objects.select_related("user").order_by("-date")
    activities_paginator = Paginator(activities_list, items_per_page)
    activities_page_number = request.GET.get("activities_page")
    activities = activities_paginator.get_page(activities_page_number)

    return render(
        request,
        "reports/report.html",
        {
            "recent_incoming": recent_incoming,
            "recent_outgoing": recent_outgoing,
            "activities": activities,
        },
    )


@login_required
def users_list(request):
    """List all users with advanced filtering."""
    if not request.user.is_superuser:
        messages.error(request, "فقط مدیر می‌تواند کاربران را مدیریت کند.")
        return redirect("warehouse:dashboard")

    users = User.objects.select_related("profile").all()

    query = request.GET.get("q", "").strip()
    first_name = request.GET.get("first_name", "").strip()
    last_name = request.GET.get("last_name", "").strip()
    username = request.GET.get("username", "").strip()
    role = request.GET.get("role", "")
    is_active = request.GET.get("is_active", "")

    if query:
        q_objects = (
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
        role_mapping = dict(Profile.ROLE_CHOICES)
        reverse_role_mapping = {v: k for k, v in role_mapping.items()}
        if query in reverse_role_mapping:
            q_objects |= Q(profile__role=reverse_role_mapping[query])
        elif query.lower() in role_mapping:
            q_objects |= Q(profile__role=query.lower())
        users = users.filter(q_objects).distinct()

    if first_name:
        users = users.filter(first_name__icontains=first_name)
    if last_name:
        users = users.filter(last_name__icontains=last_name)
    if username:
        users = users.filter(username__icontains=username)
    if role:
        users = users.filter(profile__role=role)
    if is_active == "1":
        users = users.filter(is_active=True)
    elif is_active == "0":
        users = users.filter(is_active=False)

    return render(request, "users/list.html", {"users": users, "filters": request.GET})


@login_required
def user_create(request):
    """Create a new user."""
    if not request.user.is_superuser:
        messages.error(request, "فقط مدیر می‌تواند کاربر اضافه کند.")
        return redirect("warehouse:dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                Activity.objects.create(
                    user=request.user,
                    type="add_user",
                    description=f"کاربر {user.username} اضافه شد",
                )
                messages.success(request, "کاربر با موفقیت اضافه شد.")
                return redirect("warehouse:users_list")
            except ValueError as e:
                messages.error(request, f"خطا در افزودن کاربر: {str(e)}")
    else:
        form = UserCreationForm()
    return render(request, "users/create.html", {"form": form})


@login_required
def user_edit(request, user_id):
    """Edit an existing user."""
    if not request.user.is_superuser:
        messages.error(request, "فقط مدیر می‌تواند کاربر را ویرایش کند.")
        return redirect("warehouse:dashboard")
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserCreationForm(request.POST, instance=user)
        if form.is_valid():
            try:
                user = form.save()
                profile, created = Profile.objects.get_or_create(user=user)
                profile.role = form.cleaned_data["role"]
                profile.save()
                Activity.objects.create(
                    user=request.user,
                    type="edit_user",
                    description=f"کاربر {user.username} ویرایش شد",
                )
                messages.success(request, "کاربر با موفقیت ویرایش شد.")
                return redirect("warehouse:users_list")
            except ValueError as e:
                messages.error(request, f"خطا در ویرایش کاربر: {str(e)}")
    else:
        form = UserCreationForm(
            instance=user,
            initial={
                "role": user.profile.role if hasattr(user, "profile") else "customer"
            },
        )
    return render(request, "users/edit.html", {"form": form, "user": user})


@login_required
def user_delete(request, user_id):
    """Delete a user."""
    if not request.user.is_superuser:
        messages.error(request, "فقط مدیر می‌تواند کاربر را حذف کند.")
        return redirect("warehouse:dashboard")
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "نمی‌توانید حساب کاربری خود را حذف کنید.")
        return redirect("warehouse:users_list")
    if request.method == "POST":
        try:
            username = user.username
            user.delete()
            Activity.objects.create(
                user=request.user,
                type="delete_user",
                description=f"کاربر {username} حذف شد",
            )
            messages.success(request, "کاربر با موفقیت حذف شد.")
            return redirect("warehouse:users_list")
        except Exception as e:
            messages.error(request, f"خطا در حذف کاربر: {str(e)}")
    return render(request, "users/delete_confirm.html", {"user": user})


@login_required
def user_reports(request, user_id):
    """Display user activity and transaction reports with pagination."""
    if not request.user.is_superuser:
        messages.error(request, "فقط مدیر می‌تواند گزارشات کاربر را مشاهده کند.")
        return redirect("warehouse:dashboard")

    user = get_object_or_404(User, id=user_id)
    items_per_page = 20

    activities_list = Activity.objects.filter(user=user).order_by("-date")
    activities_paginator = Paginator(activities_list, items_per_page)
    activities_page = request.GET.get("activities_page")
    activities = activities_paginator.get_page(activities_page)

    transactions_list = (
        Transaction.objects.filter(user=user).select_related("item").order_by("-date")
    )
    transactions_paginator = Paginator(transactions_list, items_per_page)
    transactions_page = request.GET.get("transactions_page")
    transactions = transactions_paginator.get_page(transactions_page)

    received_invoices_list = (
        Invoice.objects.filter(customer=user).select_related("user").order_by("-date")
    )
    invoices_paginator = Paginator(received_invoices_list, items_per_page)
    invoices_page = request.GET.get("invoices_page")
    received_invoices = invoices_paginator.get_page(invoices_page)

    return render(
        request,
        "users/reports.html",
        {
            "user": user,
            "activities": activities,
            "transactions": transactions,
            "received_invoices": received_invoices,
        },
    )


@login_required
def get_item_details(request):
    """Return item details for AJAX requests."""
    item_id = request.GET.get("item_id")
    try:
        item = Item.objects.get(id=item_id)
        data = {
            "sale_price": float(item.sale_price or 0),
            "last_price": float(item.last_price or 0),
            "profit_margin": float(item.profit_margin or 0),
            "shipping_cost": float(item.shipping_cost or 0),
            "discount_percentage": float(item.discount_percentage or 0),
            "stock": item.stock,
        }
        return JsonResponse(data)
    except Item.DoesNotExist:
        return JsonResponse({"error": "کالا یافت نشد"}, status=404)


@login_required
def get_invoice_items(request):
    """برگرداندن لیست کالاهای یک فاکتور به صورت JSON برای استفاده در AJAX."""
    if not check_admin(request.user):
        return JsonResponse({"error": "دسترسی مجاز نیست."}, status=403)

    invoice_id = request.GET.get("invoice_id")
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        items = InvoiceItem.objects.filter(invoice=invoice)
        data = [
            {
                "id": item.item.id,
                "name": item.item.name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price or 0),
            }
            for item in items
        ]
        return JsonResponse({"items": data})
    except Invoice.DoesNotExist:
        return JsonResponse({"error": "فاکتور یافت نشد."}, status=404)
