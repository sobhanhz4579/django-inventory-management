from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Transaction


@receiver(post_save, sender=Transaction)
def send_transaction_email(sender, instance, created, **kwargs):
    """
    ارسال ایمیل بعد از ثبت تراکنش
    فقط برای تراکنش‌های خروج (out)
    """

    if not created:
        return

    if instance.type != "out":
        return

    user = instance.user

    if user.email:
        recipient_list = [user.email]
    else:
        recipient_list = getattr(settings, "ADMIN_EMAILS", None)

        if not recipient_list:
            default_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
            if default_email:
                recipient_list = [default_email]
            else:
                return

    subject = "ثبت تراکنش خروج از سیستم"

    message = f"""
یک تراکنش خروج در سیستم ثبت شد:

نوع تراکنش:
خروج

کالا:
{instance.item.name or '-'}

تعداد:
{instance.quantity or '-'}

قیمت واحد:
{instance.price or '-'}

کاربر:
{user.username or '-'}

تاریخ:
{instance.date or '-'}

یادداشت:
{instance.notes or '-'}
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception:
        pass
