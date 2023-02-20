from django.urls import path
from .views import *

app_name = 'dashboard'

urlpatterns = [    
    path('user-list', UserManageView.as_view(), name='usermanage'),
    path('user/inactive', inactive, name='inactive'),
    path('user/delete/<int:pk>', deletuser, name='userdelete'),
    path('user/update/<int:pk>', userinfoupdate, name='userupdate'),
    path('user-detail/<int:pk>', UserDetailView.as_view(), name='user-detail'),
    path('orderhistory/', OrderHistory.as_view(), name='orderhistory'),
    
    path('plan-list', PlanList.as_view(), name='planmanage'),
    path('plan/delete/<int:pk>', deletplan, name='deletplan'),
    path('plan/update/<int:pk>', plan_update, name='plan_update'),
]
