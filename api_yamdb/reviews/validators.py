from datetime import date as dt

from django.core.exceptions import ValidationError


def validate_year(value):
    year = dt.today().year
    if not value <= year:
        raise ValidationError(
            'Год произведения не может быть больше текущего!'
        )
    return value
