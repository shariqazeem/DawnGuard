# core/urls.py - Add these new paths

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import vault_views
from . import family_views
from . import blackbox_views
from . import setup_views
from . import memory_views

urlpatterns = [
    # ============================================================
    # ONE-TIME SETUP WIZARD (First Run Experience)
    # ============================================================
    path('welcome/', setup_views.welcome_animation, name='welcome_animation'),
    path('setup/', setup_views.setup_wizard, name='setup_wizard'),
    path('setup/complete/', setup_views.complete_setup, name='complete_setup'),
    path('setup/status/', setup_views.get_setup_status, name='setup_status'),

    # Family-Focused Routes (NEW - Main Routes)
    path('', family_views.family_home, name='home'),
    path('family/', family_views.family_dashboard, name='family_dashboard'),
    path('kids-ai/', family_views.kids_ai_home, name='kids_ai_home'),
    path('kids-ai/chat/', family_views.kids_ai_chat, name='kids_ai_chat'),
    path('kids-ai/conversation/<int:conversation_id>/', family_views.get_conversation_detail, name='kids_ai_conversation_detail'),

    # Legacy routes (kept for backwards compatibility)
    path('old-home/', views.home, name='old_home'),
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
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        next_page='family_dashboard'  # Redirect to family dashboard
    ), name='login'),
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

    # ============================================================
    # FAMILY VAULT - Private Cloud Storage (Dropbox Killer!)
    # ============================================================
    path('vault/', vault_views.vault_home, name='vault_home'),
    path('vault/upload/', vault_views.upload_file, name='vault_upload'),
    path('vault/file/<int:file_id>/', vault_views.view_file, name='vault_view_file'),
    path('vault/file/<int:file_id>/download/', vault_views.download_file, name='vault_download_file'),
    path('vault/file/<int:file_id>/delete/', vault_views.delete_file, name='vault_delete_file'),
    path('vault/file/<int:file_id>/move/', vault_views.move_file, name='vault_move_file'),
    path('vault/file/<int:file_id>/toggle-share/', vault_views.toggle_file_share, name='vault_toggle_share'),
    path('vault/folder/create/', vault_views.create_folder, name='vault_create_folder'),
    path('vault/folder/<int:folder_id>/', vault_views.browse_folder, name='vault_browse_folder'),
    path('vault/search/', vault_views.search_files, name='vault_search'),
    path('vault/family/', vault_views.family_settings, name='vault_family_settings'),
    path('vault/family/add/', vault_views.add_family_member, name='vault_add_member'),
    path('vault/family/<int:member_id>/update/', vault_views.update_member_permissions, name='vault_update_member'),
    path('vault/family/<int:member_id>/delete/', vault_views.delete_family_member, name='vault_delete_member'),
    path('vault/analytics/', vault_views.storage_analytics, name='vault_analytics'),

    # ============================================================
    # BLACK BOX HARDWARE DASHBOARD - Priority 3
    # ============================================================
    path('blackbox/', blackbox_views.blackbox_dashboard_view, name='blackbox_dashboard'),
    path('blackbox/status/', blackbox_views.blackbox_status_api, name='blackbox_status'),
    path('blackbox/storage/', blackbox_views.storage_breakdown_api, name='blackbox_storage'),

    # ============================================================
    # AI GUARDIAN ALERTS - Content Moderation
    # ============================================================
    path('guardian/', views.guardian_alerts_view, name='guardian_alerts'),

    # ============================================================
    # ENCRYPTED FAMILY MEMORY - Digital Journal System
    # ============================================================
    path('memory/', memory_views.memory_home, name='memory_home'),
    path('memory/entry/create/', memory_views.create_journal_entry, name='memory_create_entry'),
    path('memory/entries/', memory_views.view_journal_entries, name='memory_entries'),
    path('memory/summary/generate/', memory_views.generate_weekly_summary, name='memory_generate_summary'),
    path('memory/summaries/', memory_views.view_weekly_summaries, name='memory_summaries'),
    path('memory/search/', memory_views.search_memories, name='memory_search'),

]