"""
License Key Generator (Admin Only)
Generate license keys untuk customer
"""
import random
import string
import hashlib
from datetime import datetime

def generate_license_key(prefix='JDWL'):
    """
    Generate unique license key
    Format: JDWL-XXXX-YYYY-ZZZZ
    """
    def random_segment(length=4):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    # Generate 3 random segments
    seg1 = random_segment(4)
    seg2 = random_segment(4)
    seg3 = random_segment(4)
    
    # Create license key
    license_key = f"{prefix}-{seg1}-{seg2}-{seg3}"
    
    return license_key

def generate_bulk_licenses(count=1, prefix='JDWL'):
    """
    Generate multiple license keys
    """
    licenses = []
    for _ in range(count):
        key = generate_license_key(prefix)
        licenses.append({
            'License Key': key,
            'Email': '',
            'HWID': '',
            'Status': 'pending',
            'Activated Date': '',
            'Expiry Date': '',
            'Notes': 'Belum aktivasi'
        })
    return licenses

def generate_for_customer(email, count=1):
    """
    Generate license for specific customer with email
    """
    licenses = []
    for _ in range(count):
        key = generate_license_key()
        licenses.append({
            'License Key': key,
            'Email': email,
            'HWID': '',
            'Status': 'pending',
            'Activated Date': '',
            'Expiry Date': '',
            'Notes': f'Generated for {email} on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        })
    return licenses

if __name__ == '__main__':
    print("=== License Key Generator ===\n")
    print("1. Generate Single License")
    print("2. Generate Bulk Licenses")
    print("3. Generate for Customer (with email)\n")
    
    choice = input("Pilih (1/2/3): ").strip()
    
    if choice == '1':
        key = generate_license_key()
        print(f"\nGenerated License Key:\n{key}")
        print("\nCopy ke Google Sheet:")
        print(f"{key}\t\t\tpending\t\t\tBelum aktivasi")
    
    elif choice == '2':
        count = int(input("Berapa banyak lisensi? "))
        licenses = generate_bulk_licenses(count)
        print(f"\n{count} License Keys Generated:\n")
        for i, lic in enumerate(licenses, 1):
            print(f"{i}. {lic['License Key']}")
        
        print("\n\nCopy ke Google Sheet (tab-separated):")
        for lic in licenses:
            print(f"{lic['License Key']}\t\t\tpending\t\t\tBelum aktivasi")
    
    elif choice == '3':
        email = input("Email customer: ").strip()
        count = int(input("Berapa banyak lisensi? "))
        licenses = generate_for_customer(email, count)
        
        print(f"\n{count} License Keys Generated for {email}:\n")
        for i, lic in enumerate(licenses, 1):
            print(f"{i}. {lic['License Key']}")
        
        print("\n\nCopy ke Google Sheet (tab-separated):")
        for lic in licenses:
            print(f"{lic['License Key']}\t{lic['Email']}\t\tpending\t\t\t{lic['Notes']}")
