#!/usr/bin/env python3
"""
Test script for new blockchain methods
"""

from blockchain.green_chain import GreenChain
import json

def test_new_methods():
    print("🧪 Testing New Blockchain Methods...")
    
    # Create a fresh blockchain instance
    chain = GreenChain(difficulty=4, storage_file="test_new_methods.json")
    
    # Add some test data
    test_data1 = {
        'seller_id': 1,
        'facility_name': 'Test Wind Farm',
        'hydrogen_weight_kg': 150.0,
        'tokens_generated': 150,
        'renewable_source': 'wind',
        'production_date': '2025-08-30',
        'location': 'Texas',
        'certification_type': 'premium',
        'price_per_token': 3.5
    }
    
    test_data2 = {
        'seller_id': 2,
        'facility_name': 'Test Solar Farm',
        'hydrogen_weight_kg': 200.0,
        'tokens_generated': 200,
        'renewable_source': 'solar',
        'production_date': '2025-08-30',
        'location': 'California',
        'certification_type': 'standard',
        'price_per_token': 2.8
    }
    
    try:
        # Issue certificates
        print("\n1. Issuing test certificates...")
        cert1_hash = chain.issue_certificate(test_data1)
        cert2_hash = chain.issue_certificate(test_data2)
        print(f"✅ Certificates issued: {cert1_hash[:16]}..., {cert2_hash[:16]}...")
        
        # Test transaction history
        print("\n2. Testing transaction history...")
        history = chain.get_transaction_history()
        print(f"   Total transactions: {len(history)}")
        for tx in history[:3]:  # Show first 3
            print(f"   - {tx['type']}: {tx.get('facility_name', 'N/A')} ({tx['timestamp']})")
        
        # Test analytics
        print("\n3. Testing blockchain analytics...")
        analytics = chain.get_blockchain_analytics()
        print(f"   Total blocks: {analytics['blockchain_summary']['total_blocks']}")
        print(f"   Total certificates: {analytics['blockchain_summary']['total_certificates']}")
        print(f"   Active certificates: {analytics['blockchain_summary']['active_certificates']}")
        print(f"   Retired certificates: {analytics['blockchain_summary']['retired_certificates']}")
        
        # Test user transactions
        print("\n4. Testing user transactions...")
        user1_tx = chain.get_user_transactions(1)
        user2_tx = chain.get_user_transactions(2)
        print(f"   User 1 transactions: {len(user1_tx)}")
        print(f"   User 2 transactions: {len(user2_tx)}")
        
        # Test recent activity
        print("\n5. Testing recent activity...")
        recent = chain.get_recent_activity(hours=24)
        print(f"   Recent activity (24h): {len(recent)} transactions")
        
        # Test search
        print("\n6. Testing search...")
        search_results = chain.search_transactions("wind")
        print(f"   Search 'wind': {len(search_results)} results")
        
        print("\n🎉 All new methods tested successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_methods()
