from django import template
from core.models import Plan, Order,PlanDataChoice,PlanProviderChoice

register = template.Library()

@register.filter(is_safe=True)
def get_plandata_list(id):
    return PlanDataChoice

@register.filter
def get_plandata(id):
    return PlanDataChoice[id-1][1]

@register.filter(is_safe=True)
def get_planprovider_list(id):
    return PlanProviderChoice

@register.filter
def get_planprovider(id):
    return PlanProviderChoice[id-1][1]

