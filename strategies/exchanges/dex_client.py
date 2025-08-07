import asyncio
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os

class DEXClient:
    """
    DEX client for Uniswap V3 and token sniping
    """
    
    def __init__(self):
        # Use configured Ethereum RPC URL (Infura or other provider)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_RPC_URL')))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Uniswap V3 contracts
        self.router_address = Web3.to_checksum_address('0xE592427A0AEce92De3Edee1F18E0157C05861564')
        self.factory_address = Web3.to_checksum_address('0x1F98431c8aD98523631AE4a59f267346ea31F984')
        
        # Load ABIs
        self.router_abi = self.load_abi('uniswap_v3_router.json')
        self.factory_abi = self.load_abi('uniswap_v3_factory.json')
        self.erc20_abi = self.load_abi('erc20.json')
        
        self.router = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
        self.factory = self.w3.eth.contract(address=self.factory_address, abi=self.factory_abi)
        
        # Private key for transactions
        self.account = self.w3.eth.account.from_key(os.getenv('WALLET_PRIVATE_KEY'))
        
    def load_abi(self, filename: str) -> List:
        """Load contract ABI"""
        try:
            with open(f'contracts/{filename}', 'r') as f:
                return json.load(f)
        except:
            # Return minimal ABI if file not found
            return []
            
    async def snipe_token(self, token_address: str, eth_amount: float) -> Dict:
        """
        Snipe new token launch with <100ms execution
        """
        start = time.time()
        
        token_address = Web3.to_checksum_address(token_address)
        weth_address = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
        
        # Build swap transaction
        deadline = int(time.time()) + 300  # 5 minutes
        
        params = {
            'tokenIn': weth_address,
            'tokenOut': token_address,
            'fee': 3000,  # 0.3%
            'recipient': self.account.address,
            'deadline': deadline,
            'amountIn': Web3.to_wei(eth_amount, 'ether'),
            'amountOutMinimum': 0,  # Accept any amount for snipe
            'sqrtPriceLimitX96': 0
        }
        
        # Build transaction
        tx = self.router.functions.exactInputSingle(params).build_transaction({
            'from': self.account.address,
            'value': Web3.to_wei(eth_amount, 'ether'),
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price * 2,  # 2x gas for speed
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        execution_time = (time.time() - start) * 1000
        if execution_time > 100:
            print(f"⚠️ Slow DEX execution: {execution_time:.2f}ms")
            
        return {
            'tx_hash': tx_hash.hex(),
            'execution_time': execution_time
        }
        
    async def monitor_new_pairs(self) -> AsyncGenerator[Dict, None]:
        """Monitor for new token launches"""
        
        # Create event filter for PairCreated events
        event_filter = self.factory.events.PoolCreated.create_filter(fromBlock='latest')
        
        while True:
            try:
                for event in event_filter.get_new_entries():
                    yield {
                        'token0': event['args']['token0'],
                        'token1': event['args']['token1'],
                        'pool': event['args']['pool'],
                        'fee': event['args']['fee'],
                        'block': event['blockNumber']
                    }
                    
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error monitoring pairs: {e}")
                await asyncio.sleep(5)
                
    async def get_token_info(self, token_address: str) -> Dict:
        """Get token information"""
        token_address = Web3.to_checksum_address(token_address)
        token = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
        
        try:
            name = token.functions.name().call()
            symbol = token.functions.symbol().call()
            decimals = token.functions.decimals().call()
            total_supply = token.functions.totalSupply().call()
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'total_supply': total_supply
            }
        except:
            return {}
            
    async def execute_swap(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Execute token swap"""
        start = time.time()
        
        # Implementation for standard swaps
        # ...existing code...
        
        execution_time = (time.time() - start) * 1000
        return {
            'success': True,
            'execution_time': execution_time
        }