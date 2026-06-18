import re

from django.core.exceptions import ValidationError


class UppercaseNumberSymbolValidator:
    def validate(self, password, user=None):
        missing = []
        if not re.search(r"[A-Z]", password):
            missing.append("an uppercase letter")
        if not re.search(r"\d", password):
            missing.append("a number")
        if not re.search(r"[^A-Za-z0-9]", password):
            missing.append("a symbol")

        if missing:
            raise ValidationError(
                "Password must contain at least " + ", ".join(missing) + ".",
                code="password_policy",
            )

    def get_help_text(self):
        return "Your password must include at least one uppercase letter, one number, and one symbol."
