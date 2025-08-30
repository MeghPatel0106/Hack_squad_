#!/usr/bin/env python3
"""
Real-Time Blockchain Integration for Green Hydrogen Credits
Provides live blockchain events, WebSocket connections, and real-time data synchronization
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import queue
import logging

# Optional Web3 import for real blockchain integration
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("⚠️ Web3 not available - using local blockchain only")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTimeBlockchain:
    """Real-time blockchain integration with live event streaming"""
    
    def __init__(self, socketio: SocketIO, web3_provider: str = None):
        self.socketio = socketio
        self.event_queue = queue.Queue()
        self.subscribers = {}
        self.live_connections = {}
        self.blockchain_events = []
        
        # Web3 integration (optional - for real blockchain)
        if web3_provider and WEB3_AVAILABLE:
            try:
                self.web3 = Web3(Web3.HTTPProvider(web3_provider))
                self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                self.is_connected = self.web3.is_connected()
            except Exception as e:
                logger.warning(f"Web3 initialization failed: {e}")
                self.web3 = None
                self.is_connected = False
        else:
            self.web3 = None
            self.is_connected = False
        
        # Start event processing thread
        self.running = True
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()
        
        logger.info("🚀 Real-time blockchain system initialized")
    
    def _process_events(self):
        """Background thread for processing blockchain events"""
        while self.running:
            try:
                if not self.event_queue.empty():
                    event = self.event_queue.get(timeout=1)
                    self._broadcast_event(event)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing blockchain events: {e}")
    
    def _broadcast_event(self, event: Dict):
        """Broadcast blockchain event to all connected clients"""
        try:
            event_type = event.get('type')
            room = event.get('room', 'blockchain')
            
            # Emit to specific room or broadcast
            if room == 'broadcast':
                self.socketio.emit('blockchain_event', event, namespace='/blockchain')
            else:
                self.socketio.emit('blockchain_event', event, room=room, namespace='/blockchain')
            
            # Store event for history
            self.blockchain_events.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event': event
            })
            
            # Keep only last 1000 events
            if len(self.blockchain_events) > 1000:
                self.blockchain_events = self.blockchain_events[-1000:]
                
        except Exception as e:
            logger.error(f"Error broadcasting blockchain event: {e}")
    
    def emit_certificate_issued(self, certificate_data: Dict, blockchain_hash: str):
        """Emit real-time event when certificate is issued"""
        event = {
            'type': 'certificate_issued',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'certificate_id': certificate_data.get('certificate_id'),
                'blockchain_hash': blockchain_hash,
                'seller_id': certificate_data.get('seller_id'),
                'facility_name': certificate_data.get('facility_name'),
                'tokens_generated': certificate_data.get('tokens_generated'),
                'renewable_source': certificate_data.get('renewable_source'),
                'status': 'issued'
            },
            'room': 'blockchain'
        }
        
        self.event_queue.put(event)
        logger.info(f"🎫 Real-time certificate issued event: {blockchain_hash[:16]}...")
    
    def emit_certificate_verified(self, certificate_data: Dict, verified_by: str):
        """Emit real-time event when certificate is verified"""
        event = {
            'type': 'certificate_verified',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'certificate_id': certificate_data.get('certificate_id'),
                'blockchain_hash': certificate_data.get('blockchain_hash'),
                'verified_by': verified_by,
                'status': 'verified',
                'verified_at': datetime.now(timezone.utc).isoformat()
            },
            'room': 'blockchain'
        }
        
        self.event_queue.put(event)
        logger.info(f"✅ Real-time certificate verified event: {certificate_data.get('certificate_id')}")
    
    def emit_certificate_traded(self, trade_data: Dict):
        """Emit real-time event when certificate is traded"""
        event = {
            'type': 'certificate_traded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'certificate_id': trade_data.get('certificate_id'),
                'blockchain_hash': trade_data.get('blockchain_hash'),
                'seller_id': trade_data.get('seller_id'),
                'buyer_id': trade_data.get('buyer_id'),
                'tokens_amount': trade_data.get('tokens_amount'),
                'price_per_token': trade_data.get('price_per_token'),
                'total_amount': trade_data.get('total_amount'),
                'status': 'traded'
            },
            'room': 'blockchain'
        }
        
        self.event_queue.put(event)
        logger.info(f"💰 Real-time certificate traded event: {trade_data.get('certificate_id')}")
    
    def emit_certificate_retired(self, certificate_data: Dict):
        """Emit real-time event when certificate is retired"""
        event = {
            'type': 'certificate_retired',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'certificate_id': certificate_data.get('certificate_id'),
                'blockchain_hash': certificate_data.get('blockchain_hash'),
                'retired_at': datetime.now(timezone.utc).isoformat(),
                'status': 'retired'
            },
            'room': 'blockchain'
        }
        
        self.event_queue.put(event)
        logger.info(f"♻️ Real-time certificate retired event: {certificate_data.get('certificate_id')}")
    
    def emit_blockchain_update(self, update_data: Dict):
        """Emit general blockchain update"""
        event = {
            'type': 'blockchain_update',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': update_data,
            'room': 'broadcast'
        }
        
        self.event_queue.put(event)
        logger.info(f"📊 Real-time blockchain update: {update_data.get('type', 'unknown')}")
    
    def get_live_statistics(self) -> Dict:
        """Get real-time blockchain statistics"""
        return {
            'total_events': len(self.blockchain_events),
            'active_connections': len(self.live_connections),
            'last_event': self.blockchain_events[-1] if self.blockchain_events else None,
            'web3_connected': self.is_connected,
            'event_types': self._get_event_type_counts()
        }
    
    def _get_event_type_counts(self) -> Dict:
        """Count events by type"""
        counts = {}
        for event_record in self.blockchain_events:
            event_type = event_record['event'].get('type')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Dict]:
        """Get blockchain event history"""
        events = self.blockchain_events
        
        if event_type:
            events = [e for e in events if e['event'].get('type') == event_type]
        
        return events[-limit:] if events else []
    
    def subscribe_to_events(self, user_id: str, event_types: List[str] = None):
        """Subscribe user to specific blockchain events"""
        if event_types is None:
            event_types = ['all']
        
        self.subscribers[user_id] = event_types
        logger.info(f"👤 User {user_id} subscribed to events: {event_types}")
    
    def unsubscribe_from_events(self, user_id: str):
        """Unsubscribe user from blockchain events"""
        if user_id in self.subscribers:
            del self.subscribers[user_id]
            logger.info(f"👤 User {user_id} unsubscribed from events")
    
    def connect_user(self, user_id: str, session_id: str):
        """Connect user to real-time blockchain"""
        self.live_connections[user_id] = {
            'session_id': session_id,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"🔌 User {user_id} connected to real-time blockchain")
    
    def disconnect_user(self, user_id: str):
        """Disconnect user from real-time blockchain"""
        if user_id in self.live_connections:
            del self.live_connections[user_id]
            logger.info(f"🔌 User {user_id} disconnected from real-time blockchain")
    
    def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        if user_id in self.live_connections:
            self.live_connections[user_id]['last_activity'] = datetime.now(timezone.utc).isoformat()
    
    def cleanup_inactive_connections(self, max_inactive_minutes: int = 30):
        """Clean up inactive connections"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_inactive_minutes * 60)
        
        inactive_users = []
        for user_id, connection in self.live_connections.items():
            last_activity = datetime.fromisoformat(connection['last_activity']).timestamp()
            if last_activity < cutoff_time:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            self.disconnect_user(user_id)
        
        if inactive_users:
            logger.info(f"🧹 Cleaned up {len(inactive_users)} inactive connections")
    
    def stop(self):
        """Stop the real-time blockchain system"""
        self.running = False
        if self.event_thread.is_alive():
            self.event_thread.join(timeout=5)
        logger.info("🛑 Real-time blockchain system stopped")


class BlockchainEventManager:
    """Manages blockchain event subscriptions and routing"""
    
    def __init__(self, realtime_chain: RealTimeBlockchain):
        self.realtime_chain = realtime_chain
        self.event_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler('certificate_issued', self._handle_certificate_issued)
        self.register_handler('certificate_verified', self._handle_certificate_verified)
        self.register_handler('certificate_traded', self._handle_certificate_traded)
        self.register_handler('certificate_retired', self._handle_certificate_retired)
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register custom event handler"""
        self.event_handlers[event_type] = handler
        logger.info(f"📝 Registered handler for event type: {event_type}")
    
    def handle_event(self, event: Dict):
        """Route event to appropriate handler"""
        event_type = event.get('type')
        handler = self.event_handlers.get(event_type)
        
        if handler:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        else:
            logger.warning(f"No handler registered for event type: {event_type}")
    
    def _handle_certificate_issued(self, event: Dict):
        """Handle certificate issued events"""
        logger.info(f"🎫 Processing certificate issued: {event['data'].get('certificate_id')}")
        # Add custom logic here
    
    def _handle_certificate_verified(self, event: Dict):
        """Handle certificate verified events"""
        logger.info(f"✅ Processing certificate verified: {event['data'].get('certificate_id')}")
        # Add custom logic here
    
    def _handle_certificate_traded(self, event: Dict):
        """Handle certificate traded events"""
        logger.info(f"💰 Processing certificate traded: {event['data'].get('certificate_id')}")
        # Add custom logic here
    
    def _handle_certificate_retired(self, event: Dict):
        """Handle certificate retired events"""
        logger.info(f"♻️ Processing certificate retired: {event['data'].get('certificate_id')}")
        # Add custom logic here


# Global instances
realtime_blockchain = None
event_manager = None


def init_realtime_blockchain(socketio: SocketIO, web3_provider: str = None):
    """Initialize global real-time blockchain instances"""
    global realtime_blockchain, event_manager
    
    realtime_blockchain = RealTimeBlockchain(socketio, web3_provider)
    event_manager = BlockchainEventManager(realtime_blockchain)
    
    logger.info("🌐 Real-time blockchain system initialized globally")
    return realtime_blockchain, event_manager


def get_realtime_blockchain() -> RealTimeBlockchain:
    """Get global real-time blockchain instance"""
    return realtime_blockchain


def get_event_manager() -> BlockchainEventManager:
    """Get global event manager instance"""
    return event_manager


if __name__ == "__main__":
    # Test the real-time blockchain system
    print("🧪 Testing Real-Time Blockchain System...")
    
    # Mock SocketIO for testing
    class MockSocketIO:
        def emit(self, event, data, room=None, namespace=None):
            print(f"📡 Emitted: {event} to {room or 'broadcast'}")
    
    mock_socketio = MockSocketIO()
    
    # Initialize system
    chain, manager = init_realtime_blockchain(mock_socketio)
    
    # Test events
    test_cert = {
        'certificate_id': 'test-123',
        'seller_id': 1,
        'facility_name': 'Test Farm',
        'tokens_generated': 100,
        'renewable_source': 'solar'
    }
    
    chain.emit_certificate_issued(test_cert, 'test-hash-123')
    chain.emit_certificate_verified(test_cert, 'authority1')
    
    # Wait for events to process
    time.sleep(2)
    
    # Show statistics
    stats = chain.get_live_statistics()
    print(f"📊 Live Statistics: {stats}")
    
    # Cleanup
    chain.stop()
    print("✅ Real-time blockchain test completed!")
