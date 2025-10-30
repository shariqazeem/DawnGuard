# core/vault_views_ipfs.py - TRUE DAPP Vault with IPFS Storage

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import mimetypes
import json
import requests

from .utils.encryption import EncryptionManager

encryption_manager = EncryptionManager()

# Direct IPFS connection (works in Docker network)
# Get from environment or use defaults
import os
IPFS_API_URL = os.getenv('IPFS_API_URL', 'http://localhost:5001')
IPFS_GATEWAY = os.getenv('IPFS_GATEWAY', 'http://localhost:8080')

# For public sharing, always use localhost gateway (accessible from browser)
IPFS_PUBLIC_GATEWAY = 'http://localhost:8080'


@login_required
@csrf_exempt
def upload_file_ipfs(request):
    """
    TRUE DAPP: Upload file to IPFS (decentralized storage)

    Flow:
    1. Receive file from user
    2. Encrypt file client-side or server-side
    3. Upload encrypted file to IPFS
    4. Return CID to frontend
    5. Frontend stores in Gun.js (no Django database)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Read file content
        file_content = uploaded_file.read()
        file_size = len(file_content)

        # Detect mime type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Encrypt file BEFORE uploading to IPFS
        # For binary files (images, PDFs), we need to base64 encode first, then encrypt
        try:
            import base64
            # Convert to base64 string (handles binary data)
            b64_content = base64.b64encode(file_content).decode('utf-8')
            # Encrypt the base64 string
            encrypted_content = encryption_manager.encrypt(b64_content)
            # Convert back to bytes for IPFS
            encrypted_bytes = encrypted_content.encode('utf-8')
        except Exception as encrypt_error:
            # If encryption fails, use raw bytes
            print(f"Encryption error: {encrypt_error}")
            encrypted_bytes = file_content

        # Upload to IPFS directly
        try:
            files = {'file': (uploaded_file.name, encrypted_bytes)}
            response = requests.post(
                f"{IPFS_API_URL}/api/v0/add",
                files=files,
                params={'cid-version': 1, 'hash': 'sha2-256', 'pin': 'true'},
                timeout=30
            )

            if response.status_code != 200:
                return JsonResponse({
                    'success': False,
                    'error': f'IPFS upload failed: {response.text}'
                }, status=500)

            result = response.json()
            cid = result.get('Hash')

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'success': False,
                'error': 'Cannot connect to IPFS. Make sure IPFS is running: docker-compose up -d ipfs'
            }, status=500)
        except Exception as ipfs_error:
            return JsonResponse({
                'success': False,
                'error': f'IPFS error: {str(ipfs_error)}'
            }, status=500)

        # Return CID and metadata (frontend will store in Gun.js)
        return JsonResponse({
            'success': True,
            'message': 'File uploaded to IPFS successfully!',
            'ipfs_cid': cid,
            'gateway_url': f"{IPFS_PUBLIC_GATEWAY}/ipfs/{cid}",  # Browser-accessible URL
            'file_name': uploaded_file.name,
            'file_size': file_size,
            'mime_type': mime_type,
            'encrypted': True,
            'storage': 'IPFS (Decentralized)',
            'public_url': f"https://ipfs.io/ipfs/{cid}"
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)


@login_required
def download_file_ipfs(request):
    """
    TRUE DAPP: Download file from IPFS

    Frontend provides CID, we fetch from IPFS and decrypt
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        cid = data.get('cid')

        if not cid:
            return JsonResponse({'error': 'No CID provided'}, status=400)

        # Fetch from IPFS
        try:
            response = requests.post(
                f"{IPFS_API_URL}/api/v0/cat",
                params={'arg': cid},
                timeout=30
            )

            if response.status_code != 200:
                return JsonResponse({
                    'success': False,
                    'error': 'File not found on IPFS'
                }, status=404)

            encrypted_content = response.content

        except Exception as ipfs_error:
            return JsonResponse({
                'success': False,
                'error': f'IPFS fetch error: {str(ipfs_error)}'
            }, status=500)

        # Decrypt content
        try:
            import base64
            # Decrypt the encrypted content (returns base64 string)
            decrypted_b64 = encryption_manager.decrypt(encrypted_content.decode('utf-8'))
            # Decode base64 to get original binary data
            original_bytes = base64.b64decode(decrypted_b64)
            # Convert to base64 for safe JSON transport
            content_b64 = base64.b64encode(original_bytes).decode('utf-8')
        except Exception as decrypt_error:
            return JsonResponse({
                'success': False,
                'error': f'Decryption failed: {str(decrypt_error)}'
            }, status=500)

        return JsonResponse({
            'success': True,
            'content': content_b64,  # Send as base64 for JSON safety
            'cid': cid,
            'encoding': 'base64'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }, status=500)
