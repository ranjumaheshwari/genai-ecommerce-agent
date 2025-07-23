#!/usr/bin/env python3
"""
Setup script for GenAI E-commerce Agent
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up GenAI E-commerce Agent")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Check if .env exists
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("📝 Please copy .env.example to .env and configure your API key")
            if sys.platform == "win32":
                run_command("copy .env.example .env", "Creating .env file")
            else:
                run_command("cp .env.example .env", "Creating .env file")
        else:
            print("⚠️  Please create a .env file with your GEMINI_API_KEY")
    else:
        print("✅ .env file already exists")
    
    # Load sample data
    if not run_command(f"python app/load_data.py", "Loading sample data"):
        print("⚠️  Sample data loading failed, but you can continue")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Google Gemini API key")
    print("2. Run: python -m app.main")
    print("3. In another terminal: cd frontend && npm install && npm start")
    print("4. Visit http://localhost:3000")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)
