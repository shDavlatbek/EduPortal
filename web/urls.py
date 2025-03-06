from django.urls import path
from web import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('report/', views.report, name='report'),
    path('help/', views.help, name='help'),
]

