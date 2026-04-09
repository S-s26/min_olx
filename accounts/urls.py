from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/',views.signup,name='signup'),
    path('login/',views.logins,name='login'),
    path('logout/',views.logout_user,name='logout'),
    # path('verifyotp/', views.verify_otp,name='verifyotp')
]