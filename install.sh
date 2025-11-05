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

# Check and install FFmpeg
check_ffmpeg() {
    print_info "Checking FFmpeg..."
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
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
        print_info "FFmpeg detected: $FFMPEG_VERSION"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        print_info "Installing pip..."
        python3 -m ensurepip --default-pip
    fi
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        print_info "Python dependencies installed successfully"
    else
        print_error "requirements.txt not found!"
        exit 1
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
    print_info "Directories created"
    
    # Create empty Excel file if not exists
    if [ ! -f "live_stream_data.xlsx" ]; then
        print_info "Creating empty schedule database..."
        python3 create_empty_excel.py
    else
        print_info "Schedule database already exists"
    fi
}

# Setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Copy example files if not exist
    print_info "Copying template files..."
    for file in *.example; do
        if [ -f "$file" ]; then
            target="${file%.example}"
            if [ ! -f "$target" ]; then
                cp "$file" "$target"
                print_info "Created $target from template"
            else
                print_info "Skipped $target (already exists)"
            fi
        fi
    done
    
    # Check for client_secret.json
    if [ ! -f "client_secret.json" ]; then
        print_warning "client_secret.json not found!"
        echo "Please obtain OAuth credentials from Google Cloud Console:"
        echo "1. Go to https://console.cloud.google.com"
        echo "2. Create OAuth 2.0 credentials"
        echo "3. Download and save as 'client_secret.json'"
        echo ""
        echo "See SETUP.md for detailed instructions"
        read -p "Press Enter when ready to continue..."
    fi
    
    # Check for license_credentials.json
    if [ ! -f "license_credentials.json" ]; then
        print_warning "license_credentials.json not found!"
        echo "License system requires Google Sheets credentials."
        echo "See SETUP.md for detailed instructions"
        read -p "Do you have license_credentials.json? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "You can set this up later."
        fi
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
    print_info "Default login: admin / admin123"
    echo ""
    print_info "Useful commands:"
    echo "  - pm2 list               : View all processes"
    echo "  - pm2 logs jadwalstream  : View application logs"
    echo "  - pm2 restart jadwalstream : Restart application"
    echo "  - pm2 stop jadwalstream  : Stop application"
    echo "  - pm2 monit              : Monitor resources"
    echo ""
    print_warning "Remember to:"
    echo "  1. Setup client_secret.json for Google OAuth"
    echo "  2. Setup license_credentials.json for license system"
    echo "  3. Configure telegram_config.json for notifications"
    echo "  4. Change default admin password"
    echo ""
}

# Main installation flow
main() {
    print_header
    check_root
    check_python
    check_ffmpeg
    install_python_deps
    check_nodejs
    create_directories
    setup_environment
    start_application
    print_final_info
}

# Run main function
main
