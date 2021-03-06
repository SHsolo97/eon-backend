from utils.helper import send_email_sms_and_notification


def post_save_method(sender, **kwargs):
    instance = kwargs.get('instance')
    if instance.method_name == 'old_instance':
        if instance.previous_state and not instance.is_active:
            send_email_sms_and_notification(action_name="user_blocked",
                                            email_ids=[instance.email])
        elif not instance.previous_state and instance.is_active:
            send_email_sms_and_notification(action_name="user_unblocked",
                                            email_ids=[instance.email])


def remember_state_method(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.previous_state = instance.is_active


def pre_save_method(sender, **kwargs):
    instance = kwargs.get('instance')
    updated_fields = kwargs.get('updated_fields')
    if updated_fields is None:
        instance.method_name = 'new_instance'
    else:
        instance.method_name = 'old_instance'
