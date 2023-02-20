import random
import string

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm,SetPasswordForm
from django.contrib.auth import get_user_model,update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.decorators import user_passes_test
from core.models import Plan, Order, PaymentHistory, UserProfile, Categories
from core.permissions import SuperUserCheck
from .forms import UserUpdateForm
from django_countries import countries
User = get_user_model()

class UserManageView(SuperUserCheck,ListView):
    model = User    
    template_name = "user/userlist.html"

class OrderHistory(SuperUserCheck,ListView):
    template_name = 'admin/orderhistory.html'
    model = Order    
    paginate_by = 10    

    def get_queryset(self):
        return Order.objects.all().order_by('-id')
    
class UserDetailView(LoginRequiredMixin,TemplateView):
    model = User
    template_name = 'user/user_detail.html'
    
    def get(self,request,pk):
        
        context = {}
        user = get_object_or_404(User,id=pk)
        context['user'] = user
        
        if 'pw_form' not in context:
            context['pw_form'] = SetPasswordForm(user=user)
        return render(request,self.template_name,context)
    
@user_passes_test(lambda u: u.is_superuser)  
def inactive(request):
    pk = request.POST.get('user_id')
    user = get_object_or_404(User, id=pk)
    active_status = user.is_active
    if active_status:
        active_status = 0
    else:
        active_status = 1
    user.is_active = active_status
    user.save()
    resp = HttpResponse(f'{{"active_status": "{user.is_active}"}}')
    resp.content_type = "application/json"
    resp.status_code = 200
    return resp

@user_passes_test(lambda u: u.is_superuser)  
def deletuser(request, pk):
    user = get_object_or_404(User, id=pk)
    
    user.delete()
    return redirect("dashboard:usermanage")

@user_passes_test(lambda u: u.is_superuser)
def userinfoupdate(request,pk):
    form_class = UserUpdateForm(data=request.POST,pk=pk)    
    if form_class.is_valid():
        try:
            user = form_class.update(pk)
            messages.add_message(request, messages.SUCCESS, '成功!')
            return redirect('dashboard:user-detail', pk=pk)
        except:
            messages.add_message(request, messages.ERROR, '失敗!')
            return redirect('dashboard:user-detail', pk=pk)        
    else:
        print("failed")
        messages.add_message(request, messages.ERROR, '失敗!')
        return redirect('dashboard:user-detail', pk=pk)

########## プラン管理 ###############
class PlanList(SuperUserCheck,TemplateView):
    model = Plan    
    template_name = "admin/plan_manage.html"

    def get(self,request, **kwargs):
        context = {}
        context['plans'] = Plan.objects.all()
        context['countries'] = countries
        return render(request, self.template_name, context)
    
    def post(self,request, **kwargs):
        plan_id = request.POST.get('plan_id')
        plan_name = request.POST.get('plan_name')
        plan_country = request.POST.get('country')
        coverage_area = request.POST.get('coverage_area')
        plan_data = request.POST.get('plan_data')
        plan_price = request.POST.get('plan_price')
        plan_provider = request.POST.get('plan_provider')
        plan_network = request.POST.get('plan_network')
        summary = request.POST.get('summary')
        stripe_price_id = request.POST.get('stripe_price_id')
        
        plan = Plan()
        plan.planID = plan_id
        plan.name = plan_name
        plan.country = plan_country
        plan.coverage_area = coverage_area
        plan.plan_data = plan_data        
        plan.plan_price = plan_price
        plan.plan_provider = plan_provider
        plan.plan_network = plan_network
        plan.summary = summary
        plan.stripe_price_id = stripe_price_id
        plan.save()
        return redirect("dashboard:planmanage")
    
class PlanDetail(SuperUserCheck,DetailView):
    model = Plan    
    template_name = "admin/plan_manage.html" 
    
@user_passes_test(lambda u: u.is_superuser)  
def deletplan(request, pk):
    obj = get_object_or_404(Plan, id=pk)
    
    obj.delete()
    return redirect("dashboard:planmanage")

@user_passes_test(lambda u: u.is_superuser)  
def plan_update(request, pk):
    plan = get_object_or_404(Plan, id=pk)
    plan_id = request.POST.get('plan_id')
    plan_name = request.POST.get('plan_name')
    plan_country = request.POST.get('country')
    coverage_area = request.POST.get('coverage_area')
    plan_data = request.POST.get('plan_data')
    plan_price = request.POST.get('plan_price')
    plan_provider = request.POST.get('plan_provider')
    plan_network = request.POST.get('plan_network')
    summary = request.POST.get('summary')
    stripe_price_id = request.POST.get('stripe_price_id')
    
    plan.planID = plan_id
    plan.name = plan_name
    plan.country = plan_country
    plan.coverage_area = coverage_area
    plan.plan_data = plan_data        
    plan.plan_price = plan_price
    plan.plan_provider = plan_provider
    plan.plan_network = plan_network
    plan.summary = summary
    plan.stripe_price_id = stripe_price_id
    plan.save()
    return redirect("dashboard:planmanage")