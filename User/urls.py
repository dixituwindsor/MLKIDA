from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.loginUser, name='loginUser'),
    path('register/', views.createUser, name='createUser'),
    path('logout/', views.logoutUser, name='logoutUser'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('login_history/<str:username>/', views.user_login_history, name='user_login_history'),
    path('video_upload_history/<str:username>/', views.user_video_upload_history, name='user_video_upload_history'),
    path('upload/', views.upload_video, name='upload_video'),
]