from django.urls import path
from . import views

app_name = "warehouse"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("items/", views.items_list, name="items_list"),
    path("items/create/", views.item_create, name="item_create"),
    path("items/<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:item_id>/delete/", views.item_delete, name="item_delete"),
    path("invoices/", views.invoices_list, name="invoices_list"),
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:invoice_id>/edit/", views.invoice_edit, name="invoice_edit"),
    path(
        "invoices/<int:invoice_id>/delete/", views.invoice_delete, name="invoice_delete"
    ),
    path(
        "invoices/<int:invoice_id>/detail/", views.invoice_detail, name="invoice_detail"
    ),
    path("invoices/<int:invoice_id>/print/", views.invoice_print, name="invoice_print"),
    path("return/", views.return_purchase, name="return_purchase"),
    path(
        "return/get-invoice-items/", views.get_invoice_items, name="get_invoice_items"
    ),
    path("reports/", views.reports, name="reports"),
    path("users/", views.users_list, name="users_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("users/<int:user_id>/reports/", views.user_reports, name="user_reports"),
    path("items/get-details/", views.get_item_details, name="get_item_details"),
]
