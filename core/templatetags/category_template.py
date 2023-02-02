from django import template
from core.models import Categories, Order

register = template.Library()


@register.filter
def get_categories(user):
    categories = Categories.objects.all()
    return categories

