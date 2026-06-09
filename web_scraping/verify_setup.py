#!/usr/bin/env python3
"""
System Verification Script
Checks if all dependencies and system requirements are met
Run this before your first scraping session
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Tuple, List


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.8+"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version >= (3, 8):
        return True, version_str
    return False, version_str


def check_virtual_environment() -> Tuple[bool, str]:
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    venv_path = sys.prefix
    return in_venv, venv_path


def check_module(module_name: str) -> Tuple[bool, str]:
    """Check if a Python module is installed"""
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'Unknown')
        return True, version
    except ImportError:
        return False, "Not installed"


def check_chrome() -> Tuple[bool, str]:
    """Check if Chrome is installed"""
    paths = {
        'win32': [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ],
        'darwin': [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ],
        'linux': [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium',
        ]
    }
    
    search_paths = paths.get(sys.platform, [])
    
    for path in search_paths:
        if Path(path).exists():
            return True, path
    
    return False, "Not found in standard locations"


def check_chromedriver() -> Tuple[bool, str]:
    """Check if ChromeDriver can be downloaded"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        return True, driver_path
    except Exception as e:
        return False, str(e)


def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if a required file exists"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        return True, f"{size:,} bytes"
    return False, "File not found"


def check_writable_directory(directory: str = ".") -> Tuple[bool, str]:
    """Check if directory is writable"""
    try:
        test_file = Path(directory) / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True, "Writable"
    except Exception as e:
        return False, str(e)


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space"""
    try:
        import shutil
        _, _, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        
        if free_gb >= 0.5:  # Minimum 500MB
            return True, f"{free_gb:.2f} GB free"
        return False, f"Only {free_gb:.2f} GB available (need 0.5+ GB)"
    except Exception as e:
        return False, str(e)


def check_internet() -> Tuple[bool, str]:
    """Check internet connectivity"""
    try:
        import requests
        response = requests.get('https://www.google.com', timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "No connection"
    except Exception as e:
        return False, str(e)


def run_full_verification() -> int:
    """Run complete verification suite"""
    
    print_header("SYSTEM VERIFICATION TOOL")
    print_info("Checking system requirements for Image Scraper\n")
    
    all_passed = True
    
    # Python Version
    print(f"{Colors.BOLD}1. Python Environment{Colors.RESET}")
    python_ok, py_version = check_python_version()
    if python_ok:
        print_success(f"Python version: {py_version}")
    else:
        print_error(f"Python version: {py_version} (need 3.8+)")
        all_passed = False
    
    # Virtual Environment
    venv_ok, venv_path = check_virtual_environment()
    if venv_ok:
        print_success(f"Virtual environment: {venv_path}")
    else:
        print_warning("Not in virtual environment (recommended to use venv)")
    
    # Chrome Installation
    print(f"\n{Colors.BOLD}2. Browser Setup{Colors.RESET}")
    chrome_ok, chrome_path = check_chrome()
    if chrome_ok:
        print_success(f"Chrome browser: {chrome_path}")
    else:
        print_error(f"Chrome browser: {chrome_path}")
        all_passed = False
    
    # ChromeDriver
    driver_ok, driver_path = check_chromedriver()
    if driver_ok:
        print_success(f"ChromeDriver: {driver_path}")
    else:
        print_error(f"ChromeDriver: {driver_path}")
        print_info("Install with: pip install webdriver-manager")
        all_passed = False
    
    # Required Packages
    print(f"\n{Colors.BOLD}3. Python Dependencies{Colors.RESET}")
    required_packages = {
        'selenium': 'Selenium WebDriver',
        'requests': 'HTTP Library',
        'webdriver_manager': 'Driver Manager',
        'urllib3': 'URL Utilities',
    }
    
    for package, description in required_packages.items():
        pkg_ok, version = check_module(package)
        if pkg_ok:
            print_success(f"{description}: {package} v{version}")
        else:
            print_error(f"{description}: {package} - {version}")
            all_passed = False
    
    # Required Files
    print(f"\n{Colors.BOLD}4. Project Files{Colors.RESET}")
    required_files = {
        'image_scraper.py': 'Main scraper module',
        'requirements.txt': 'Dependencies list',
        'cli.py': 'Command-line interface',
        'examples.py': 'Example implementations',
        'README.md': 'Documentation',
    }
    
    for filename, description in required_files.items():
        file_ok, size = check_file_exists(filename)
        if file_ok:
            print_success(f"{description}: {filename} ({size})")
        else:
            print_warning(f"{description}: {filename} - {size}")
    
    # System Resources
    print(f"\n{Colors.BOLD}5. System Resources{Colors.RESET}")
    
    disk_ok, disk_info = check_disk_space()
    if disk_ok:
        print_success(f"Disk space: {disk_info}")
    else:
        print_error(f"Disk space: {disk_info}")
        all_passed = False
    
    writable_ok, writable_info = check_writable_directory()
    if writable_ok:
        print_success(f"Directory writable: {writable_info}")
    else:
        print_error(f"Directory writable: {writable_info}")
        all_passed = False
    
    # Network
    print(f"\n{Colors.BOLD}6. Network Connectivity{Colors.RESET}")
    net_ok, net_info = check_internet()
    if net_ok:
        print_success(f"Internet: {net_info}")
    else:
        print_error(f"Internet: {net_info}")
        print_warning("Check your internet connection or firewall")
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    if all_passed:
        print_success("All critical checks passed! ✨")
        print_success("You're ready to start scraping. Run:")
        print(f"\n  {Colors.BOLD}python cli.py \"your search query\"{Colors.RESET}\n")
        return 0
    else:
        print_error("Some checks failed. Please fix issues above.")
        print_info("Refer to SETUP.md for troubleshooting help.")
        print()
        return 1


def main():
    """Main entry point"""
    try:
        exit_code = run_full_verification()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Fatal error during verification: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
