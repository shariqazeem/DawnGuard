# core/blackbox_views.py - Black Box Hardware Dashboard
"""
Priority 3: Black Box Hardware Dashboard
Shows real-time system stats, container management, and storage breakdown
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import psutil
import os
import subprocess
import json

@login_required
def blackbox_dashboard_view(request):
    """
    Black Box Hardware Dashboard - Real-time monitoring
    """
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network stats
        net_io = psutil.net_io_counters()
        
        context = {
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': round(disk.percent, 1),
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'net_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
            'net_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
        }
        
        return render(request, 'blackbox/dashboard.html', context)
        
    except Exception as e:
        return render(request, 'blackbox/dashboard.html', {
            'error': str(e),
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
        })


@login_required
def blackbox_status_api(request):
    """
    API endpoint for real-time stats (AJAX polling)
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        # Get container stats if Docker is available
        containers = []
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            containers.append(json.loads(line))
                        except:
                            pass
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': round(disk.percent, 1),
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'net_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
            'net_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
            'containers_count': len(containers),
            'containers': containers[:5],  # First 5 containers
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required  
def storage_breakdown_api(request):
    """
    Storage breakdown showing what's using space on Black Box
    """
    try:
        from .models import VaultFile, FamilyMember
        
        # Calculate vault storage
        vault_files = VaultFile.objects.all()
        total_vault_size = sum(f.file_size for f in vault_files)
        vault_size_gb = round(total_vault_size / (1024**3), 2)
        
        # Estimate AI models size (if Ollama directory exists)
        ai_models_gb = 0
        try:
            ollama_path = '/root/.ollama/models'  # Common Ollama path
            if os.path.exists(ollama_path):
                ai_models_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(ollama_path)
                    for filename in filenames
                )
                ai_models_gb = round(ai_models_size / (1024**3), 2)
        except:
            ai_models_gb = 5  # Estimate if we can't access
        
        # Get total disk usage
        disk = psutil.disk_usage('/')
        total_used_gb = round(disk.used / (1024**3), 2)
        total_gb = round(disk.total / (1024**3), 2)
        
        # Calculate system overhead
        system_gb = round(total_used_gb - vault_size_gb - ai_models_gb, 2)
        if system_gb < 0:
            system_gb = 10  # Estimate
        
        available_gb = round(disk.free / (1024**3), 2)
        
        return JsonResponse({
            'success': True,
            'breakdown': {
                'vault': vault_size_gb,
                'ai_models': ai_models_gb,
                'system': system_gb,
                'available': available_gb,
                'total': total_gb,
            },
            'vault_files_count': vault_files.count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
