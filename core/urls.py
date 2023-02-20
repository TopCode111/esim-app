from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('profile/', views.UserDetailView.as_view(), name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('change_email/', views.change_email, name='change_email'),
    path('update_profile/', views.update_profile, name='update_profile'),
    
    ## クレジットカード
    path('payment-card/', views.CardView.as_view(), name='payment-card'),
    path('payment/', views.PlanView.as_view(), name='payment-pricing'),
    path('payment-history/',views.payment_history,name='payment_history'), 
    path('config/', views.stripe_config,name='config'),   
    path('create-checkout-session/',views.create_checkout_session),
    path('cancel-checkout-session/',views.cancel_checkout_session),
    path('payment/success/', views.SuccessView.as_view()),
    path('payment/cancelled/', views.CancelledView.as_view()),
    path('payment/webhook/', views.stripe_webhook),
   
]
