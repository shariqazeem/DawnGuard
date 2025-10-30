# core/utils/ipfs_handler.py
import requests
import json
from typing import Optional, Dict, Any


class IPFSHandler:
    """
    Handle IPFS integration for decentralized file storage
    Uses IPFS HTTP API (no Python SDK needed)
    """

    def __init__(self, ipfs_api_url=None):
        """
        Initialize IPFS handler
        :param ipfs_api_url: IPFS API endpoint
        """
        # Try multiple endpoints
        if ipfs_api_url:
            self.api_url = ipfs_api_url
        else:
            # Try Docker container name first, then localhost
            for url in ['http://dawnguard_ipfs:5001', 'http://localhost:5001', 'http://127.0.0.1:5001']:
                if self._test_connection(url):
                    self.api_url = url
                    break
            else:
                self.api_url = 'http://localhost:5001'  # Default fallback

        self.gateway_url = 'http://localhost:8080'  # IPFS gateway for retrieval
        self.available = self.check_ipfs_connection()

        if self.available:
            print(f"✅ IPFS Handler initialized - Connected to {self.api_url}")
        else:
            print(f"⚠️  IPFS Handler - WARNING: IPFS daemon not available at {self.api_url}")
            print("   Files will be stored locally. Start IPFS with: docker-compose up ipfs")

    def _test_connection(self, url):
        """Quick test if URL is reachable"""
        try:
            response = requests.get(f"{url}/api/v0/version", timeout=1)
            return response.status_code == 200
        except:
            return False

    def check_ipfs_connection(self) -> bool:
        """Check if IPFS daemon is running"""
        try:
            response = requests.get(f"{self.api_url}/api/v0/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def add_file(self, file_content: bytes, filename: str = None) -> Optional[Dict[str, str]]:
        """
        Add file to IPFS

        :param file_content: File content as bytes
        :param filename: Optional filename
        :return: Dict with 'cid' and 'size', or None if failed
        """
        if not self.available:
            print("⚠️  IPFS not available - file not uploaded to IPFS")
            return None

        try:
            # Prepare file for upload
            files = {
                'file': (filename or 'file', file_content)
            }

            # Add to IPFS
            response = requests.post(
                f"{self.api_url}/api/v0/add",
                files=files,
                params={
                    'cid-version': 1,  # Use CIDv1 (modern format)
                    'hash': 'sha2-256',
                    'pin': 'true'  # Pin by default to prevent garbage collection
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                cid = result.get('Hash')
                size = result.get('Size')

                print(f"✅ File added to IPFS: {cid}")

                return {
                    'cid': cid,
                    'size': int(size),
                    'gateway_url': f"{self.gateway_url}/ipfs/{cid}",
                    'filename': filename
                }
            else:
                print(f"❌ IPFS add failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ IPFS add error: {str(e)}")
            return None

    def get_file(self, cid: str) -> Optional[bytes]:
        """
        Retrieve file from IPFS by CID

        :param cid: IPFS Content Identifier
        :return: File content as bytes, or None if failed
        """
        if not self.available:
            print("⚠️  IPFS not available - cannot retrieve file")
            return None

        try:
            response = requests.post(
                f"{self.api_url}/api/v0/cat",
                params={'arg': cid},
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ File retrieved from IPFS: {cid}")
                return response.content
            else:
                print(f"❌ IPFS cat failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ IPFS retrieval error: {str(e)}")
            return None

    def pin_file(self, cid: str) -> bool:
        """
        Pin file to prevent garbage collection

        :param cid: IPFS Content Identifier
        :return: True if pinned successfully
        """
        if not self.available:
            return False

        try:
            response = requests.post(
                f"{self.api_url}/api/v0/pin/add",
                params={'arg': cid},
                timeout=10
            )

            return response.status_code == 200
        except Exception:
            return False

    def unpin_file(self, cid: str) -> bool:
        """
        Unpin file (allows garbage collection)

        :param cid: IPFS Content Identifier
        :return: True if unpinned successfully
        """
        if not self.available:
            return False

        try:
            response = requests.post(
                f"{self.api_url}/api/v0/pin/rm",
                params={'arg': cid},
                timeout=10
            )

            return response.status_code == 200
        except Exception:
            return False

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get IPFS node statistics

        :return: Dict with repo stats, or None if failed
        """
        if not self.available:
            return None

        try:
            response = requests.post(
                f"{self.api_url}/api/v0/repo/stat",
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def get_peers(self) -> list:
        """
        Get list of connected IPFS peers

        :return: List of peer IDs
        """
        if not self.available:
            return []

        try:
            response = requests.post(
                f"{self.api_url}/api/v0/swarm/peers",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                peers = data.get('Peers', [])
                return [peer.get('Peer') for peer in peers if 'Peer' in peer]
            return []
        except Exception:
            return []

    def add_encrypted_file(self, encrypted_content: bytes, filename: str = None) -> Optional[Dict[str, str]]:
        """
        Add already-encrypted file to IPFS
        (Encryption should be done BEFORE calling this)

        :param encrypted_content: Already encrypted file content
        :param filename: Optional filename
        :return: Dict with CID and metadata
        """
        return self.add_file(encrypted_content, filename)

    def get_gateway_url(self, cid: str) -> str:
        """
        Get public IPFS gateway URL for a CID

        :param cid: IPFS Content Identifier
        :return: Full gateway URL
        """
        return f"{self.gateway_url}/ipfs/{cid}"

    def get_public_gateway_url(self, cid: str) -> str:
        """
        Get public gateway URL (ipfs.io) for sharing

        :param cid: IPFS Content Identifier
        :return: Public gateway URL
        """
        return f"https://ipfs.io/ipfs/{cid}"


# Initialize global IPFS handler
ipfs_handler = IPFSHandler()
