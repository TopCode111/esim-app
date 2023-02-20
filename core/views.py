
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
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.generic import ListView, DetailView, View, TemplateView
from .forms import PaymentForm, UserDeleteForm
from .models import Plan, Order, PaymentHistory, UserProfile, Categories
from .permissions import *
import stripe
import calendar
import time
from datetime import datetime
import pytz
import random
import string
stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        }

        userprofile = self.request.user.userprofile
        if userprofile.one_click_purchasing:
            # fetch the users card list
            cards = stripe.Customer.list_sources(
                userprofile.stripe_customer_id,
                limit=3,
                object='card'
            )
            card_list = cards['data']
            if len(card_list) > 0:
                # update the context with the default card
                context.update({
                    'card': card_list[0]
                })
                print(card_list[0])
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    # customer = stripe.Customer.retrieve(
                    # userprofile.stripe_customer_id)
                    # customer.sources.create(source=token)

                    customer = stripe.Customer.modify(
                        userprofile.stripe_customer_id,
                        card=token
                    )
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.save()

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                        card=token
                    )
                    # customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total())

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="jpy",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="jpy",
                        source=token
                    )

                # create the payment
                payment = PaymentHistory()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.plans.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.ref_code = create_ref_code()
                order.save()

                #messages.success(self.request, "決済が成功しました!")
                return redirect("core:paymentcomplete")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "認証されていない!")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "ネットワークエラー!")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "決済失敗!")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "決済失敗!")
                return redirect("/")

        messages.warning(self.request, "受信したデータが無効です!")
        return redirect("/payment/stripe/")

class HomeView(TemplateView):    
    template_name = "home.html"
    
    def get(self,request):
        context = {}
        context['user'] = request.user
        context['plans'] = Plan.objects.all().order_by('-id')
        return render(request,self.template_name,context)

class UserDetailView(LoginRequiredMixin,TemplateView):
    model = User
    template_name = 'user/user_detail.html'
    
    def get(self,request):
        
        context = {}
        context['user'] = request.user
        
        if 'pw_form' not in context:
            context['pw_form'] = SetPasswordForm(user=self.request.user)
        return render(request,self.template_name,context)


class ItemDetailView(TemplateView):
    model = Plan
    template_name = "product.html"


class CloseAccount(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = UserDeleteForm()
        return render(self.request, "close_account.html", {'form': form})

    def post(self, request, *args, **kwargs):
        form = UserDeleteForm(request.POST)
        if form.is_valid():
            user = request.user
            confirm_password = form.cleaned_data.get('password')
            if not check_password(confirm_password, user.password):
                messages.success(
                    request, '申し訳なく存じますが、パスワードが間違っています。ご確認お願いします。')
                return render(self.request, "close_account.html", {'form': form})
            else:
                logout(request)
                # user.delete()
                messages.success(request, 'アカウントが削除されました。')
                return redirect("/")
        return render(self.request, "close_account.html", {'form': form})


@login_required
def update_profile(request):
    username = request.POST.get('username')
    if username == request.user.username:
        pass
    else:
        try:
            user = User.objects.get(username=username)
            messages.add_message(request, messages.ERROR, '既にこのユーザー名は存在する為、登録できません。')
            return redirect("core:profile")
        except User.DoesNotExist:
            user = request.user
            user.username = username
            user.save()
    
    return redirect("core:profile")

@login_required
def change_email(request):
    new_email = request.POST.get('new_email')    
    try:
        user = User.objects.get(email=new_email)
        messages.add_message(request, messages.ERROR, '既にこのメールは存在する為、登録できません。')
        return JsonResponse({"success":"failed"})
    except User.DoesNotExist:
        pass
    user = request.user
    user.email = new_email
    user.save()
    messages.add_message(request, messages.SUCCESS, '成功！')
    return JsonResponse({'status':'success'})

@login_required
def change_password(request):
    pw_form = SetPasswordForm(user=request.user, data=request.POST)
    ctxt = {}
    if pw_form.is_valid():
        print("pw_form is valid")
        messages.add_message(request, messages.SUCCESS, '成功！')
        pw_form.save()
        update_session_auth_hash(request, pw_form.user)                
    else:
        print(pw_form.errors)
        messages.add_message(request, messages.ERROR, 'ERROR')
        ctxt['pw_form'] = pw_form
    
    return redirect('core:profile')

class PlanView(TemplateView):
    model = Plan
    template_name = 'payment/pricing.html'
    
    def get(self,request):
        context = {}
        plans = Plan.objects.all()
        if request.user.is_authenticated:
            paymenthistory = PaymentHistory.objects.filter(user=request.user)
            context['paymenthistory'] = paymenthistory
        context['plans'] = plans
        #context['paymenthistory'] = paymenthistory
        return render(request, self.template_name, context)
    
class CardView(TemplateView):
    model = User
    template_name = 'payment/card.html'
    
    def get(self, request, *args, **kwargs):
        context = {            
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        }
        userprofile = self.request.user.userprofile
        if userprofile.stripe_customer_id:
            # fetch the users card list
            cards = stripe.Customer.list_sources(
                userprofile.stripe_customer_id,
                limit=3,
                object='card'
            )
            card_list = cards['data']
            if len(card_list) > 0:
                # update the context with the default card
                context.update({
                    'card': card_list[0]
                })
                print(card_list[0])
        return render(self.request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:               

                customer = stripe.Customer.modify(
                    userprofile.stripe_customer_id,
                    card=token
                )
                userprofile.stripe_customer_id = customer['id']
                userprofile.save()

            else:
                customer = stripe.Customer.create(
                    email=self.request.user.email,
                    card=token
                )
                # customer.sources.create(source=token)
                userprofile.stripe_customer_id = customer['id']                
                userprofile.save()
            return redirect("core:payment")
        else:
            return redirect("core:payment")
        
@login_required
def payment_history(request):
    payment_history = PaymentHistory.objects.filter(user=request.user)
    return render(request, 'payment/payment_history.html', context={'payment_history':payment_history})

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        plan_id = request.GET.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        user = request.user        
        #domain_url = 'http://127.0.0.1:8003/'
        domain_url = request.scheme+'://'+request.META['HTTP_HOST']+'/'
        if request.user.email == '':
            messages.add_message(request, messages.SUCCESS, 'メールアドレスをご記入ください！')
            email = 'example@domain.com'
            return JsonResponse({'email': 'error'})
        else:
            email = request.user.email
        print(request.user.email)
        dt = time.gmtime()        
        ts = calendar.timegm(dt)        
        timestamp_delta = ts + 14 * 24 * 60 * 60 + 9 * 60 * 60
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            payment_history = PaymentHistory.objects.get(user=user)        
            subscription_id = payment_history.checkout_session
            if subscription_id:
                stripe.Subscription.delete(subscription_id)
        except:
            pass
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'accounts/payment/success?session_id={CHECKOUT_SESSION_ID}&plan_id='+str(plan_id),
                cancel_url=domain_url + 'payment',
                payment_method_types=['card'],
                customer_email=email,
                mode='subscription',
                locale='ja',
                line_items=[
                    {
                        'price': plan.stripe_price_id,
                        "quantity": 1,
                    }
                ],
                
                metadata={'plan_id':plan_id},
                subscription_data={
                    'trial_end':int(timestamp_delta)
                },
                client_reference_id = request.user.id
            )            
            
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    print(event)
    if event['type'] == 'checkout.session.completed':

        data = event['data']['object']
        user_id = data['client_reference_id']
        user = User.objects.get(id=user_id)
        plan_id = int(data['metadata']['plan_id'])
    return HttpResponse(status=200)

class SuccessView(TemplateView):
    template_name = 'payment/payment_success.html'

    def get(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session_id = request.GET.get('session_id')        
        stripe_response = stripe.checkout.Session.retrieve(
            session_id,
            expand=['subscription']
        )
        print(stripe_response['subscription']['id'])
        plan_id = request.GET.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        try:
            payment_history = PaymentHistory.objects.get(user=request.user)            
        except:
            payment_history = PaymentHistory()        
            payment_history.user = request.user
        payment_history.plan_id = plan_id
        payment_history.price = plan.price
        payment_history.checkout_session = stripe_response['subscription']['id']
        payment_history.save()
        return render(request,self.template_name)

class CancelledView(TemplateView):
    template_name = 'payment/payment_cancelled.html'

def cancel_checkout_session(request):
    if request.method == 'GET':
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            checkout_session_id = request.GET.get('checkout_session_id')
            stripe.Subscription.delete(checkout_session_id)
            payment = PaymentHistory.objects.get(checkout_session=checkout_session_id)            
            payment.delete()
            return JsonResponse({'success':True})
        except Exception as e:
            return JsonResponse({'error': str(e)})
