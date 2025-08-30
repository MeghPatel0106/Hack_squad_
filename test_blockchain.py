#!/usr/bin/env python3
"""
Test script for the Green Hydrogen Credit Blockchain Simulator
"""

from blockchain.green_chain import GreenChain
import json

def test_blockchain():
    print("🧪 Testing Enhanced Blockchain Simulator...")
    
    # Create a new blockchain instance
    chain = GreenChain(difficulty=4, storage_file="test_blockchain.json")
    
    # Test certificate issuance
    test_data = {
        'seller_id': 2,
        'facility_name': 'Test Wind Farm',
        'hydrogen_weight_kg': 200.0,
        'tokens_generated': 200,
        'renewable_source': 'wind',
        'production_date': '2025-08-30',
        'location': 'Texas',
        'certification_type': 'premium',
        'price_per_token': 4.2
    }
    
    try:
        # Issue certificate
        print("\n1. Issuing certificate...")
        cert_hash = chain.issue_certificate(test_data)
        print(f"✅ Certificate issued with hash: {cert_hash[:16]}...")
        
        # Check blockchain state
        print("\n2. Checking blockchain state...")
        chain_info = chain.get_chain_info()
        print(f"   Total blocks: {chain_info['total_blocks']}")
        print(f"   Total certificates: {chain_info['total_certificates']}")
        print(f"   Active certificates: {chain_info['active_certificates']}")
        
        # List all certificates
        print("\n3. All certificates:")
        for cert_id, cert_info in chain.certificates.items():
            print(f"   - {cert_id}: {cert_info['data']['facility_name']} (Status: {cert_info['status']})")
        
        # Verify certificate
        print("\n4. Verifying certificate...")
        is_valid, cert_data = chain.verify_certificate(cert_hash)
        print(f"   Certificate valid: {is_valid}")
        if is_valid:
            print(f"   Facility: {cert_data['facility_name']}")
            print(f"   Tokens: {cert_data['tokens_generated']}")
        
        # Test retirement
        print("\n5. Testing certificate retirement...")
        retired = chain.retire_certificate(cert_hash)
        print(f"   Retirement successful: {retired}")
        
        # Verify after retirement
        print("\n6. Verifying after retirement...")
        is_valid_after, _ = chain.verify_certificate(cert_hash)
        print(f"   Certificate valid after retirement: {is_valid_after}")
        
        # Test double retirement (should fail)
        print("\n7. Testing double retirement...")
        double_retire = chain.retire_certificate(cert_hash)
        print(f"   Double retirement attempt: {double_retire}")
        
        # Final state
        print("\n8. Final blockchain state...")
        final_info = chain.get_chain_info()
        print(f"   Total blocks: {final_info['total_blocks']}")
        print(f"   Total certificates: {final_info['total_certificates']}")
        print(f"   Retired certificates: {final_info['retired_certificates']}")
        
        print("\n🎉 All tests passed successfully!")
        
        # Check if JSON file was created
        import os
        if os.path.exists("test_blockchain.json"):
            print(f"💾 Blockchain data saved to: test_blockchain.json")
            
            # Show file size
            size = os.path.getsize("test_blockchain.json")
            print(f"   File size: {size} bytes")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blockchain()
