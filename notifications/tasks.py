# notifications/tasks.py

from celery import shared_task


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def send_notification_email(notification_id):
    ...


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def send_notification_email(notification_id):
    ...

@shared_task
def send_sms_notification(notification_id):
    ...