"""
Hardware ID Generator
Generates unique hardware ID based on system characteristics
"""
import platform
import subprocess
import hashlib
import uuid

def get_hwid():
    """
    Generate unique hardware ID based on:
    - CPU info
    - MAC address
    - Machine UUID (if available)
    - Hostname
    
    Returns consistent HWID for same machine
    """
    components = []
    
    # 1. Get CPU info
    try:
        if platform.system() == 'Windows':
            cpu_info = subprocess.check_output('wmic cpu get processorid', shell=True).decode()
            cpu_id = cpu_info.split('\n')[1].strip()
            components.append(cpu_id)
        elif platform.system() == 'Linux':
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Serial' in line or 'processor' in line:
                        components.append(line.strip())
                        break
    except:
        pass
    
    # 2. Get MAC address
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0,2*6,2)][::-1])
        components.append(mac)
    except:
        pass
    
    # 3. Get machine UUID
    try:
        if platform.system() == 'Windows':
            machine_uuid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode()
            machine_id = machine_uuid.split('\n')[1].strip()
            components.append(machine_id)
        elif platform.system() == 'Linux':
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()
                components.append(machine_id)
    except:
        pass
    
    # 4. Get hostname as fallback
    try:
        hostname = platform.node()
        components.append(hostname)
    except:
        pass
    
    # 5. Combine all components and hash
    combined = '|'.join(components)
    hwid_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    # Return first 32 characters for readability
    return hwid_hash[:32].upper()

def get_system_info():
    """Get human-readable system information"""
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'hwid': get_hwid()
    }

if __name__ == '__main__':
    # Test HWID generation
    print("=== Hardware ID Generator ===")
    info = get_system_info()
    print(f"\nOS: {info['os']}")
    print(f"Hostname: {info['hostname']}")
    print(f"Processor: {info['processor']}")
    print(f"\nHWID: {info['hwid']}")
    print("\nThis HWID will be used for license activation.")
