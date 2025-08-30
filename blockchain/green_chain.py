#!/usr/bin/env python3
"""
Green Hydrogen Credit Blockchain Simulator
A simple, web-based blockchain simulation for managing Green Hydrogen Certificates
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid


class Block:
    """Represents a single block in the blockchain"""
    
    def __init__(self, index: int, timestamp: float, data: Dict, previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate the hash of the current block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary for serialization"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class GreenChain:
    """Simple Blockchain Simulator for Green Hydrogen Credit Certificates"""
    
    def __init__(self, difficulty: int = 4, storage_file: str = "blockchain_data.json"):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.storage_file = storage_file
        self.certificates: Dict[str, Dict] = {}  # certificate_id -> certificate_data
        self.retired_certificates: set = set()
        
        # Load existing blockchain or create new one
        self.load_blockchain()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        """Create the first block in the chain"""
        genesis_data = {
            'type': 'genesis',
            'message': 'Green Hydrogen Credit Blockchain Simulator - Genesis Block',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0',
            'description': 'This is a simple blockchain simulation for demonstration purposes'
        }
        
        genesis_block = Block(0, time.time(), genesis_data, "0")
        self.chain.append(genesis_block)
        print("🌱 Genesis block created for Green Hydrogen Credit Blockchain Simulator")
        self.save_blockchain()
    
    def load_blockchain(self) -> None:
        """Load blockchain data from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                # Load chain
                self.chain = []
                for block_data in data.get('chain', []):
                    block = Block(
                        index=block_data['index'],
                        timestamp=block_data['timestamp'],
                        data=block_data['data'],
                        previous_hash=block_data['previous_hash'],
                        nonce=block_data['nonce']
                    )
                    block.hash = block_data['hash']
                    self.chain.append(block)
                
                # Load certificates
                self.certificates = data.get('certificates', {})
                self.retired_certificates = set(data.get('retired_certificates', []))
                
                print(f"📂 Blockchain loaded from {self.storage_file}")
                print(f"   - {len(self.chain)} blocks loaded")
                print(f"   - {len(self.certificates)} certificates loaded")
                print(f"   - {len(self.retired_certificates)} retired certificates")
                
            else:
                print(f"📂 No existing blockchain found. Creating new one.")
                
        except Exception as e:
            print(f"⚠️  Error loading blockchain: {e}")
            print("   Creating new blockchain...")
            self.chain = []
            self.certificates = {}
            self.retired_certificates = set()
    
    def save_blockchain(self) -> None:
        """Save blockchain data to JSON file"""
        try:
            data = {
                'chain': [block.to_dict() for block in self.chain],
                'certificates': self.certificates,
                'retired_certificates': list(self.retired_certificates),
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_blocks': len(self.chain),
                'total_certificates': len(self.certificates),
                'retired_count': len(self.retired_certificates)
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"💾 Blockchain saved to {self.storage_file}")
            
        except Exception as e:
            print(f"❌ Error saving blockchain: {e}")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain"""
        return self.chain[-1] if self.chain else None
    
    def mine_block(self, data: Dict) -> Block:
        """Mine a new block with simple proof-of-work"""
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1 if previous_block else 0
        new_timestamp = time.time()
        new_block = Block(new_index, new_timestamp, data, previous_block.hash if previous_block else "0")
        
        # Simple proof of work (find hash starting with zeros)
        while not new_block.hash.startswith('0' * self.difficulty):
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()
        
        print(f"⛏️  Block {new_index} mined with hash: {new_block.hash[:16]}...")
        return new_block
    
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain after validation"""
        if self.is_valid_block(block):
            self.chain.append(block)
            print(f"✅ Block {block.index} added to chain")
            self.save_blockchain()  # Save after each block addition
            return True
        else:
            print(f"❌ Block {block.index} validation failed")
            return False
    
    def is_valid_block(self, block: Block) -> bool:
        """Validate a block before adding to chain"""
        if block.index == 0:  # Genesis block
            return True
        
        if block.index - 1 >= len(self.chain):
            return False
        
        previous_block = self.chain[block.index - 1]
        
        # Check if previous hash matches
        if block.previous_hash != previous_block.hash:
            return False
        
        # Check if hash is valid
        if block.hash != block.calculate_hash():
            return False
        
        # Check proof of work
        if not block.hash.startswith('0' * self.difficulty):
            return False
        
        return True
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if not self.is_valid_block(current_block):
                return False
        
        return True
    
    def issue_certificate(self, data: Dict) -> str:
        """
        Issue a new green hydrogen credit certificate
        
        Args:
            data: Dictionary containing certificate data
            
        Returns:
            str: Unique hash of the issued certificate
        """
        # Generate unique certificate ID
        certificate_id = str(uuid.uuid4())
        
        # Check if certificate ID already exists (prevent duplicates)
        if certificate_id in self.certificates:
            raise Exception("Certificate ID already exists - duplicate detected")
        
        # Prepare certificate data
        certificate_data = {
            'type': 'hydrogen_credit_certificate',
            'certificate_id': certificate_id,
            'seller_id': data.get('seller_id'),
            'facility_name': data.get('facility_name'),
            'hydrogen_weight_kg': data.get('hydrogen_weight_kg'),
            'tokens_generated': data.get('tokens_generated'),
            'renewable_source': data.get('renewable_source'),
            'production_date': data.get('production_date'),
            'location': data.get('location'),
            'certification_type': data.get('certification_type'),
            'price_per_token': data.get('price_per_token'),
            'status': 'issued',
            'issued_at': datetime.now(timezone.utc).isoformat(),
            'blockchain_version': '1.0'
        }
        
        # Mine new block with certificate
        new_block = self.mine_block(certificate_data)
        
        # Add to chain
        if self.add_block(new_block):
            # Store certificate data
            self.certificates[certificate_id] = {
                'hash': new_block.hash,
                'block_index': new_block.index,
                'data': certificate_data,
                'status': 'active'
            }
            
            print(f"🎫 Certificate issued: {certificate_id}")
            print(f"🔗 Blockchain hash: {new_block.hash}")
            print(f"📊 Block #{new_block.index} added to chain")
            
            return new_block.hash
        else:
            raise Exception("Failed to add certificate block to blockchain")
    
    def verify_certificate(self, certificate_hash: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify a certificate's validity on the blockchain
        
        Args:
            certificate_hash: Hash of the certificate to verify
            
        Returns:
            Tuple[bool, Optional[Dict]]: (is_valid, certificate_data)
        """
        # Find certificate by hash
        for cert_id, cert_info in self.certificates.items():
            if cert_info['hash'] == certificate_hash:
                # Check if certificate is retired
                if cert_id in self.retired_certificates:
                    return False, {'error': 'Certificate has been retired/used', 'status': 'retired'}
                
                # Verify block exists in chain
                if cert_info['block_index'] < len(self.chain):
                    block = self.chain[cert_info['block_index']]
                    if block.hash == certificate_hash:
                        return True, cert_info['data']
                
                return False, {'error': 'Certificate not found in blockchain'}
        
        return False, {'error': 'Certificate not found'}
    
    def verify_certificate_by_id(self, certificate_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify a certificate by its ID
        
        Args:
            certificate_id: ID of the certificate to verify
            
        Returns:
            Tuple[bool, Optional[Dict]]: (is_valid, certificate_data)
        """
        if certificate_id not in self.certificates:
            return False, {'error': 'Certificate ID not found'}
        
        cert_info = self.certificates[certificate_id]
        
        # Check if certificate is retired
        if certificate_id in self.retired_certificates:
            return False, {'error': 'Certificate has been retired/used', 'status': 'retired'}
        
        # Verify block exists in chain
        if cert_info['block_index'] < len(self.chain):
            block = self.chain[cert_info['block_index']]
            if block.hash == cert_info['hash']:
                return True, cert_info['data']
        
        return False, {'error': 'Certificate not found in blockchain'}
    
    def retire_certificate(self, certificate_hash: str) -> bool:
        """
        Mark a certificate as used/retired (prevent double counting)
        
        Args:
            certificate_hash: Hash of the certificate to retire
            
        Returns:
            bool: True if successfully retired, False otherwise
        """
        # Find certificate by hash
        for cert_id, cert_info in self.certificates.items():
            if cert_info['hash'] == certificate_hash:
                if cert_id in self.retired_certificates:
                    print(f"⚠️  Certificate {cert_id} already retired - cannot reuse")
                    return False
                
                # Mark as retired
                self.retired_certificates.add(cert_id)
                self.certificates[cert_id]['status'] = 'retired'
                
                # Create retirement record
                retirement_data = {
                    'type': 'certificate_retirement',
                    'certificate_id': cert_id,
                    'original_hash': certificate_hash,
                    'retired_at': datetime.now(timezone.utc).isoformat(),
                    'status': 'retired',
                    'reason': 'Certificate used for credit purchase'
                }
                
                # Add retirement block to chain
                retirement_block = self.mine_block(retirement_data)
                if self.add_block(retirement_block):
                    print(f"♻️  Certificate {cert_id} retired successfully")
                    print(f"🔗 Retirement hash: {retirement_block.hash}")
                    print(f"⚠️  Certificate cannot be reused (double counting prevention)")
                    return True
                else:
                    print(f"❌ Failed to add retirement block for {cert_id}")
                    return False
        
        print(f"❌ Certificate with hash {certificate_hash} not found")
        return False
    
    def get_certificate_status(self, certificate_hash: str) -> str:
        """Get the current status of a certificate"""
        for cert_id, cert_info in self.certificates.items():
            if cert_info['hash'] == certificate_hash:
                if cert_id in self.retired_certificates:
                    return 'retired'
                return 'active'
        return 'not_found'
    
    def get_certificate_by_hash(self, certificate_hash: str) -> Optional[Dict]:
        """Get certificate data by its blockchain hash"""
        for cert_id, cert_info in self.certificates.items():
            if cert_info['hash'] == certificate_hash:
                return {
                    'certificate_id': cert_id,
                    'hash': cert_info['hash'],
                    'data': cert_info['data'],
                    'status': 'retired' if cert_id in self.retired_certificates else 'active'
                }
        return None
    
    def get_chain(self) -> List[Dict]:
        """Get the full blockchain"""
        return [block.to_dict() for block in self.chain]
    
    def get_chain_info(self) -> Dict:
        """Get blockchain statistics and information"""
        return {
            'total_blocks': len(self.chain),
            'total_certificates': len(self.certificates),
            'retired_certificates': len(self.retired_certificates),
            'active_certificates': len(self.certificates) - len(self.retired_certificates),
            'difficulty': self.difficulty,
            'last_block_hash': self.get_latest_block().hash if self.chain else None,
            'chain_valid': self.is_chain_valid(),
            'storage_file': self.storage_file,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    
    def get_transaction_history(self, limit: int = 100) -> List[Dict]:
        """
        Get complete transaction history from blockchain
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction records with timestamps
        """
        transactions = []
        
        for block in self.chain:
            if block.data.get('type') == 'hydrogen_credit_certificate':
                transactions.append({
                    'type': 'certificate_issued',
                    'timestamp': block.data.get('issued_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'certificate_id': block.data.get('certificate_id'),
                    'seller_id': block.data.get('seller_id'),
                    'facility_name': block.data.get('facility_name'),
                    'hydrogen_weight_kg': block.data.get('hydrogen_weight_kg'),
                    'tokens_generated': block.data.get('tokens_generated'),
                    'renewable_source': block.data.get('renewable_source'),
                    'location': block.data.get('location'),
                    'certification_type': block.data.get('certification_type'),
                    'price_per_token': block.data.get('price_per_token'),
                    'status': 'issued'
                })
            
            elif block.data.get('type') == 'certificate_retirement':
                transactions.append({
                    'type': 'certificate_retired',
                    'timestamp': block.data.get('retired_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'certificate_id': block.data.get('certificate_id'),
                    'original_hash': block.data.get('original_hash'),
                    'reason': block.data.get('reason', 'Unknown'),
                    'status': 'retired'
                })
            
            elif block.data.get('type') == 'genesis':
                transactions.append({
                    'type': 'genesis_block',
                    'timestamp': block.timestamp,
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'message': block.data.get('message'),
                    'version': block.data.get('version'),
                    'status': 'created'
                })
        
        # Sort by timestamp (newest first)
        # Sort by timestamp (newest first) - handle mixed types
        def safe_timestamp_sort(tx):
            ts = tx['timestamp']
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            elif isinstance(ts, (int, float)):
                return ts
            else:
                return 0
        
        transactions.sort(key=safe_timestamp_sort, reverse=True)
        
        return transactions[:limit]
    
    def get_certificate_transactions(self, certificate_id: str) -> List[Dict]:
        """
        Get all transactions for a specific certificate
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            List of all transactions for this certificate
        """
        if certificate_id not in self.certificates:
            return []
        
        transactions = []
        cert_info = self.certificates[certificate_id]
        
        # Find issuance transaction
        for block in self.chain:
            if (block.data.get('type') == 'hydrogen_credit_certificate' and 
                block.data.get('certificate_id') == certificate_id):
                transactions.append({
                    'type': 'certificate_issued',
                    'timestamp': block.data.get('issued_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'facility_name': block.data.get('facility_name'),
                    'hydrogen_weight_kg': block.data.get('hydrogen_weight_kg'),
                    'tokens_generated': block.data.get('tokens_generated'),
                    'renewable_source': block.data.get('renewable_source'),
                    'location': block.data.get('location'),
                    'certification_type': block.data.get('certification_type'),
                    'price_per_token': block.data.get('price_per_token'),
                    'status': 'issued'
                })
                break
        
        # Find retirement transaction
        for block in self.chain:
            if (block.data.get('type') == 'certificate_retirement' and 
                block.data.get('certificate_id') == certificate_id):
                transactions.append({
                    'type': 'certificate_retired',
                    'timestamp': block.data.get('retired_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'reason': block.data.get('reason', 'Unknown'),
                    'status': 'retired'
                })
                break
        
        # Sort by timestamp
        def safe_timestamp_sort(tx):
            ts = tx['timestamp']
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            elif isinstance(ts, (int, float)):
                return ts
            else:
                return 0
        
        transactions.sort(key=safe_timestamp_sort)
        return transactions
    
    def get_user_transactions(self, user_id: int) -> List[Dict]:
        """
        Get all transactions for a specific user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of all transactions involving this user
        """
        transactions = []
        
        for block in self.chain:
            if block.data.get('type') == 'hydrogen_credit_certificate':
                if block.data.get('seller_id') == user_id:
                    transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': block.data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'certificate_id': block.data.get('certificate_id'),
                        'facility_name': block.data.get('facility_name'),
                        'hydrogen_weight_kg': block.data.get('hydrogen_weight_kg'),
                        'tokens_generated': block.data.get('tokens_generated'),
                        'renewable_source': block.data.get('renewable_source'),
                        'location': block.data.get('location'),
                        'certification_type': block.data.get('certification_type'),
                        'price_per_token': block.data.get('price_per_token'),
                        'role': 'seller',
                        'status': 'issued'
                    })
            
            elif block.data.get('type') == 'certificate_retirement':
                # Check if this retirement involves the user
                cert_id = block.data.get('certificate_id')
                if cert_id in self.certificates:
                    cert_info = self.certificates[cert_id]
                    if cert_info['data'].get('seller_id') == user_id:
                        transactions.append({
                            'type': 'certificate_retired',
                            'timestamp': block.data.get('retired_at', block.timestamp),
                            'block_index': block.index,
                            'block_hash': block.hash,
                            'certificate_id': cert_id,
                            'facility_name': cert_info['data'].get('facility_name'),
                            'tokens_generated': cert_info['data'].get('tokens_generated'),
                            'renewable_source': cert_info['data'].get('renewable_source'),
                            'role': 'seller',
                            'status': 'retired'
                        })
        
        # Sort by timestamp (newest first)
        def safe_timestamp_sort(tx):
            ts = tx['timestamp']
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            elif isinstance(ts, (int, float)):
                return ts
            else:
                return 0
        
        transactions.sort(key=safe_timestamp_sort, reverse=True)
        return transactions
    
    def get_blockchain_analytics(self) -> Dict:
        """
        Get comprehensive blockchain analytics and statistics
        
        Returns:
            Dictionary with detailed analytics
        """
        analytics = {
            'blockchain_summary': {
                'total_blocks': len(self.chain),
                'total_certificates': len(self.certificates),
                'active_certificates': len(self.certificates) - len(self.retired_certificates),
                'retired_certificates': len(self.retired_certificates),
                'chain_valid': self.is_chain_valid(),
                'difficulty': self.difficulty,
                'last_block_time': self.get_latest_block().timestamp if self.chain else None
            },
            'certificate_breakdown': {
                'by_source': {},
                'by_location': {},
                'by_certification_type': {},
                'by_status': {
                    'active': len(self.certificates) - len(self.retired_certificates),
                    'retired': len(self.retired_certificates)
                }
            },
            'token_economics': {
                'total_tokens_issued': 0,
                'total_tokens_retired': 0,
                'active_tokens': 0,
                'average_price_per_token': 0.0
            },
            'timeline': {
                'first_certificate': None,
                'latest_certificate': None,
                'total_days_active': 0
            }
        }
        
        # Calculate certificate breakdowns
        total_price = 0.0
        total_tokens = 0
        
        for cert_id, cert_info in self.certificates.items():
            data = cert_info['data']
            
            # Source breakdown
            source = data.get('renewable_source', 'unknown')
            analytics['certificate_breakdown']['by_source'][source] = \
                analytics['certificate_breakdown']['by_source'].get(source, 0) + 1
            
            # Location breakdown
            location = data.get('location', 'unknown')
            analytics['certificate_breakdown']['by_location'][location] = \
                analytics['certificate_breakdown']['by_location'].get(location, 0) + 1
            
            # Certification type breakdown
            cert_type = data.get('certification_type', 'unknown')
            analytics['certificate_breakdown']['by_certification_type'][cert_type] = \
                analytics['certificate_breakdown']['by_certification_type'].get(cert_type, 0) + 1
            
            # Token economics
            tokens = data.get('tokens_generated', 0)
            price = data.get('price_per_token', 0.0)
            
            total_tokens += tokens
            total_price += (tokens * price)
            
            if cert_id not in self.retired_certificates:
                analytics['token_economics']['active_tokens'] += tokens
            else:
                analytics['token_economics']['total_tokens_retired'] += tokens
        
        analytics['token_economics']['total_tokens_issued'] = total_tokens
        if total_tokens > 0:
            analytics['token_economics']['average_price_per_token'] = total_price / total_tokens
        
        # Timeline analysis
        if self.certificates:
            timestamps = []
            for cert_info in self.certificates.values():
                if 'issued_at' in cert_info['data']:
                    try:
                        timestamps.append(datetime.fromisoformat(cert_info['data']['issued_at']))
                    except:
                        pass
            
            if timestamps:
                timestamps.sort()
                analytics['timeline']['first_certificate'] = timestamps[0].isoformat()
                analytics['timeline']['latest_certificate'] = timestamps[-1].isoformat()
                
                if len(timestamps) > 1:
                    delta = timestamps[-1] - timestamps[0]
                    analytics['timeline']['total_days_active'] = delta.days
        
        return analytics
    
    def get_recent_activity(self, hours: int = 24) -> List[Dict]:
        """
        Get recent blockchain activity within specified hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent transactions
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent_transactions = []
        
        for block in self.chain:
            if block.timestamp >= cutoff_time:
                if block.data.get('type') == 'hydrogen_credit_certificate':
                    recent_transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': block.data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'facility_name': block.data.get('facility_name'),
                        'tokens_generated': block.data.get('tokens_generated'),
                        'renewable_source': block.data.get('renewable_source'),
                        'status': 'issued'
                    })
                elif block.data.get('type') == 'certificate_retirement':
                    recent_transactions.append({
                        'type': 'certificate_retired',
                        'timestamp': block.data.get('retired_at', block.timestamp),
                        'block_index': block.index,
                        'certificate_id': block.data.get('certificate_id'),
                        'status': 'retired'
                    })
        
        # Sort by timestamp (newest first)
        def safe_timestamp_sort(tx):
            ts = tx['timestamp']
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            elif isinstance(ts, (int, float)):
                return ts
            else:
                return 0
        
        recent_transactions.sort(key=safe_timestamp_sort, reverse=True)
        return recent_transactions
    
    def search_transactions(self, query: str) -> List[Dict]:
        """
        Search transactions by various criteria
        
        Args:
            query: Search query (facility name, location, source, etc.)
            
        Returns:
            List of matching transactions
        """
        query = query.lower()
        matching_transactions = []
        
        for block in self.chain:
            if block.data.get('type') == 'hydrogen_credit_certificate':
                data = block.data
                
                # Search in various fields
                if (query in data.get('facility_name', '').lower() or
                    query in data.get('location', '').lower() or
                    query in data.get('renewable_source', '').lower() or
                    query in data.get('certification_type', '').lower() or
                    query in str(data.get('certificate_id', '')).lower()):
                    
                    matching_transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'certificate_id': data.get('certificate_id'),
                        'facility_name': data.get('facility_name'),
                        'hydrogen_weight_kg': data.get('hydrogen_weight_kg'),
                        'tokens_generated': data.get('tokens_generated'),
                        'renewable_source': data.get('renewable_source'),
                        'location': data.get('location'),
                        'certification_type': data.get('certification_type'),
                        'price_per_token': data.get('price_per_token'),
                        'status': 'issued'
                    })
        
        # Sort by timestamp (newest first)
        def safe_timestamp_sort(tx):
            ts = tx['timestamp']
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            elif isinstance(ts, (int, float)):
                return ts
            else:
                return 0
        
        matching_transactions.sort(key=safe_timestamp_sort, reverse=True)
        return matching_transactions
    
    def get_certificate_transactions(self, certificate_id: str) -> List[Dict]:
        """
        Get all transactions for a specific certificate
        
        Args:
            certificate_id: ID of the certificate
            
        Returns:
            List of all transactions for this certificate
        """
        if certificate_id not in self.certificates:
            return []
        
        transactions = []
        cert_info = self.certificates[certificate_id]
        
        # Find issuance transaction
        for block in self.chain:
            if (block.data.get('type') == 'hydrogen_credit_certificate' and 
                block.data.get('certificate_id') == certificate_id):
                transactions.append({
                    'type': 'certificate_issued',
                    'timestamp': block.data.get('issued_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'facility_name': block.data.get('facility_name'),
                    'hydrogen_weight_kg': block.data.get('hydrogen_weight_kg'),
                    'tokens_generated': block.data.get('tokens_generated'),
                    'renewable_source': block.data.get('renewable_source'),
                    'location': block.data.get('location'),
                    'certification_type': block.data.get('certification_type'),
                    'price_per_token': block.data.get('price_per_token'),
                    'status': 'issued'
                })
                break
        
        # Find retirement transaction
        for block in self.chain:
            if (block.data.get('type') == 'certificate_retirement' and 
                block.data.get('certificate_id') == certificate_id):
                transactions.append({
                    'type': 'certificate_retired',
                    'timestamp': block.data.get('retired_at', block.timestamp),
                    'block_index': block.index,
                    'block_hash': block.hash,
                    'reason': block.data.get('reason', 'Unknown'),
                    'status': 'retired'
                })
                break
        
        # Sort by timestamp
        transactions.sort(key=lambda x: x['timestamp'])
        return transactions
    
    def get_user_transactions(self, user_id: int) -> List[Dict]:
        """
        Get all transactions for a specific user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of all transactions involving this user
        """
        transactions = []
        
        for block in self.chain:
            if block.data.get('type') == 'hydrogen_credit_certificate':
                if block.data.get('seller_id') == user_id:
                    transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': block.data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'certificate_id': block.data.get('certificate_id'),
                        'facility_name': block.data.get('facility_name'),
                        'hydrogen_weight_kg': block.data.get('hydrogen_weight_kg'),
                        'tokens_generated': block.data.get('tokens_generated'),
                        'renewable_source': block.data.get('renewable_source'),
                        'location': block.data.get('location'),
                        'certification_type': block.data.get('certification_type'),
                        'price_per_token': block.data.get('price_per_token'),
                        'role': 'seller',
                        'status': 'issued'
                    })
            
            elif block.data.get('type') == 'certificate_retirement':
                # Check if this retirement involves the user
                cert_id = block.data.get('certificate_id')
                if cert_id in self.certificates:
                    cert_info = self.certificates[cert_id]
                    if cert_info['data'].get('seller_id') == user_id:
                        transactions.append({
                            'type': 'certificate_retired',
                            'timestamp': block.data.get('retired_at', block.timestamp),
                            'block_index': block.index,
                            'block_hash': block.hash,
                            'certificate_id': cert_id,
                            'facility_name': cert_info['data'].get('facility_name'),
                            'tokens_generated': cert_info['data'].get('tokens_generated'),
                            'renewable_source': cert_info['data'].get('renewable_source'),
                            'role': 'seller',
                            'status': 'retired'
                        })
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        return transactions
    
    def get_blockchain_analytics(self) -> Dict:
        """
        Get comprehensive blockchain analytics and statistics
        
        Returns:
            Dictionary with detailed analytics
        """
        analytics = {
            'blockchain_summary': {
                'total_blocks': len(self.chain),
                'total_certificates': len(self.certificates),
                'active_certificates': len(self.certificates) - len(self.retired_certificates),
                'retired_certificates': len(self.retired_certificates),
                'chain_valid': self.is_chain_valid(),
                'difficulty': self.difficulty,
                'last_block_time': self.get_latest_block().timestamp if self.chain else None
            },
            'certificate_breakdown': {
                'by_source': {},
                'by_location': {},
                'by_certification_type': {},
                'by_status': {
                    'active': len(self.certificates) - len(self.retired_certificates),
                    'retired': len(self.retired_certificates)
                }
            },
            'token_economics': {
                'total_tokens_issued': 0,
                'total_tokens_retired': 0,
                'active_tokens': 0,
                'average_price_per_token': 0.0
            },
            'timeline': {
                'first_certificate': None,
                'latest_certificate': None,
                'total_days_active': 0
            }
        }
        
        # Calculate certificate breakdowns
        total_price = 0.0
        total_tokens = 0
        
        for cert_id, cert_info in self.certificates.items():
            data = cert_info['data']
            
            # Source breakdown
            source = data.get('renewable_source', 'unknown')
            analytics['certificate_breakdown']['by_source'][source] = \
                analytics['certificate_breakdown']['by_source'].get(source, 0) + 1
            
            # Location breakdown
            location = data.get('location', 'unknown')
            analytics['certificate_breakdown']['by_location'][location] = \
                analytics['certificate_breakdown']['by_location'].get(location, 0) + 1
            
            # Certification type breakdown
            cert_type = data.get('certification_type', 'unknown')
            analytics['certificate_breakdown']['by_certification_type'][cert_type] = \
                analytics['certificate_breakdown']['by_certification_type'].get(cert_type, 0) + 1
            
            # Token economics
            tokens = data.get('tokens_generated', 0)
            price = data.get('price_per_token', 0.0)
            
            total_tokens += tokens
            total_price += (tokens * price)
            
            if cert_id not in self.retired_certificates:
                analytics['token_economics']['active_tokens'] += tokens
            else:
                analytics['token_economics']['total_tokens_retired'] += tokens
        
        analytics['token_economics']['total_tokens_issued'] = total_tokens
        if total_tokens > 0:
            analytics['token_economics']['average_price_per_token'] = total_price / total_tokens
        
        # Timeline analysis
        if self.certificates:
            timestamps = []
            for cert_info in self.certificates.values():
                if 'issued_at' in cert_info['data']:
                    try:
                        timestamps.append(datetime.fromisoformat(cert_info['data']['issued_at']))
                    except:
                        pass
            
            if timestamps:
                timestamps.sort()
                analytics['timeline']['first_certificate'] = timestamps[0].isoformat()
                analytics['timeline']['latest_certificate'] = timestamps[-1].isoformat()
                
                if len(timestamps) > 1:
                    delta = timestamps[-1] - timestamps[0]
                    analytics['timeline']['total_days_active'] = delta.days
        
        return analytics
    
    def get_recent_activity(self, hours: int = 24) -> List[Dict]:
        """
        Get recent blockchain activity within specified hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent transactions
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent_transactions = []
        
        for block in self.chain:
            if block.timestamp >= cutoff_time:
                if block.data.get('type') == 'hydrogen_credit_certificate':
                    recent_transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': block.data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'facility_name': block.data.get('facility_name'),
                        'tokens_generated': block.data.get('tokens_generated'),
                        'renewable_source': block.data.get('renewable_source'),
                        'status': 'issued'
                    })
                elif block.data.get('type') == 'certificate_retirement':
                    recent_transactions.append({
                        'type': 'certificate_retired',
                        'timestamp': block.data.get('retired_at', block.timestamp),
                        'block_index': block.index,
                        'certificate_id': block.data.get('certificate_id'),
                        'status': 'retired'
                    })
        
        # Sort by timestamp (newest first)
        recent_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        return recent_transactions
    
    def search_transactions(self, query: str) -> List[Dict]:
        """
        Search transactions by various criteria
        
        Args:
            query: Search query (facility name, location, source, etc.)
            
        Returns:
            List of matching transactions
        """
        query = query.lower()
        matching_transactions = []
        
        for block in self.chain:
            if block.data.get('type') == 'hydrogen_credit_certificate':
                data = block.data
                
                # Search in various fields
                if (query in data.get('facility_name', '').lower() or
                    query in data.get('location', '').lower() or
                    query in data.get('renewable_source', '').lower() or
                    query in data.get('certification_type', '').lower() or
                    query in str(data.get('certificate_id', '')).lower()):
                    
                    matching_transactions.append({
                        'type': 'certificate_issued',
                        'timestamp': data.get('issued_at', block.timestamp),
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'certificate_id': data.get('certificate_id'),
                        'facility_name': data.get('facility_name'),
                        'hydrogen_weight_kg': data.get('hydrogen_weight_kg'),
                        'tokens_generated': data.get('tokens_generated'),
                        'renewable_source': data.get('renewable_source'),
                        'location': data.get('location'),
                        'certification_type': data.get('certification_type'),
                        'price_per_token': data.get('price_per_token'),
                        'status': 'issued'
                    })
        
        # Sort by timestamp (newest first)
        matching_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        return matching_transactions
    
    def get_certificate_history(self, certificate_id: str) -> List[Dict]:
        """Get the complete history of a certificate"""
        history = []
        
        if certificate_id not in self.certificates:
            return history
        
        cert_info = self.certificates[certificate_id]
        
        # Add issuance record
        history.append({
            'action': 'issued',
            'timestamp': cert_info['data']['issued_at'],
            'hash': cert_info['hash'],
            'block_index': cert_info['block_index']
        })
        
        # Check if retired
        if certificate_id in self.retired_certificates:
            # Find retirement block
            for block in self.chain:
                if (block.data.get('type') == 'certificate_retirement' and 
                    block.data.get('certificate_id') == certificate_id):
                    history.append({
                        'action': 'retired',
                        'timestamp': block.data['retired_at'],
                        'hash': block.hash,
                        'block_index': block.index,
                        'reason': block.data.get('reason', 'Unknown')
                    })
                    break
        
        return history
    
    def export_chain(self) -> List[Dict]:
        """Export the entire blockchain for backup/verification"""
        return [block.to_dict() for block in self.chain]
    
    def import_chain(self, chain_data: List[Dict]) -> bool:
        """Import a blockchain from backup data"""
        try:
            self.chain = []
            for block_data in chain_data:
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    data=block_data['data'],
                    previous_hash=block_data['previous_hash'],
                    nonce=block_data['nonce']
                )
                block.hash = block_data['hash']
                self.chain.append(block)
            
            # Rebuild certificates and retired sets
            self.certificates = {}
            self.retired_certificates = set()
            
            for block in self.chain:
                if block.data.get('type') == 'hydrogen_credit_certificate':
                    cert_id = block.data['certificate_id']
                    self.certificates[cert_id] = {
                        'hash': block.hash,
                        'block_index': block.index,
                        'data': block.data,
                        'status': 'active'
                    }
                elif block.data.get('type') == 'certificate_retirement':
                    self.retired_certificates.add(block.data['certificate_id'])
                    if block.data['certificate_id'] in self.certificates:
                        self.certificates[block.data['certificate_id']]['status'] = 'retired'
            
            print(f"✅ Blockchain imported successfully with {len(self.chain)} blocks")
            self.save_blockchain()
            return True
            
        except Exception as e:
            print(f"❌ Failed to import blockchain: {e}")
            return False
    
    def reset_blockchain(self) -> None:
        """Reset blockchain to initial state (for testing)"""
        self.chain = []
        self.certificates = {}
        self.retired_certificates = set()
        self.create_genesis_block()
        print("🔄 Blockchain reset to initial state")


# Global blockchain instance
green_chain = GreenChain(difficulty=4, storage_file="blockchain_data.json")


def get_blockchain() -> GreenChain:
    """Get the global blockchain instance"""
    return green_chain


if __name__ == "__main__":
    # Test the blockchain simulator
    print("🧪 Testing Green Hydrogen Credit Blockchain Simulator...")
    
    # Test certificate issuance
    test_data = {
        'seller_id': 1,
        'facility_name': 'Test Solar Farm',
        'hydrogen_weight_kg': 100.0,
        'tokens_generated': 100,
        'renewable_source': 'solar',
        'production_date': '2025-08-30',
        'location': 'California',
        'certification_type': 'standard',
        'price_per_token': 2.5
    }
    
    try:
        # Issue certificate
        cert_hash = green_chain.issue_certificate(test_data)
        print(f"\n🎫 Test certificate issued with hash: {cert_hash[:16]}...")
        
        # Verify certificate
        is_valid, cert_data = green_chain.issue_certificate(test_data)
        print(f"✅ Certificate verification: {is_valid}")
        
        # Get chain info
        chain_info = green_chain.get_chain_info()
        print(f"📊 Chain info: {chain_info}")
        
        # Test retirement
        retired = green_chain.retire_certificate(cert_hash)
        print(f"♻️  Certificate retirement: {retired}")
        
        # Final verification (should fail - certificate retired)
        is_valid_after, _ = green_chain.verify_certificate(cert_hash)
        print(f"✅ Certificate valid after retirement: {is_valid_after}")
        
        # Test double retirement (should fail)
        double_retire = green_chain.retire_certificate(cert_hash)
        print(f"🔄 Double retirement attempt: {double_retire}")
        
        print("\n🎉 Blockchain simulator test completed successfully!")
        print(f"💾 Data saved to: {green_chain.storage_file}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

