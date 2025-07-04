#!/bin/bash

GREEN="\033[0;32m"
CYAN="\033[0;36m"
WHITE="\033[0m"
RED="\033[0;31m"

reset_color() {
  echo -ne "${WHITE}"
}

install_brew_packages() {
  echo -e "\n${GREEN}[+]${CYAN} Checking required packages..."

  local packages=(curl unzip python3)
  local missing=()

  # Check installed packages for curl, unzip, python3
  for pkg in "${packages[@]}"; do
    if ! command -v "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done

  # Check cloudflared separately, since it might be installed but not via brew or named differently
  if ! command -v cloudflared >/dev/null 2>&1; then
    missing+=("cloudflared")
  fi

  if [ ${#missing[@]} -eq 0 ]; then
    echo -e "\n${GREEN}[+]${GREEN} Packages already installed.${WHITE}"
    return
  fi

  echo -e "\n${GREEN}[+]${CYAN} The following packages are missing: ${missing[*]}"

  # Check for brew installation
  if ! command -v brew >/dev/null 2>&1; then
    read -rp "[+] Homebrew is not installed. Install Homebrew now? (y/N): " answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
      echo -e "\n${RED}[!]${RED} Cannot continue without Homebrew.${WHITE}"
      exit 1
    fi
    echo -e "\n${GREEN}[+]${CYAN} Installing Homebrew...${WHITE}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to shell environment (adjust for architecture)
    if [[ "$(uname -m)" == "arm64" ]]; then
      echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
      eval "$(/opt/homebrew/bin/brew shellenv)"
    else
      echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
      eval "$(/usr/local/bin/brew shellenv)"
    fi
  fi

  # Install missing packages
  for pkg in "${missing[@]}"; do
    echo -e "\n${GREEN}[+]${CYAN} Installing package: ${pkg}${WHITE}"
    brew install "$pkg"
  done
}

install_python_dependencies() {
  echo -e "\n${GREEN}[+]${CYAN} Installing Python dependencies from requirements.txt..."

  if ! command -v pip3 >/dev/null 2>&1; then
    echo -e "\n${RED}[!]${RED} pip3 not found. Please install pip for Python3.${WHITE}"
    exit 1
  fi

  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
}

check_internet_status() {
  echo -ne "\n${GREEN}[+]${CYAN} Internet Status : "
  if command -v gtimeout >/dev/null 2>&1; then
    if gtimeout 3 curl -fIs "https://api.github.com" >/dev/null 2>&1; then
      echo -e "${GREEN}Online${WHITE}"
    else
      echo -e "${RED}Offline${WHITE}"
    fi
  else
    if curl -fIs --max-time 3 "https://api.github.com" >/dev/null 2>&1; then
      echo -e "${GREEN}Online${WHITE}"
    else
      echo -e "${RED}Offline${WHITE}"
    fi
  fi
}

echo -e "${GREEN}[+]${CYAN} Starting Phisher-X Setup...${WHITE}"

mkdir -p .server
install_brew_packages
check_internet_status
install_python_dependencies

echo -e "\n${GREEN}[+]${CYAN} Setup complete. Starting phisherx.py...\n${WHITE}"

python3 phisherx.py

