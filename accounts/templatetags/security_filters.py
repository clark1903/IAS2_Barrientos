from django import template


register = template.Library()


@register.filter
def mask_student_id(value):
    value = str(value or "")
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


@register.filter
def mask_email(value):
    value = str(value or "")
    if "@" not in value:
        return value
    local, domain = value.split("@", 1)
    if len(local) <= 1:
        local_masked = "*"
    else:
        local_masked = local[0] + "*" * (len(local) - 1)
    return f"{local_masked}@{domain}"
