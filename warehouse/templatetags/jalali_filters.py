from django import template
from jdatetime import date as jdate, datetime as jdatetime
from persian_tools import digits

register = template.Library()

@register.filter
def to_jalali_date(value):
    if not value:
        return '-'
    if isinstance(value, str):
        try:
            year, month, day = map(int, value.split('/'))
            j_date = jdate(year, month, day).togregorian()
        except (ValueError, TypeError):
            return '-'
    else:
        j_date = jdate.fromgregorian(date=value)
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    return f"{j_date.day} {months[j_date.month-1]} {j_date.year}"

@register.filter
def to_jalali_datetime(value):
    if not value:
        return '-'
    j_date = jdatetime.fromgregorian(datetime=value)
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    return f"{j_date.day} {months[j_date.month-1]} {j_date.year} {j_date.hour:02d}:{j_date.minute:02d}"

@register.filter
def to_jalali_date_input(value):
    if not value:
        return ''
    if isinstance(value, str):
        return value
    j_date = jdate.fromgregorian(date=value)
    return f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"


