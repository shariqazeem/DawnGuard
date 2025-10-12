from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:conversation_id>/', views.chat_view, name='chat_with_id'),
    path('chat/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('chat/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('settings/', views.settings_view, name='settings'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),]