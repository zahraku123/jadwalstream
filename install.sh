#!/bin/bash

# JadwalStream - Installation Script
# This script automates the installation and setup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "================================================"
    echo "  JadwalStream - Automated Installation"
    echo "================================================"
    echo ""
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is not recommended for production."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
    REQUIRED_VERSION="3.10"
    
    if awk "BEGIN {exit !($PYTHON_VERSION >= $REQUIRED_VERSION)}"; then
        print_info "Python $PYTHON_VERSION detected (OK)"
    else
        print_error "Python $PYTHON_VERSION detected. Required: Python $REQUIRED_VERSION or higher"
        exit 1
    fi
}

# Check and install system dependencies
check_system_deps() {
    print_info "Checking system dependencies..."
    
    # Check FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "FFmpeg is not installed."
        read -p "Do you want to install FFmpeg? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                print_info "Installing FFmpeg on Linux..."
                sudo apt update
                sudo apt install -y ffmpeg
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                print_info "Installing FFmpeg on macOS..."
                brew install ffmpeg
            else
                print_error "Unsupported OS. Please install FFmpeg manually."
                exit 1
            fi
        else
            print_warning "FFmpeg not installed. Streaming features will not work."
        fi
    else
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1 | awk '{print $3}')
        print_info "FFmpeg detected: version $FFMPEG_VERSION ✓"
    fi
    
    # Check if running on Debian/Ubuntu for additional packages
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v apt &> /dev/null; then
        print_info "Checking additional system packages..."
        
        # List of packages to check
        packages_needed=()
        
        # Check for build essentials (might be needed for some Python packages)
        if ! dpkg -s python3-dev &> /dev/null; then
            packages_needed+=("python3-dev")
        fi
        
        # Install missing packages if any
        if [ ${#packages_needed[@]} -gt 0 ]; then
            print_info "Installing additional packages: ${packages_needed[*]}"
            sudo apt update
            sudo apt install -y "${packages_needed[@]}"
        else
            print_info "All system dependencies satisfied ✓"
        fi
    fi
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Check if pip is available for current python3
    if python3 -m pip --version &> /dev/null; then
        print_info "pip already installed"
    elif command -v pip3 &> /dev/null; then
        print_info "pip3 command found"
    else
        print_info "Installing pip..."
        if python3 -m ensurepip --default-pip 2>/dev/null; then
            print_info "pip installed via ensurepip"
        else
            print_error "Failed to install pip. Please install python3-pip manually:"
            print_error "  Ubuntu/Debian: sudo apt install python3-pip"
            print_error "  macOS: brew install python3"
            exit 1
        fi
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Try to install packages, handling PEP 668 externally-managed-environment
    print_info "Installing Python packages..."
    
    # Try normal installation first
    if python3 -m pip install -r requirements.txt --quiet 2>/dev/null; then
        print_info "Python dependencies installed successfully"
    elif pip3 install -r requirements.txt --quiet 2>/dev/null; then
        print_info "Python dependencies installed successfully"
    else
        # Check if it's an externally-managed-environment error
        print_warning "Standard pip install failed (likely PEP 668 protection)"
        print_info "Using --break-system-packages flag..."
        
        if python3 -m pip install -r requirements.txt --break-system-packages; then
            print_info "Python dependencies installed successfully with --break-system-packages"
        elif pip3 install -r requirements.txt --break-system-packages; then
            print_info "Python dependencies installed successfully with --break-system-packages"
        else
            print_error "Failed to install dependencies!"
            print_info "Alternative: Create a virtual environment:"
            print_info "  python3 -m venv venv"
            print_info "  source venv/bin/activate"
            print_info "  pip install -r requirements.txt"
            exit 1
        fi
    fi
}

# Check and install Node.js & PM2
check_nodejs() {
    print_info "Checking Node.js and PM2..."
    
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed."
        read -p "Do you want to install Node.js and PM2? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                print_info "Installing Node.js on Linux..."
                curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                sudo apt install -y nodejs
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                print_info "Installing Node.js on macOS..."
                brew install node
            fi
        fi
    else
        NODE_VERSION=$(node --version)
        print_info "Node.js detected: $NODE_VERSION"
    fi
    
    # Install PM2
    if ! command -v pm2 &> /dev/null; then
        print_warning "PM2 is not installed."
        read -p "Do you want to install PM2? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installing PM2..."
            sudo npm install -g pm2
            print_info "PM2 installed successfully"
        fi
    else
        PM2_VERSION=$(pm2 --version)
        print_info "PM2 detected: v$PM2_VERSION"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p videos
    mkdir -p thumbnails
    mkdir -p tokens
    mkdir -p ffmpeg_logs
    mkdir -p videos/done  # For looped videos
    print_info "Directories created"
    
    # Initialize SQLite database (runs migrations if exists, creates if not)
    print_info "Initializing/updating SQLite database..."
    python3 -c "from modules.database import init_database; init_database(); print('Database ready')" 2>&1
    if [ $? -eq 0 ]; then
        if [ -f "jadwalstream.db" ]; then
            print_info "Database initialized/migrated successfully"
        else
            print_info "Database created successfully"
        fi
    else
        print_error "Failed to initialize database"
        exit 1
    fi
}

# Setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Check for client_secret.json
    if [ ! -f "client_secret.json" ]; then
        print_warning "client_secret.json not found!"
        echo ""
        echo "⚠️  YouTube OAuth credentials required for full functionality"
        echo ""
        echo "To obtain credentials:"
        echo "1. Go to https://console.cloud.google.com"
        echo "2. Create a new project or select existing one"
        echo "3. Enable YouTube Data API v3"
        echo "4. Create OAuth 2.0 credentials (Desktop app)"
        echo "5. Download and save as 'client_secret.json' in this directory"
        echo ""
        print_info "You can add this later - the app will still start"
        read -p "Press Enter to continue..."
    else
        print_info "client_secret.json found ✓"
    fi
    
    # Check for license_config.json
    if [ ! -f "license_config.json" ]; then
        print_warning "license_config.json not found!"
        echo ""
        echo "⚠️  License system configuration missing"
        echo ""
        echo "Creating default license_config.json..."
        cat > license_config.json << 'EOF'
{
  "appScriptUrl": "YOUR_APPS_SCRIPT_URL_HERE",
  "validatorKey": "YOUR_VALIDATOR_KEY_HERE"
}
EOF
        print_info "Default license_config.json created"
        print_info "Edit this file with your license server details"
        print_info "See LICENSE_APPSCRIPT_SETUP.md for instructions"
    else
        print_info "license_config.json found ✓"
    fi
    
    # Check for telegram config (optional)
    if [ ! -f "modules/services/telegram_config.json" ]; then
        print_info "Creating default telegram_config.json..."
        mkdir -p modules/services
        cat > modules/services/telegram_config.json << 'EOF'
{
  "enabled": false,
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "admin_chat_id": "YOUR_CHAT_ID_HERE"
}
EOF
        print_info "Telegram notifications disabled by default"
        print_info "Edit modules/services/telegram_config.json to enable"
    fi
}

# Start application
start_application() {
    print_info "Starting application..."
    
    read -p "Start with PM2? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v pm2 &> /dev/null; then
            # Stop if already running
            pm2 stop jadwalstream 2>/dev/null || true
            pm2 delete jadwalstream 2>/dev/null || true
            
            # Start with PM2
            pm2 start app.py --name jadwalstream --interpreter python3
            pm2 save
            
            print_info "Application started with PM2"
            print_info "Use 'pm2 logs jadwalstream' to view logs"
            print_info "Use 'pm2 monit' to monitor"
            
            # Ask about auto-start
            read -p "Setup auto-start on boot? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pm2 startup
                print_info "Run the command above to enable auto-start"
            fi
        else
            print_warning "PM2 not available. Starting manually..."
            python3 app.py &
            print_info "Application started in background (PID: $!)"
        fi
    else
        print_info "Skipping auto-start. Run manually with: python3 app.py"
    fi
}

# Print final information
print_final_info() {
    echo ""
    echo "================================================"
    echo "  Installation Complete!"
    echo "================================================"
    echo ""
    print_info "Application URL: http://localhost:5000"
    print_info "Default credentials:"
    echo "  • Admin: admin / admin123"
    echo "  • Demo:  demo / demo123"
    echo ""
    if command -v pm2 &> /dev/null; then
        print_info "PM2 Commands:"
        echo "  • pm2 list                 - View all processes"
        echo "  • pm2 logs jadwalstream    - View application logs"
        echo "  • pm2 restart jadwalstream - Restart application"
        echo "  • pm2 stop jadwalstream    - Stop application"
        echo "  • pm2 monit                - Monitor resources"
        echo ""
    fi
    print_warning "⚠️  Important Next Steps:"
    echo "  1. ⚠️  CHANGE DEFAULT ADMIN PASSWORD IMMEDIATELY!"
    echo "  2. Activate your license key (License menu)"
    echo "  3. Add client_secret.json for YouTube OAuth (if not done)"
    echo "  4. Add YouTube account tokens via Settings menu"
    echo "  5. (Optional) Configure telegram notifications"
    echo ""
    print_info "💡 License System:"
    echo "  • Fresh install = NO active license"
    echo "  • You need to activate a license key via License menu"
    echo "  • license_config.json contains server URL only"
    echo "  • License data is stored locally in license_cache.json (not in git)"
    echo ""
    print_info "📚 Documentation:"
    echo "  • README.md - Quick start guide"
    echo "  • Check repository for detailed setup guides"
    echo ""
    print_info "🎉 Ready to use! Access the app at http://localhost:5000"
    echo ""
}

# Check for existing installation
check_existing_installation() {
    print_info "Checking for existing installation..."
    
    # Check if database exists
    if [ -f "jadwalstream.db" ]; then
        print_warning "Existing installation detected!"
        echo ""
        echo "Found existing files:"
        [ -f "jadwalstream.db" ] && echo "  • jadwalstream.db (database)"
        [ -f "license_cache.json" ] && echo "  • license_cache.json (license data)"
        [ -d "videos" ] && [ "$(ls -A videos 2>/dev/null)" ] && echo "  • videos/ (uploaded videos)"
        [ -d "tokens" ] && [ "$(ls -A tokens 2>/dev/null)" ] && echo "  • tokens/ (YouTube tokens)"
        echo ""
        read -p "Do you want to keep existing data? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "This will DELETE all existing data!"
            read -p "Are you sure? Type 'yes' to confirm: " confirm
            if [ "$confirm" = "yes" ]; then
                print_info "Cleaning up old installation..."
                rm -f jadwalstream.db
                rm -f license_cache.json
                rm -f scheduler_status.json
                rm -f auto_upload_scheduler_status.json
                rm -rf videos/*
                rm -rf tokens/*
                rm -rf ffmpeg_logs/*
                print_info "Old data removed. Fresh installation will proceed."
            else
                print_info "Keeping existing data. Installation will update files only."
            fi
        else
            print_info "Keeping existing data. Installation will update files only."
        fi
    else
        print_info "No existing installation found. Proceeding with fresh install."
    fi
}

# Main installation flow
main() {
    print_header
    check_root
    check_existing_installation
    check_python
    check_system_deps
    install_python_deps
    check_nodejs
    create_directories
    setup_environment
    start_application
    print_final_info
}

# Run main function
main
