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
    path('user/', views.user, name='user'),
    path('user/add/', views.user_add, name='user_add'),
    path('user/export/', views.export_students, name='export_students'),
    # path('user/edit/<int:pk>/', views.user_edit, name='user_edit'),
    # path('user/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('teacher/', views.teacher, name='teacher'),
    path('teacher/add/', views.teacher_add, name='teacher_add'),
    path('teacher/export/', views.export_teachers, name='export_teachers'),
]

