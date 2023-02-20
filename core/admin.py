from django.contrib import admin

from .models import Plan, Order, PaymentHistory, UserProfile, Categories


# def make_refund_accepted(modeladmin, request, queryset):
#     queryset.update(refund_requested=False, refund_granted=True)


# make_refund_accepted.short_description = 'Update orders to refund granted'

admin.site.register(Plan)
admin.site.register(Order)
admin.site.register(PaymentHistory)

admin.site.register(UserProfile)
admin.site.register(Categories)
