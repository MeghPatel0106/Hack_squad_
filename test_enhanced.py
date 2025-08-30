#!/usr/bin/env python3
"""
Test script for enhanced blockchain methods
"""

from blockchain.green_chain import GreenChain

def test_enhanced_blockchain():
    print("🧪 Testing Enhanced Blockchain Methods...")
    
    # Create a fresh blockchain instance
    chain = GreenChain(difficulty=4, storage_file="test_enhanced.json")
    
    # Add test data
    test_data = {
        'seller_id': 1,
        'facility_name': 'Test Enhanced Farm',
        'hydrogen_weight_kg': 100.0,
        'tokens_generated': 100,
        'renewable_source': 'solar',
        'production_date': '2025-08-30',
        'location': 'Test Location',
        'certification_type': 'standard',
        'price_per_token': 2.5
    }
    
    try:
        # Issue certificate
        print("\n1. Issuing test certificate...")
        cert_hash = chain.issue_certificate(test_data)
        print(f"✅ Certificate issued: {cert_hash[:16]}...")
        
        # Test transaction history
        print("\n2. Testing transaction history...")
        history = chain.get_transaction_history()
        print(f"   Total transactions: {len(history)}")
        
        # Test analytics
        print("\n3. Testing blockchain analytics...")
        analytics = chain.get_blockchain_analytics()
        print(f"   Total blocks: {analytics['blockchain_summary']['total_blocks']}")
        print(f"   Total certificates: {analytics['blockchain_summary']['total_certificates']}")
        
        # Test user transactions
        print("\n4. Testing user transactions...")
        user_tx = chain.get_user_transactions(1)
        print(f"   User 1 transactions: {len(user_tx)}")
        
        # Test recent activity
        print("\n5. Testing recent activity...")
        recent = chain.get_recent_activity(hours=24)
        print(f"   Recent activity (24h): {len(recent)} transactions")
        
        # Test search
        print("\n6. Testing search...")
        search_results = chain.search_transactions("enhanced")
        print(f"   Search 'enhanced': {len(search_results)} results")
        
        print("\n🎉 All enhanced methods tested successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_blockchain()
