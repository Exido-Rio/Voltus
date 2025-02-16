from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
   # path('val',views.validation, name='validation'),
    path('locker',views.addToLocker, name='locker'),
    path('apply',views.apply_for_verification, name='apply'),
    path('verify',views.verify, name='verify'),
    path('logout',views.logout, name='logout'),
   # path('nonce',views.generate_nonce, name='nonce'),
   # path('authenticate_wallet',views.authenticate_wallet, name='authenticate_wallet'),
    
]