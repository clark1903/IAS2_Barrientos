import hashlib
import hmac
import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from .models import AuditLog
from .request_context import get_current_ip, get_current_user


def _normalize(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def serialize_instance(instance):
    data = {}
    for field in instance._meta.fields:
        data[field.name] = getattr(instance, field.attname)
    return _normalize(data)


def log_audit_event(*, action, instance=None, model_name="", object_pk="", before=None, after=None, user=None, ip_address=""):
    actor = user if user is not None else get_current_user()
    target_model = model_name or (instance._meta.label if instance is not None else "")
    target_pk = object_pk or (str(instance.pk) if instance is not None and instance.pk is not None else "")
    before_state = _normalize(before or {})
    after_state = _normalize(after or {})
    ip_value = ip_address or get_current_ip()
    created_at = timezone.now()

    payload = {
        "action": action,
        "model_name": target_model,
        "object_pk": target_pk,
        "before_state": before_state,
        "after_state": after_state,
        "actor_id": getattr(actor, "pk", None),
        "ip_address": ip_value,
        "created_at": created_at.isoformat(),
    }
    record_hash = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        model_name=target_model,
        object_pk=target_pk,
        ip_address=ip_value or None,
        before_state=before_state,
        after_state=after_state,
        record_hash=record_hash,
        created_at=created_at,
    )
