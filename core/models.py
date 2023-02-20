from django.db.models.signals import post_save
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404, reverse, redirect
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django.utils.text import slugify
import itertools


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Categories(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

PlanDataChoice = (1, "300MB"), (2, "1GB"), (3, "無制限")
PlanProviderChoice = (1, "3G"), (2, "LTE"), (3, "4G"), (4, "5G")
class Plan(models.Model):    
    planID = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100,blank=True, null=True)
    country = CountryField(blank=True, null=True)
    coverage_area = CountryField(blank=True, null=True)
    plan_data = models.PositiveIntegerField(choices=PlanDataChoice,blank=True, null=True)
    plan_price = models.PositiveIntegerField(blank=True, null=True)
    plan_provider = models.CharField(max_length=50,blank=True, null=True)
    plan_network = models.CharField(max_length=50,blank=True, null=True)
    plan_tethering = models.BooleanField(default=False)
    plan_cell = models.BooleanField(default=False)    
    summary = models.TextField(blank=True, null=True)
    stripe_price_id = models.CharField(_(u'Stripe Products'),max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("core:plan", kwargs={
            'pk': self.id
        })

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=50, blank=True, null=True)
    plan = models.ForeignKey(Plan,on_delete=models.CASCADE)
    activateDate = models.DateField()
    endDate = models.DateField()
    ordered_date = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    period = models.PositiveIntegerField(blank=True, null=True)
    '''
    
    '''

    def __str__(self):
        return self.plan.name
    
    def get_absolute_url(self):
        return reverse("core:order", kwargs={
            'pk': self.id
        })

class PaymentHistory(models.Model):
    checkout_session = models.CharField(_(u'Stripe Subscriptions'),max_length=255, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)    
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.stipe_charge_id
    
class Blog(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    title = models.CharField(max_length=50)
    content = models.TextField()
    slug = models.SlugField(max_length=50, unique=True, null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_absolute_url(self):
        return reverse("article", args=[self.slug])
    
    def _generate_slug(self):
        max_length = self._meta.get_field('slug').max_length
        value = self.name
        slug_candidate = slug_original = slugify(value, allow_unicode=True)
        for i in itertools.count(1):
            if not Blog.objects.filter(slug=slug_candidate).exists():
                break
            slug_candidate = '{}-{}'.format(slug_original, i)

        self.slug = slug_candidate

    def save(self, *args, **kwargs):   
        if not self.pk:
            self._generate_slug()     
        super().save(*args, **kwargs)
    

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
