from django.urls import path
from .views import *

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # path('products/', ProductsListView.as_view(), name='products'),
    # path('search/', common_search, name='search'),
    # path('advanced-search/', advanced_search, name='advanced_search'),
    # path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    # path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    # path('close-account/', CloseAccount.as_view(), name='close-account'),
]
