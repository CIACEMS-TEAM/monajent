from __future__ import annotations

import string
from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """
    Exige une complexité minimale "3 sur 4":
    - au moins une minuscule
    - au moins une majuscule
    - au moins un chiffre
    - au moins un caractère spécial
    """

    def validate(self, password: str, user=None) -> None:
        if not password:
            raise ValidationError("Le mot de passe est requis.")

        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        specials = set(string.punctuation)
        has_special = any(c in specials for c in password)

        score = sum([has_lower, has_upper, has_digit, has_special])
        if score < 3:
            raise ValidationError(
                "Le mot de passe doit contenir au moins trois catégories parmi: minuscule, majuscule, chiffre, caractère spécial."
            )

    def get_help_text(self) -> str:
        return ("Le mot de passe doit contenir au moins trois catégories parmi: "
                "minuscule, majuscule, chiffre, caractère spécial.")


