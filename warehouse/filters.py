import django_filters
from .models import Item, Invoice, User


class ItemFilter(django_filters.FilterSet):
    class Meta:
        model = Item
        fields = {
            "code": ["icontains"],
            "name": ["icontains"],
            "category": ["exact"],
            "subcategory": ["exact"],
        }
