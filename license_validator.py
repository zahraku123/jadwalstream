"""
License Validator - Google Apps Script Based
Simple license system with hardware locking via Apps Script API
"""
import os
import json
import requests
from datetime import datetime, timedelta
from hwid import get_hwid, get_system_info

# Apps Script Configuration
APPS_SCRIPT_URL = ''  # Will be set from config file
CONFIG_FILE = 'license_config.json'
CACHE_FILE = 'license_cache.json'  # Local cache untuk offline mode

class LicenseValidator:
    def __init__(self):
        self.hwid = get_hwid()
        self.apps_script_url = self._load_config()
        self.cache = self._load_cache()
        
    def _load_config(self):
        """Load Apps Script URL from config"""
        global APPS_SCRIPT_URL
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    APPS_SCRIPT_URL = config.get('apps_script_url', '')
                    return APPS_SCRIPT_URL
            except:
                pass
        return APPS_SCRIPT_URL
    
    def _load_cache(self):
        """Load cached license data"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self, data):
        """Save license data to cache"""
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _call_api(self, action, params):
        """Call Apps Script API"""
        if not self.apps_script_url:
            return None, "Apps Script URL not configured"
        
        try:
            payload = {
                'action': action,
                **params
            }
            
            response = requests.post(
                self.apps_script_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"API Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return None, "Request timeout. Check internet connection."
        except requests.exceptions.RequestException as e:
            return None, f"Connection error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def activate_license(self, license_key):
        """
        Activate license with current hardware ID
        Returns: (success: bool, message: str)
        """
        result, error = self._call_api('activate', {
            'license_key': license_key,
            'hwid': self.hwid
        })
        
        if error:
            return False, f"Tidak dapat terhubung ke server lisensi: {error}"
        
        if result and result.get('success'):
            # Cache license data
            cache_data = {
                'license_key': result.get('license_key'),
                'hwid': result.get('hwid'),
                'status': result.get('status'),
                'activated_date': result.get('activated_date'),
                'expiry_date': result.get('expiry_date'),
                'last_verified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._save_cache(cache_data)
            
            expiry = result.get('expiry_date', 'N/A')
            return True, f"Lisensi berhasil diaktifkan! Berlaku hingga {expiry}"
        else:
            message = result.get('message', 'Aktivasi gagal') if result else 'Server error'
            return False, message
    
    def verify_license(self, force_online=False):
        """
        Verify license is valid
        Returns: (valid: bool, message: str, days_remaining: int)
        """
        # Check cache first (offline mode)
        if not force_online and self.cache:
            return self._verify_from_cache()
        
        # Online verification
        result, error = self._call_api('validate', {'hwid': self.hwid})
        
        if error:
            # Fallback to cache if can't connect
            if self.cache:
                return self._verify_from_cache()
            return False, f"Tidak dapat terhubung ke server: {error}", 0
        
        if result and result.get('success'):
            # Update cache
            cache_data = {
                'license_key': result.get('license_key'),
                'hwid': result.get('hwid'),
                'status': result.get('status'),
                'expiry_date': result.get('expiry_date'),
                'last_verified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._save_cache(cache_data)
            
            days = result.get('days_remaining', 0)
            return True, f"Lisensi valid. {days} hari tersisa.", days
        else:
            # License invalid or expired
            status = result.get('status') if result else None
            if status == 'revoked':
                self.cache = {}
                self._save_cache({})
                return False, "Lisensi Anda telah dicabut.", 0
            elif status == 'expired':
                return False, "Lisensi Anda telah kadaluarsa. Silakan perpanjang.", 0
            else:
                message = result.get('message', 'Tidak ada lisensi aktif') if result else 'Server error'
                return False, message, 0
    
    def _verify_from_cache(self):
        """Verify license from local cache (offline mode)"""
        if not self.cache:
            return False, "Tidak ada lisensi yang tersimpan.", 0
        
        # Check HWID match
        if self.cache.get('hwid') != self.hwid:
            return False, "Hardware ID tidak cocok. Lisensi tidak valid.", 0
        
        # Check status
        if self.cache.get('status') != 'active':
            return False, "Lisensi tidak aktif.", 0
        
        # Check expiry
        try:
            expiry_str = self.cache.get('expiry_date', '')
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            days_remaining = (expiry_date - datetime.now()).days
            
            if days_remaining < 0:
                return False, "Lisensi telah kadaluarsa (cache).", 0
            
            # Check last verification (warn if too old)
            last_verified = self.cache.get('last_verified', '')
            try:
                last_check = datetime.strptime(last_verified, '%Y-%m-%d %H:%M:%S')
                days_since_check = (datetime.now() - last_check).days
                
                if days_since_check > 30:
                    msg = f"Lisensi valid (offline). {days_remaining} hari tersisa. ⚠️ Terakhir verifikasi online {days_since_check} hari lalu."
                else:
                    msg = f"Lisensi valid (offline). {days_remaining} hari tersisa."
                
                return True, msg, days_remaining
            except:
                return True, f"Lisensi valid (offline). {days_remaining} hari tersisa.", days_remaining
            
        except:
            return False, "Data lisensi cache rusak.", 0
    
    def get_license_info(self):
        """Get current license information"""
        if not self.cache:
            return {
                'status': 'unlicensed',
                'hwid': self.hwid,
                'message': 'Tidak ada lisensi aktif'
            }
        
        return {
            'status': self.cache.get('status', 'unknown'),
            'license_key': self.cache.get('license_key', 'N/A'),
            'email': self.cache.get('email', 'N/A'),
            'hwid': self.hwid,
            'activated_date': self.cache.get('activated_date', 'N/A'),
            'expiry_date': self.cache.get('expiry_date', 'N/A'),
            'last_verified': self.cache.get('last_verified', 'N/A')
        }

def check_license():
    """
    Main function to check license validity
    Returns: (valid: bool, message: str)
    """
    validator = LicenseValidator()
    valid, message, days = validator.verify_license()
    return valid, message

if __name__ == '__main__':
    # Test license validation
    print("=== License Validator Test ===\n")
    
    validator = LicenseValidator()
    info = get_system_info()
    
    print(f"System Info:")
    print(f"  OS: {info['os']}")
    print(f"  Hostname: {info['hostname']}")
    print(f"  HWID: {info['hwid']}\n")
    
    # Check current license
    valid, message, days = validator.verify_license()
    print(f"License Status: {'✓ VALID' if valid else '✗ INVALID'}")
    print(f"Message: {message}")
    if valid:
        print(f"Days Remaining: {days}")
