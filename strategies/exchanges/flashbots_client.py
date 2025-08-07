import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
import aiohttp
import os

class FlashbotsClient:
    """
    Flashbots client for MEV extraction
    """
    
    def __init__(self):
        # Use configured Ethereum RPC URL (Infura or other provider)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_RPC_URL')))
        self.flashbots_url = "https://relay.flashbots.net"
        
        # Signing account
        self.signer: LocalAccount = Account.from_key(os.getenv('FLASHBOTS_SIGNER_KEY'))
        self.account: LocalAccount = Account.from_key(os.getenv('WALLET_PRIVATE_KEY'))
        
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def send_bundle(self, transactions: List[Dict]) -> Dict:
        """
        Send bundle to Flashbots with <100ms execution
        """
        start = time.time()
        
        # Get current block
        block_number = self.w3.eth.block_number
        target_block = block_number + 1
        
        # Sign bundle
        bundle = []
        for tx in transactions:
            signed_tx = self.account.sign_transaction(tx)
            bundle.append({
                'signed_transaction': signed_tx.rawTransaction.hex()
            })
            
        # Prepare request
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'eth_sendBundle',
            'params': [{
                'txs': [tx['signed_transaction'] for tx in bundle],
                'blockNumber': hex(target_block),
                'minTimestamp': 0,
                'maxTimestamp': int(time.time()) + 120
            }]
        }
        
        # Sign the payload
        message = Web3.keccak(text=json.dumps(body))
        signature = self.signer.signHash(message)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Flashbots-Signature': f"{self.signer.address}:{signature.signature.hex()}"
        }
        
        async with self.session.post(
            self.flashbots_url,
            headers=headers,
            json=body
        ) as response:
            result = await response.json()
            
        execution_time = (time.time() - start) * 1000
        if execution_time > 100:
            print(f"⚠️ Slow Flashbots execution: {execution_time:.2f}ms")
            
        return {
            'bundle_hash': result.get('result', {}).get('bundleHash'),
            'execution_time': execution_time
        }
        
    async def simulate_bundle(self, transactions: List[Dict]) -> Dict:
        """Simulate bundle execution"""
        
        body = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'eth_callBundle',
            'params': [{
                'txs': [self.account.sign_transaction(tx).rawTransaction.hex() for tx in transactions],
                'blockNumber': hex(self.w3.eth.block_number + 1),
                'stateBlockNumber': 'latest'
            }]
        }
        
        message = Web3.keccak(text=json.dumps(body))
        signature = self.signer.signHash(message)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Flashbots-Signature': f"{self.signer.address}:{signature.signature.hex()}"
        }
        
        async with self.session.post(
            f"{self.flashbots_url}/simulate",
            headers=headers,
            json=body
        ) as response:
            return await response.json()
            
    async def find_sandwich_opportunity(self, pending_tx: Dict) -> Optional[Dict]:
        """
        Find sandwich attack opportunity in pending transaction
        """
        
        # Decode transaction
        try:
            # Check if it's a swap transaction
            if self.is_swap_transaction(pending_tx):
                # Calculate sandwich profitability
                front_run_tx = self.build_front_run_tx(pending_tx)
                back_run_tx = self.build_back_run_tx(pending_tx)
                
                # Simulate bundle
                simulation = await self.simulate_bundle([front_run_tx, pending_tx, back_run_tx])
                
                if simulation.get('result', {}).get('coinbaseDiff', 0) > 0:
                    return {
                        'target_tx': pending_tx,
                        'front_run': front_run_tx,
                        'back_run': back_run_tx,
                        'expected_profit': simulation['result']['coinbaseDiff']
                    }
        except Exception as e:
            print(f"Error analyzing transaction: {e}")
            
        return None
        
    def is_swap_transaction(self, tx: Dict) -> bool:
        """Check if transaction is a swap"""
        # Check for common DEX router addresses
        dex_routers = [
            '0xE592427A0AEce92De3Edee1F18E0157C05861564',  # Uniswap V3
            '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2
            '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'   # SushiSwap
        ]
        
        return tx.get('to', '').lower() in [addr.lower() for addr in dex_routers]
        
    def build_front_run_tx(self, target_tx: Dict) -> Dict:
        """Build front-running transaction"""
        # Implementation would analyze the target transaction
        # and build a transaction that profits from executing first
        return {}
        
    def build_back_run_tx(self, target_tx: Dict) -> Dict:
        """Build back-running transaction"""
        # Implementation would build a transaction that profits
        # from executing after the target
        return {}
        
    async def monitor_mempool(self) -> AsyncGenerator[Dict, None]:
        """Monitor mempool for MEV opportunities"""
        
        # Subscribe to pending transactions
        pending_filter = self.w3.eth.filter('pending')
        
        while True:
            try:
                pending_txs = pending_filter.get_new_entries()
                
                for tx_hash in pending_txs:
                    try:
                        tx = self.w3.eth.get_transaction(tx_hash)
                        
                        # Check for sandwich opportunity
                        opportunity = await self.find_sandwich_opportunity(tx)
                        if opportunity:
                            yield opportunity
                            
                    except Exception as e:
                        continue
                        
                await asyncio.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                print(f"Mempool monitoring error: {e}")
                await asyncio.sleep(1)
                
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
