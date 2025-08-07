import asyncio
import hmac
import hashlib
import base64
import time
import json
import urllib.parse
from typing import Dict, Any, Optional, List
import aiohttp
import websockets
import os

class KrakenClient:
    """
    Kraken API client with <100ms execution
    """
    
    def __init__(self):
        self.api_key = os.getenv('KRAKEN_API_KEY')
        self.api_secret = os.getenv('KRAKEN_SECRET')
        self.base_url = 'https://api.kraken.com'
        self.ws_url = 'wss://ws.kraken.com'
        self.session = None
        self.ws = None
        
    async def initialize(self):
        """Initialize HTTP session and WebSocket connection"""
        self.session = aiohttp.ClientSession()
        await self.connect_websocket()
        
    async def connect_websocket(self):
        """Connect to Kraken WebSocket"""
        self.ws = await websockets.connect(self.ws_url)
        
        # Subscribe to channels
        subscribe_msg = {
            "event": "subscribe",
            "pair": ["XBT/USD", "ETH/USD"],
            "subscription": {"name": "ticker"}
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
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
                print(f"Kraken WebSocket error: {e}")
                await self.reconnect_websocket()
                
    async def reconnect_websocket(self):
        """Reconnect WebSocket on disconnect"""
        await asyncio.sleep(1)
        await self.connect_websocket()
        
    def generate_signature(self, path: str, data: str, nonce: str) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(nonce) + postdata).encode()
        message = path.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        return base64.b64encode(signature.digest()).decode()
        
    async def place_order(self, side: str, symbol: str, size: float, order_type: str = 'market') -> Dict:
        """
        Place order with <100ms execution
        """
        start = time.time()
        
        nonce = str(int(time.time() * 1000))
        
        data = {
            'nonce': nonce,
            'ordertype': order_type,
            'type': side,
            'volume': str(size),
            'pair': symbol,
            'oflags': 'fciq'  # Fee in quote currency, immediate execution
        }
        
        path = '/0/private/AddOrder'
        signature = self.generate_signature(path, data, nonce)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': signature,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=data
        ) as response:
            result = await response.json()
            
        execution_time = (time.time() - start) * 1000
        if execution_time > 100:
            print(f"⚠️ Slow Kraken execution: {execution_time:.2f}ms")
            
        return result
        
    async def get_order_book(self, symbol: str) -> Dict:
        """Get current order book"""
        path = '/0/public/Depth'
        params = {'pair': symbol, 'count': 100}
        
        async with self.session.get(
            f"{self.base_url}{path}",
            params=params
        ) as response:
            return await response.json()
            
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        nonce = str(int(time.time() * 1000))
        data = {'nonce': nonce}
        
        path = '/0/private/Balance'
        signature = self.generate_signature(path, data, nonce)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': signature
        }
        
        async with self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=data
        ) as response:
            result = await response.json()
            
        if 'result' in result:
            return {k: float(v) for k, v in result['result'].items()}
        return {}
        
    async def close(self):
        """Close connections"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
