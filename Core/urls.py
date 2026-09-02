from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
   # path('val',views.validation, name='validation'),
    path('locker',views.addToLocker, name='locker'),
    path('apply',views.apply_for_verification, name='apply'),
    path('verify',views.verify, name='verify'),
    path('history', views.transaction_history, name='history'),
    path('revoke', views.revoke_certificate, name='revoke'),
    path('docs', views.docs, name='docs'),
    path('logout', views.logout, name='logout'),
]