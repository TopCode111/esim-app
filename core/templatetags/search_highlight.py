from django import template
from django.core.exceptions import ObjectDoesNotExist
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text,keyword):
    highlighted = text.replace(keyword,"<b class='keyword'>%s</b>" %keyword)
    highlighted = mark_safe(highlighted)
    return highlighted
