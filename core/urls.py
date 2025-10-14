# core/urls.py - Add these new paths

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
    path('blackbox/dashboard/', views.blackbox_dashboard_view, name='blackbox_dashboard'),
    path('blackbox/status/', views.blackbox_status, name='blackbox_status'),
    path('analytics/', views.analytics_view, name='analytics'),

    # P2P Network
    path('p2p/', views.p2p_network_view, name='p2p_network'),
    path('p2p/share/', views.share_knowledge, name='share_knowledge'),
    path('p2p/connect/<str:node_id>/', views.connect_to_node, name='connect_to_node'),
    path('p2p/download/<int:knowledge_id>/', views.download_knowledge, name='download_knowledge'),
    path('p2p/upvote/<int:knowledge_id>/', views.upvote_knowledge, name='upvote_knowledge'),
    
    # Zero-Knowledge Proof
    path('zkp/', views.zkp_auth_view, name='zkp_auth'),
    path('zkp/challenge/', views.generate_zkp_challenge, name='generate_zkp_challenge'),
    path('zkp/verify/', views.verify_zkp, name='verify_zkp'),
    path('zkp/login/', views.zkp_login_view, name='zkp_login'),
    path('zkp/setup-page/', views.setup_zkp_view, name='setup_zkp_view'),
    path('zkp/setup/', views.setup_zkp, name='setup_zkp'),
    path('zkp/check/', views.check_zkp_enabled, name='check_zkp_enabled'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

        # Wallet Authentication
    path('wallet/login/', views.wallet_login_view, name='wallet_login'),
    path('wallet/auth/challenge/', views.wallet_auth_challenge, name='wallet_auth_challenge'),
    path('wallet/auth/verify/', views.wallet_auth_verify, name='wallet_auth_verify'),
    path('auth/wallet/', views.auth_wallet, name='auth_wallet'),
    path('wallet/link/', views.wallet_link, name='wallet_link'),

    path('p2p/confirm-blockchain/', views.confirm_blockchain_share, name='confirm_blockchain_share'),
    path('governance/', views.governance_view, name='governance'),
    path('governance/vote/<int:proposal_id>/', views.vote_on_proposal, name='vote_proposal'),
    path('p2p/confirm-blockchain/', views.confirm_blockchain_share, name='confirm_blockchain_share'),

]