# core/utils/solana_handler.py
import requests
import json
import time

class SolanaHandler:
    """
    Real Solana blockchain integration using RPC calls
    No Python SDK needed - direct HTTP requests to Solana RPC
    """
    
    def __init__(self):
        # Solana Devnet RPC endpoint
        self.rpc_url = "https://api.devnet.solana.com"
        print("✅ Solana Handler initialized (Devnet)")
    
    def create_knowledge_memo(self, knowledge_id, content_hash, title, category):
        """
        Create memo data for Solana Memo Program
        This will be included in the transaction
        """
        memo_data = json.dumps({
            'app': 'DawnGuard',
            'action': 'knowledge_share',
            'knowledge_id': str(knowledge_id),
            'content_hash': content_hash,
            'title': title[:50],  # Truncate for blockchain
            'category': category,
            'timestamp': int(time.time())
        }, separators=(',', ':'))  # Compact JSON
        
        return memo_data
    
    def verify_transaction(self, signature):
        """
        Verify transaction exists on Solana blockchain using RPC
        Returns True if valid and confirmed
        """
        try:
            # Prepare RPC request
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "json",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            # Send request to Solana RPC
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            data = response.json()
            
            # Check if transaction exists and is confirmed
            if 'result' in data and data['result'] is not None:
                result = data['result']
                
                # Transaction found - check if confirmed
                if result.get('meta') and result['meta'].get('err') is None:
                    print(f"✅ Transaction verified on Solana: {signature[:16]}...")
                    return True
                else:
                    print(f"⚠️ Transaction found but failed: {signature[:16]}...")
                    return False
            else:
                print(f"⚠️ Transaction not found on Solana: {signature[:16]}...")
                return False
                
        except Exception as e:
            print(f"❌ Solana verification error: {e}")
            return False
    
    def get_transaction_details(self, signature):
        """
        Get detailed transaction information from Solana
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            data = response.json()
            
            if 'result' in data and data['result']:
                result = data['result']
                
                return {
                    'success': True,
                    'slot': result.get('slot'),
                    'block_time': result.get('blockTime'),
                    'fee': result.get('meta', {}).get('fee', 0) if result.get('meta') else 0,
                    'confirmed': result.get('meta', {}).get('err') is None
                }
            
            return {'success': False, 'error': 'Transaction not found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize handler
solana_handler = SolanaHandler()