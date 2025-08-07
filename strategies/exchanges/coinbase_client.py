import asyncio
import hmac
import hashlib
import time
import json
from typing import Dict, Any, Optional, List
import aiohttp
import websockets
from decimal import Decimal
import os

class CoinbaseClient:
    """
    Coinbase Advanced Trade API client with <100ms execution
    """
    
    def __init__(self):
        self.api_key = os.getenv('COINBASE_API_KEY')
        self.api_secret = os.getenv('COINBASE_SECRET')
        
        # Check if we're using mock keys
        self.is_mock_mode = (
            not self.api_key or 
            'mock' in self.api_key.lower() or 
            'test' in self.api_key.lower()
        )
        
        if self.is_mock_mode:
            print("🧪 CoinbaseClient: Running in MOCK mode - no real API calls")
            self.base_url = 'https://api.coinbase.com/api/v3/brokerage'  # Still set for structure
        else:
            print("🔥 CoinbaseClient: Running in LIVE mode - real API calls enabled")
            self.base_url = 'https://api.coinbase.com/api/v3/brokerage'
            
        self.ws_url = 'wss://advanced-trade-ws.coinbase.com'
        self.session = None
        self.ws = None
        
    async def initialize(self):
        """Initialize HTTP session and WebSocket connection"""
        self.session = aiohttp.ClientSession()
        await self.connect_websocket()
        
    async def connect_websocket(self):
        """Connect to Coinbase WebSocket for real-time data"""
        self.ws = await websockets.connect(self.ws_url)
        
        # Subscribe to channels
        await self.subscribe_to_channels(['ticker', 'level2', 'trades'])
        
        # Start listening
        asyncio.create_task(self.listen_websocket())
        
    async def listen_websocket(self):
        """Listen to WebSocket messages"""
        while True:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                await self.process_ws_message(data)
            except Exception as e:
                print(f"WebSocket error: {e}")
                await self.reconnect_websocket()
                
    async def reconnect_websocket(self):
        """Reconnect WebSocket on disconnect"""
        await asyncio.sleep(1)
        await self.connect_websocket()
        
    def generate_signature(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        """Generate CB-ACCESS-SIGN header"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
        
    async def place_order(self, side: str, symbol: str, size: float, order_type: str = 'market') -> Dict:
        """
        Place order with <100ms execution
        Returns order ID and status
        """
        start = time.time()
        
        # Mock mode - simulate order execution
        if self.is_mock_mode:
            execution_time = time.time() - start
            print(f"🧪 MOCK ORDER: {side.upper()} {size} {symbol} - Simulated in {execution_time*1000:.1f}ms")
            
            return {
                'order_id': f"mock_order_{int(time.time()*1000)}",
                'status': 'FILLED',
                'side': side.upper(),
                'symbol': symbol,
                'size': size,
                'price': 50000.0 + (time.time() % 1000),  # Mock price
                'execution_time_ms': execution_time * 1000,
                'mock_mode': True
            }
        
        # Real trading mode
        path = '/orders'
        timestamp = str(int(time.time()))
        
        body = {
            'client_order_id': f"v26_{int(time.time()*1000)}",
            'product_id': symbol,
            'side': side.upper(),
            'order_configuration': {
                'market_market_ioc': {
                    'quote_size': str(size) if side == 'buy' else None,
                    'base_size': str(size) if side == 'sell' else None
                }
            }
        }
        
        body_str = json.dumps(body)
        signature = self.generate_signature(timestamp, 'POST', path, body_str)
        
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        
        async with self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=body_str
        ) as response:
            result = await response.json()
            
        execution_time = (time.time() - start) * 1000
        if execution_time > 100:
            print(f"⚠️ Slow Coinbase execution: {execution_time:.2f}ms")
            
        return result
        
    async def get_order_book(self, symbol: str) -> Dict:
        """Get current order book"""
        path = f'/product_book'
        params = {'product_id': symbol, 'limit': 100}
        
        timestamp = str(int(time.time()))
        signature = self.generate_signature(timestamp, 'GET', path)
        
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp
        }
        
        async with self.session.get(
            f"{self.base_url}{path}",
            headers=headers,
            params=params
        ) as response:
            return await response.json()
            
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        path = '/accounts'
        timestamp = str(int(time.time()))
        signature = self.generate_signature(timestamp, 'GET', path)
        
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp
        }
        
        async with self.session.get(
            f"{self.base_url}{path}",
            headers=headers
        ) as response:
            accounts = await response.json()
            
        balances = {}
        for account in accounts.get('accounts', []):
            currency = account['currency']
            available = float(account['available_balance']['value'])
            if available > 0:
                balances[currency] = available
                
        return balances
        
    async def close(self):
        """Close connections"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
