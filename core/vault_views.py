# core/vault_views.py - Family Vault Views (Dropbox Replacement)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib import messages
import mimetypes
import os
import secrets
from datetime import timedelta

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .models import (
    FamilyMember,
    VaultFile,
    VaultFolder,
    FileShareLink,
    VaultActivity,
    AIGuardianScan,
    AIGuardianAlert
)
from .utils.encryption import EncryptionManager
from .utils.llm_handler import LLMHandler
from .ai_guardian import AIGuardian

encryption_manager = EncryptionManager()
llm_handler = LLMHandler()
ai_guardian = AIGuardian()


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def vault_home(request):
    """
    Main Family Vault dashboard
    Shows: Storage usage, recent files, family members
    """
    # Get or create family member for this user
    family_member, created = FamilyMember.objects.get_or_create(
        user=request.user,
        defaults={
            'display_name': request.user.username.title(),
            'role': 'admin',  # First user is admin
            'avatar_color': '#FF6B35'
        }
    )

    # Get all family members
    all_family_members = FamilyMember.objects.all()

    # Get user's files (only root-level files, not in folders)
    my_files = VaultFile.objects.filter(
        owner=family_member,
        folder__isnull=True  # Only files not in any folder
    ).order_by('-uploaded_at')[:10]

    # Get shared files (also only root-level)
    shared_files = VaultFile.objects.filter(
        Q(shared_with=family_member) | Q(is_public_to_family=True),
        folder__isnull=True  # Only root-level shared files
    ).exclude(owner=family_member).distinct()[:10]

    # Get user's folders
    my_folders = VaultFolder.objects.filter(owner=family_member, parent_folder=None)

    # Calculate storage stats
    storage_used_gb = family_member.get_storage_used_gb()
    storage_quota_gb = family_member.storage_quota_gb
    storage_percentage = family_member.get_storage_percentage()

    # Total family storage
    total_family_storage = VaultFile.objects.aggregate(
        total=Sum('file_size')
    )['total'] or 0
    total_family_storage_gb = total_family_storage / (1024**3)

    # Recent activity
    recent_activity = VaultActivity.objects.filter(member=family_member)[:10]

    # File type breakdown
    file_types = VaultFile.objects.filter(owner=family_member).values('file_type').annotate(
        count=Sum('file_size')
    )

    context = {
        'family_member': family_member,
        'all_family_members': all_family_members,
        'my_files': my_files,
        'shared_files': shared_files,
        'my_folders': my_folders,
        'storage_used_gb': round(storage_used_gb, 2),
        'storage_quota_gb': storage_quota_gb,
        'storage_percentage': round(storage_percentage, 1),
        'total_family_storage_gb': round(total_family_storage_gb, 2),
        'recent_activity': recent_activity,
        'file_types': file_types,
        'total_files': VaultFile.objects.filter(owner=family_member).count(),
    }

    return render(request, 'vault/vault_home.html', context)


@login_required
@csrf_exempt
def upload_file(request):
    """
    Handle file uploads with encryption and AI processing
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Check if user can upload
        if not family_member.file_upload_enabled:
            return JsonResponse({
                'success': False,
                'error': 'File upload is disabled for your account'
            }, status=403)

        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Check storage quota
        file_size = uploaded_file.size
        storage_used_bytes = family_member.get_storage_used_mb() * 1024 * 1024
        quota_bytes = family_member.storage_quota_gb * 1024 * 1024 * 1024

        if storage_used_bytes + file_size > quota_bytes:
            return JsonResponse({
                'success': False,
                'error': f'Storage quota exceeded. Used: {round(storage_used_bytes/(1024**3), 2)}GB / {family_member.storage_quota_gb}GB'
            }, status=400)

        # Get folder (if specified)
        folder_id = request.POST.get('folder_id')
        folder = None
        if folder_id:
            folder = VaultFolder.objects.get(id=folder_id, owner=family_member)

        # Detect mime type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Create VaultFile object
        vault_file = VaultFile(
            name=uploaded_file.name,
            original_name=uploaded_file.name,
            file=uploaded_file,
            owner=family_member,
            folder=folder,
            file_size=file_size,
            mime_type=mime_type,
            is_encrypted=True
        )

        # Detect file type
        vault_file.file_type = vault_file.detect_file_type()

        # Generate thumbnail for images (if PIL is available)
        if vault_file.file_type == 'image' and PIL_AVAILABLE:
            try:
                img = Image.open(uploaded_file)
                vault_file.width = img.width
                vault_file.height = img.height

                # Create thumbnail
                img.thumbnail((300, 300))
                thumb_io = io.BytesIO()
                img.save(thumb_io, format='JPEG', quality=85)
                thumb_io.seek(0)

                # Save thumbnail
                from django.core.files.uploadedfile import InMemoryUploadedFile
                vault_file.thumbnail = InMemoryUploadedFile(
                    thumb_io, None, f'thumb_{uploaded_file.name}', 'image/jpeg',
                    thumb_io.tell(), None
                )
            except Exception as e:
                print(f"Thumbnail generation failed: {e}")

        vault_file.save()

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='upload',
            file=vault_file,
            description=f"Uploaded {vault_file.name}",
            ip_address=get_client_ip(request)
        )

        # ============================================================
        # AI GUARDIAN SCAN - REAL-TIME CONTENT MODERATION
        # ============================================================
        scan_result = None
        try:
            # Read file content for scanning
            file_content = ""
            if vault_file.file_type in ['document', 'other']:
                try:
                    # Try to read text content
                    vault_file.file.seek(0)
                    content_bytes = vault_file.file.read(100000)  # Read first 100KB
                    vault_file.file.seek(0)  # Reset

                    # Try UTF-8 decoding
                    try:
                        file_content = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try latin-1 as fallback
                        file_content = content_bytes.decode('latin-1', errors='ignore')
                except Exception as e:
                    print(f"Could not read file content: {e}")

            # Scan with AI Guardian
            scan_result = ai_guardian.scan_content(
                content=file_content,
                filename=vault_file.name,
                file_type=vault_file.file_type
            )

            # Create Guardian Scan record
            guardian_scan = AIGuardianScan.objects.create(
                file=vault_file,
                scanned_by=family_member,
                status='completed',
                severity=scan_result['severity'],
                risk_score=scan_result['risk_score'],
                detected_patterns=scan_result.get('patterns_detected', []),
                detected_keywords=scan_result.get('keywords_detected', []),
                risk_categories=scan_result.get('categories', []),
                ai_summary=scan_result.get('summary', ''),
                recommendations=scan_result.get('recommendations', ''),
                completed_at=timezone.now()
            )

            # Create alerts if needed (medium, high, critical severity)
            if guardian_scan.is_alert():
                # Determine alert type based on risk categories
                alert_type = 'other'
                if 'personal_data' in scan_result.get('categories', []):
                    alert_type = 'personal_data'
                elif 'inappropriate' in scan_result.get('categories', []):
                    alert_type = 'inappropriate'
                elif 'privacy' in scan_result.get('categories', []):
                    alert_type = 'privacy'
                elif 'security' in scan_result.get('categories', []):
                    alert_type = 'security'

                # Get all admin family members
                admin_members = FamilyMember.objects.filter(role='admin')

                for admin in admin_members:
                    AIGuardianAlert.objects.create(
                        scan=guardian_scan,
                        alert_type=alert_type,
                        title=f"{guardian_scan.get_severity_icon()} {vault_file.name} - {scan_result['severity'].upper()} Risk",
                        description=scan_result.get('summary', f"AI Guardian detected {scan_result['severity']} risk in uploaded file."),
                        family_member=admin,
                        status='active'
                    )

                guardian_scan.parent_notified = True
                guardian_scan.notification_sent_at = timezone.now()
                guardian_scan.save()

        except Exception as e:
            print(f"AI Guardian scan failed: {e}")
            # Create error scan record
            try:
                AIGuardianScan.objects.create(
                    file=vault_file,
                    scanned_by=family_member,
                    status='error',
                    severity='safe',
                    ai_summary=f"Scan failed: {str(e)}"
                )
            except:
                pass

        # AI processing (async in background for production)
        if llm_handler.available and vault_file.file_type in ['image', 'document']:
            try:
                # Generate AI description
                if vault_file.file_type == 'image':
                    ai_prompt = f"Describe this image file named '{vault_file.name}' in one sentence."
                else:
                    ai_prompt = f"What type of document is '{vault_file.name}'? Describe briefly."

                ai_description = llm_handler.generate_response(ai_prompt)
                vault_file.ai_description = ai_description
                vault_file.ai_processed = True

                # Generate tags
                tag_prompt = f"Generate 3-5 relevant tags for a file named '{vault_file.name}'. Return only tags separated by commas."
                ai_tags_str = llm_handler.generate_response(tag_prompt)
                vault_file.ai_tags = [tag.strip() for tag in ai_tags_str.split(',')][:5]

                vault_file.save()
            except Exception as e:
                print(f"AI processing failed: {e}")

        return JsonResponse({
            'success': True,
            'file_id': vault_file.id,
            'file_name': vault_file.name,
            'file_size': vault_file.get_file_size_display(),
            'file_type': vault_file.file_type,
            'uploaded_at': vault_file.uploaded_at.isoformat(),
            'message': 'File uploaded successfully!'
        })

    except FamilyMember.DoesNotExist:
        return JsonResponse({
            'error': 'Family member profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Upload failed: {str(e)}'
        }, status=500)


@login_required
def download_file(request, file_id):
    """
    Download a file from the vault
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)
        vault_file = VaultFile.objects.get(id=file_id)

        # Check permissions
        can_access = (
            vault_file.owner == family_member or
            family_member in vault_file.shared_with.all() or
            vault_file.is_public_to_family
        )

        if not can_access:
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Update stats
        vault_file.download_count += 1
        vault_file.last_accessed = timezone.now()
        vault_file.save()

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='download',
            file=vault_file,
            description=f"Downloaded {vault_file.name}",
            ip_address=get_client_ip(request)
        )

        # Serve file
        file_path = vault_file.file.path
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = vault_file.mime_type
        response['Content-Disposition'] = f'attachment; filename="{vault_file.original_name}"'

        return response

    except FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Family member not found'}, status=404)
    except VaultFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def view_file(request, file_id):
    """
    View file details (preview)
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)
        vault_file = VaultFile.objects.get(id=file_id)

        # Check permissions
        can_access = (
            vault_file.owner == family_member or
            family_member in vault_file.shared_with.all() or
            vault_file.is_public_to_family
        )

        if not can_access:
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='view',
            file=vault_file,
            description=f"Viewed {vault_file.name}",
            ip_address=get_client_ip(request)
        )

        # Get share links
        share_links = vault_file.share_links.filter(is_active=True)

        context = {
            'file': vault_file,
            'family_member': family_member,
            'is_owner': vault_file.owner == family_member,
            'share_links': share_links,
        }

        return render(request, 'vault/file_detail.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('vault_home')


@login_required
@csrf_exempt
def delete_file(request, file_id):
    """
    Delete a file from the vault
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)
        vault_file = VaultFile.objects.get(id=file_id, owner=family_member)

        # Log activity before deleting
        VaultActivity.objects.create(
            member=family_member,
            action='delete',
            description=f"Deleted {vault_file.name}",
            ip_address=get_client_ip(request)
        )

        # Delete file
        file_name = vault_file.name
        vault_file.file.delete()  # Delete physical file
        if vault_file.thumbnail:
            vault_file.thumbnail.delete()
        vault_file.delete()  # Delete database record

        return JsonResponse({
            'success': True,
            'message': f'{file_name} deleted successfully'
        })

    except VaultFile.DoesNotExist:
        return JsonResponse({'error': 'File not found or access denied'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def create_folder(request):
    """
    Create a new folder in the vault
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        folder_name = data.get('name', '').strip()
        parent_folder_id = data.get('parent_folder_id')

        if not folder_name:
            return JsonResponse({'error': 'Folder name required'}, status=400)

        family_member = FamilyMember.objects.get(user=request.user)

        # Get parent folder if specified
        parent_folder = None
        if parent_folder_id:
            parent_folder = VaultFolder.objects.get(id=parent_folder_id, owner=family_member)

        # Create folder
        folder = VaultFolder.objects.create(
            name=folder_name,
            owner=family_member,
            parent_folder=parent_folder
        )

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='upload',
            folder=folder,
            description=f"Created folder '{folder_name}'",
            ip_address=get_client_ip(request)
        )

        return JsonResponse({
            'success': True,
            'folder_id': folder.id,
            'folder_name': folder.name,
            'message': 'Folder created successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def browse_folder(request, folder_id=None):
    """
    Browse files in a specific folder
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Get folder or show root
        current_folder = None
        if folder_id:
            current_folder = VaultFolder.objects.get(id=folder_id, owner=family_member)

        # Get subfolders
        if current_folder:
            subfolders = current_folder.subfolders.all()
        else:
            subfolders = VaultFolder.objects.filter(owner=family_member, parent_folder=None)

        # Get files in this folder
        files = VaultFile.objects.filter(
            owner=family_member,
            folder=current_folder
        ).order_by('-uploaded_at')

        context = {
            'family_member': family_member,
            'current_folder': current_folder,
            'subfolders': subfolders,
            'files': files,
        }

        return render(request, 'vault/browse_folder.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('vault_home')


@login_required
@csrf_exempt
def search_files(request):
    """
    AI-powered file search
    Search by name, AI tags, or description
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)
        query = request.GET.get('q', '').strip()

        if not query:
            return JsonResponse({'results': []})

        # Search in multiple fields
        files = VaultFile.objects.filter(
            owner=family_member
        ).filter(
            Q(name__icontains=query) |
            Q(ai_description__icontains=query) |
            Q(ai_tags__icontains=query)
        ).order_by('-uploaded_at')[:20]

        results = []
        for file in files:
            results.append({
                'id': file.id,
                'name': file.name,
                'type': file.file_type,
                'size': file.get_file_size_display(),
                'uploaded': file.uploaded_at.strftime('%Y-%m-%d'),
                'ai_description': file.ai_description,
                'icon': file.get_icon(),
            })

        return JsonResponse({'results': results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def family_settings(request):
    """
    Manage family members and permissions
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Only admins can access
        if family_member.role != 'admin':
            messages.error(request, 'Only administrators can manage family settings')
            return redirect('vault_home')

        all_members = FamilyMember.objects.all()

        context = {
            'family_member': family_member,
            'all_members': all_members,
        }

        return render(request, 'vault/family_settings.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('vault_home')


@login_required
def storage_analytics(request):
    """
    Detailed storage analytics and usage breakdown
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # File type breakdown
        file_stats = VaultFile.objects.filter(owner=family_member).values('file_type').annotate(
            count=Sum('file_size')
        )

        # Monthly upload trends (last 6 months)
        from django.db.models.functions import TruncMonth
        monthly_uploads = VaultFile.objects.filter(
            owner=family_member
        ).annotate(
            month=TruncMonth('uploaded_at')
        ).values('month').annotate(
            total_size=Sum('file_size'),
            file_count=Count('id')
        ).order_by('-month')[:6]

        context = {
            'family_member': family_member,
            'file_stats': file_stats,
            'monthly_uploads': monthly_uploads,
        }

        return render(request, 'vault/storage_analytics.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('vault_home')


@login_required
@csrf_exempt
def move_file(request, file_id):
    """
    Move a file to a different folder
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        target_folder_id = data.get('target_folder_id')

        family_member = FamilyMember.objects.get(user=request.user)
        vault_file = VaultFile.objects.get(id=file_id, owner=family_member)

        # Get target folder (None for root)
        target_folder = None
        if target_folder_id:
            target_folder = VaultFolder.objects.get(id=target_folder_id, owner=family_member)

        # Move file
        vault_file.folder = target_folder
        vault_file.save()

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='upload',
            file=vault_file,
            description=f"Moved {vault_file.name} to {target_folder.name if target_folder else 'root'}",
            ip_address=get_client_ip(request)
        )

        return JsonResponse({
            'success': True,
            'message': f'File moved to {target_folder.name if target_folder else "root"}'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def toggle_file_share(request, file_id):
    """
    Toggle sharing file with all family members
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        share_with_family = data.get('share_with_family', False)

        family_member = FamilyMember.objects.get(user=request.user)
        vault_file = VaultFile.objects.get(id=file_id, owner=family_member)

        vault_file.is_public_to_family = share_with_family
        vault_file.save()

        # Log activity
        VaultActivity.objects.create(
            member=family_member,
            action='share',
            file=vault_file,
            description=f"{'Shared' if share_with_family else 'Unshared'} {vault_file.name} with family",
            ip_address=get_client_ip(request)
        )

        return JsonResponse({
            'success': True,
            'message': 'Share settings updated'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================
# FAMILY MANAGEMENT FUNCTIONS
# ============================================================

@login_required
def add_family_member(request):
    """
    Add a new family member (admin only) - NO SUPERUSER REQUIRED!
    """
    from django.http import JsonResponse
    from django.contrib.auth.models import User
    import json
    import random

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Check if user is admin
        if family_member.role != 'admin':
            return JsonResponse({'error': 'Only administrators can add family members'}, status=403)

        data = json.loads(request.body)
        username = data.get('username', '').strip().lower()
        display_name = data.get('display_name', '').strip()
        role = data.get('role', 'member')
        storage_quota = int(data.get('storage_quota', 50))
        password = data.get('password', 'blackbox123')  # Default password

        # Validate inputs
        if not username or not display_name:
            return JsonResponse({'error': 'Username and display name are required'}, status=400)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': f'Username "{username}" already exists'}, status=400)

        # Create Django user
        new_user = User.objects.create_user(
            username=username,
            password=password,
            first_name=display_name
        )

        # Generate random avatar color
        colors = ['#FF6B35', '#6B35FF', '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63']
        avatar_color = random.choice(colors)

        # Create family member
        new_member = FamilyMember.objects.create(
            user=new_user,
            display_name=display_name,
            role=role,
            avatar_color=avatar_color,
            storage_quota_gb=storage_quota,
            ai_chat_enabled=(role != 'child'),  # Disable AI for children by default
            file_upload_enabled=True,
            can_share_files=True
        )

        return JsonResponse({
            'success': True,
            'message': f'✅ Family member "{display_name}" added successfully! Default password: {password}',
            'member': {
                'id': new_member.id,
                'username': username,
                'display_name': display_name,
                'role': role,
                'avatar_color': avatar_color
            }
        })

    except FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'You must be a family member to add others'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def update_member_permissions(request, member_id):
    """
    Update family member permissions (admin only) - PARENTAL CONTROLS!
    """
    from django.http import JsonResponse
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Check if user is admin
        if family_member.role != 'admin':
            return JsonResponse({'error': 'Only administrators can update permissions'}, status=403)

        # Get member to update
        target_member = FamilyMember.objects.get(id=member_id)

        # Don't allow modifying yourself
        if target_member.user == request.user:
            return JsonResponse({'error': 'Cannot modify your own permissions'}, status=400)

        data = json.loads(request.body)

        # Update permissions
        if 'ai_chat_enabled' in data:
            target_member.ai_chat_enabled = data['ai_chat_enabled']
        if 'file_upload_enabled' in data:
            target_member.file_upload_enabled = data['file_upload_enabled']
        if 'can_share_files' in data:
            target_member.can_share_files = data['can_share_files']
        if 'storage_quota_gb' in data:
            target_member.storage_quota_gb = int(data['storage_quota_gb'])
        if 'role' in data:
            target_member.role = data['role']

        target_member.save()

        return JsonResponse({
            'success': True,
            'message': f'✅ Permissions updated for {target_member.display_name}'
        })

    except FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Family member not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def delete_family_member(request, member_id):
    """
    Delete a family member (admin only)
    """
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Check if user is admin
        if family_member.role != 'admin':
            return JsonResponse({'error': 'Only administrators can delete family members'}, status=403)

        # Get member to delete
        target_member = FamilyMember.objects.get(id=member_id)

        # Don't allow deleting yourself
        if target_member.user == request.user:
            return JsonResponse({'error': 'Cannot delete yourself'}, status=400)

        display_name = target_member.display_name
        target_user = target_member.user

        # Delete family member and user
        target_member.delete()
        target_user.delete()

        return JsonResponse({
            'success': True,
            'message': f'✅ {display_name} has been removed from the family'
        })

    except FamilyMember.DoesNotExist:
        return JsonResponse({'error': 'Family member not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
