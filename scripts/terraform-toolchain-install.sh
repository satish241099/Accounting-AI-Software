#!/bin/bash

set -euo pipefail

# Terraform CLI Toolchain Installation Script
# Installs Terraform CLI >=1.5.0, tflint, checkov/tfsec for KB-037 preflight
# Cross-platform: Linux, macOS, and Windows (Git Bash / MINGW / MSYS2)
# Target: KB-037 preflight blocker (critical-path)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Cross-platform OS detection
# Git Bash / MINGW returns "MINGW64_NT-10.0-..." from uname -s
detect_os() {
    local uname_s="$(uname -s)"
    # Check for Windows-based systems first
    if [[ "$uname_s" =~ ^MINGW ]] || [[ "$uname_s" =~ ^MSYS ]] || [[ "$uname_s" =~ ^CYGWIN ]]; then
        echo "Windows"
    elif [[ "$uname_s" == "Linux" ]]; then
        echo "Linux"
    elif [[ "$uname_s" == "Darwin" ]]; then
        echo "macOS"
    else
        # Fallback: check MSYSTEM environment variable
        if [[ -n "$MSYSTEM" ]] && [[ "$MSYSTEM" =~ ^(MINGW|MSYS) ]]; then
            echo "Windows"
        else
            echo "Unknown"
        fi
    fi
}

# Detect architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64)    echo "amd64" ;;
        aarch64)   echo "arm64" ;;
        *)         echo "amd64" ;;
    esac
}

# Get PATH bin directory (platform-appropriate)
get_bin_dir() {
    if [[ "$MACHINE" == "Windows" ]]; then
        # On Windows via Git Bash, use /usr/local/bin or user profile bin
        if [ -d "/usr/local/bin" ]; then
            echo "/usr/local/bin"
        elif [ -d "$HOME/bin" ]; then
            echo "$HOME/bin"
        else
            echo "/usr/local/bin"
        fi
    else
        # Linux/macOS
        echo "/usr/local/bin"
    fi
}

MACHINE=$(detect_os)
ARCH=$(detect_arch)
BIN_DIR=$(get_bin_dir)

log_info "Detected OS: $MACHINE, Arch: $ARCH, Bin dir: $BIN_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to add to PATH (cross-platform)
add_to_path() {
    local dir="$1"
    if [[ "$MACHINE" == "Windows" ]]; then
        # On Windows Git Bash, prepend to PATH
        if ! echo "$PATH" | grep -q "$dir"; then
            export PATH="$dir;$PATH"
        fi
    else
        # Linux/macOS: only add if not already present
        if [[ ":$PATH:" != *":$dir:"* ]] && [[ ":$PATH:" != *":$dir" ]] && [[ ":$PATH:" != *"$dir:"* ]]; then
            export PATH="$dir:$PATH"
        fi
    fi
}

# Detect download tool (curl or wget)
get_download_cmd() {
    if command -v curl >/dev/null 2>&1; then
        echo "curl -sL"
    elif command -v wget >/dev/null 2>&1; then
        echo "wget -q"
    else
        log_error "No download tool found (curl or wget required)"
        return 1
    fi
}

DOWNLOAD_CMD=$(get_download_cmd)
log_info "Using download tool: $DOWNLOAD_CMD"

# Install Terraform CLI >=1.5.0
install_terraform() {
    log_info "Installing Terraform CLI >=1.5.0"

    # Idempotency check: if terraform is available and >=1.5.0, skip
    if command_exists terraform; then
        TF_VERSION=$(terraform version | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        if [[ -n "$TF_VERSION" ]]; then
            # Version comparison: check if >= 1.5.0
            TF_MAJOR=$(echo "$TF_VERSION" | cut -d. -f1)
            TF_MINOR=$(echo "$TF_VERSION" | cut -d. -f2)
            if [[ "$TF_MAJOR" -gt 1 ]] || [[ "$TF_MAJOR" -eq 1 && "$TF_MINOR" -ge 5 ]]; then
                log_info "Terraform already installed: v$TF_VERSION >= 1.5.0. Skipping."
                return 0
            fi
        fi
    fi

    TERRAFORM_VERSION="1.5.0"
    ARCH=$(detect_arch)

    # Create temporary directory for download
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if [[ "$MACHINE" == "Windows" ]]; then
        # Windows: download Terraform ZIP and extract
        log_info "Downloading Terraform ${TERRAFORM_VERSION} for Windows ${ARCH}..."
        $DOWNLOAD_CMD "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_windows_${ARCH}.zip" -O terraform.zip
        unzip -o terraform.zip -d terraform_install
        # Install to bin directory
        mkdir -p "$BIN_DIR"
        cp -r terraform_install/terraform.exe "$BIN_DIR/" 2>/dev/null || true
    else
        # Linux/macOS: download Terraform ZIP
        log_info "Downloading Terraform ${TERRAFORM_VERSION} for Linux ${ARCH}..."
        $DOWNLOAD_CMD "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" -O terraform.zip
        unzip -o terraform.zip
    fi

    # Install to bin directory
    mkdir -p "$BIN_DIR"

    if [[ "$MACHINE" == "Windows" ]]; then
        # On Windows, terraform may be .exe already
        chmod +x terraform 2>/dev/null || true
        cp -f terraform "$BIN_DIR/" 2>/dev/null || true
    else
        # Linux/macOS: move to /usr/local/bin
        chmod +x terraform
        mv terraform "$BIN_DIR/" 2>/dev/null || sudo mv terraform "$BIN_DIR/"
    fi

    # Verify installation
    if command_exists terraform; then
        TF_VER=$(terraform version | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        log_info "Terraform CLI ${TF_VER} installed successfully"
    else
        log_error "Failed to install Terraform CLI"
        cd /
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Clean up
    cd /
    rm -rf "$TEMP_DIR"
}

# Install tflint
install_tflint() {
    log_info "Installing tflint"

    # Idempotency check
    if command_exists tflint; then
        TF_VERSION=$(tflint --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        log_info "tflint already installed: v$TF_VERSION. Skipping."
        return 0
    fi

    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if [[ "$MACHINE" == "Windows" ]]; then
        log_info "Downloading tflint for Windows ${ARCH}..."
        $DOWNLOAD_CMD "https://github.com/terraform-linters/tflint/releases/latest/download/tflint_windows_${ARCH}.zip" -O tflint.zip
        unzip -o tflint.zip -d tflint_install
        chmod +x tflint_install/tflint.exe
        mkdir -p "$BIN_DIR"
        cp -f tflint_install/tflint.exe "$BIN_DIR/"
    else
        log_info "Downloading tflint for Linux ${ARCH}..."
        $DOWNLOAD_CMD "https://github.com/terraform-linters/tflint/releases/latest/download/tflint_linux_${ARCH}.tar.gz" -O tflint.tar.gz
        tar -xzf tflint.tar.gz
        chmod +x tflint
        mkdir -p "$BIN_DIR"
        mv tflint "$BIN_DIR/"
    fi

    # Verify installation
    if command_exists tflint; then
        log_info "tflint installed successfully"
    else
        log_error "Failed to install tflint"
        cd /
        rm -rf "$TEMP_DIR"
        return 1
    fi

    # Clean up
    cd /
    rm -rf "$TEMP_DIR"
}

# Install security scanning tools (checkov preferred, tfsec fallback)
install_security_tools() {
    log_info "Installing security scanning tools"

    # Decision rule: Prefer checkov if pip3 available; otherwise tfsec
    if command_exists pip3; then
        log_info "Preferred: Installing checkov via pip3"

        # Idempotency check: detect checkov on PATH OR via pip3 location
        # (pip-installed checkov may not be on PATH in this shell; check both)
        if command_exists checkov; then
            CHECKOV_VERSION=$(checkov --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
            log_info "checkov already installed: v$CHECKOV_VERSION. Skipping."
        elif pip3 show checkov >/dev/null 2>&1; then
            CHECKOV_VER_PIP=$(pip3 show checkov 2>/dev/null | awk -F': ' '/^Version:/{print $2}')
            log_info "checkov already installed via pip3 (v$CHECKOV_VER_PIP); adding to PATH."
        else
            pip3 install --quiet checkov 2>&1
            log_info "checkov installed via pip3"
        fi

        # Add checkov to PATH if needed (Windows Git Bash)
        # Derive the Scripts dir from the ACTUAL pip3 location instead of
        # hardcoding the system Python path — user installs land in
        # $HOME/AppData/Roaming/Python/<ver>/Scripts, not /c/Python315/Scripts.
        if [[ "$MACHINE" == "Windows" ]]; then
            PYTHON_SITE=$(pip3 show checkov 2>/dev/null | awk -F': ' '/^Location:/{print $2}')
            if [[ -n "$PYTHON_SITE" ]]; then
                PYTHON_SCRIPTS="$(dirname "$PYTHON_SITE")/Scripts"
                if [ -d "$PYTHON_SCRIPTS" ]; then
                    add_to_path "$PYTHON_SCRIPTS"
                fi
            fi
        fi
    else
        log_info "Installing tfsec (fallback - no Python dependency)"
        if [[ "$MACHINE" == "Windows" ]]; then
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            log_info "Downloading tfsec for Windows ${ARCH}..."
            $DOWNLOAD_CMD "https://github.com/aquasecurity/tfsec/releases/latest/download/tfsec_windows_${ARCH}.zip" -O tfsec.zip
            unzip -o tfsec.zip -d tfsec_install
            chmod +x tfsec_install/tfsec.exe
            mkdir -p "$BIN_DIR"
            cp -f tfsec_install/tfsec.exe "$BIN_DIR/"
            cd /
            rm -rf "$TEMP_DIR"
        else
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            log_info "Downloading tfsec for Linux ${ARCH}..."
            $DOWNLOAD_CMD "https://github.com/aquasecurity/tfsec/releases/latest/download/tfsec-linux_${ARCH}.tar.gz" -O tfsec.tar.gz
            tar -xzf tfsec.tar.gz
            chmod +x tfsec
            mkdir -p "$BIN_DIR"
            mv tfsec "$BIN_DIR/"
            cd /
            rm -rf "$TEMP_DIR"
        fi
    fi
}

# Verify all tools
verify_installation() {
    log_info "Verifying Terraform toolchain installation"

    # Create verification directory
    mkdir -p docs

    # Start verification report
    echo "# Terraform CLI Toolchain Verification Report" > docs/terraform-toolchain-verification.md
    echo "Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")" >> docs/terraform-toolchain-verification.md
    echo "" >> docs/terraform-toolchain-verification.md

    # Check each tool
    echo "## Tool Versions" >> docs/terraform-toolchain-verification.md

    # Terraform
    if command_exists terraform; then
        TERRAFORM_VERSION=$(terraform version | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        echo "✅ Terraform: $TERRAFORM_VERSION" >> docs/terraform-toolchain-verification.md
        echo "Requirement: ≥1.5.0" >> docs/terraform-toolchain-verification.md
        # Version comparison
        TF_MAJOR=$(echo "$TERRAFORM_VERSION" | cut -d. -f1)
        TF_MINOR=$(echo "$TERRAFORM_VERSION" | cut -d. -f2)
        if [[ "$TF_MAJOR" -gt 1 ]] || [[ "$TF_MAJOR" -eq 1 && "$TF_MINOR" -ge 5 ]]; then
            echo "Result: PASS (>=1.5.0)" >> docs/terraform-toolchain-verification.md
        else
            echo "Result: FAIL (<1.5.0)" >> docs/terraform-toolchain-verification.md
        fi
    else
        echo "❌ Terraform: NOT INSTALLED" >> docs/terraform-toolchain-verification.md
        echo "Requirement: ≥1.5.0" >> docs/terraform-toolchain-verification.md
        echo "Result: FAIL (not installed)" >> docs/terraform-toolchain-verification.md
    fi

    # tflint
    if command_exists tflint; then
        TFLINT_VERSION=$(tflint --version | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        echo "✅ tflint: $TFLINT_VERSION" >> docs/terraform-toolchain-verification.md
        echo "Result: PASS" >> docs/terraform-toolchain-verification.md
    else
        echo "❌ tflint: NOT INSTALLED" >> docs/terraform-toolchain-verification.md
        echo "Result: FAIL" >> docs/terraform-toolchain-verification.md
    fi

    # checkov or tfsec
    if command_exists checkov; then
        CHECKOV_VERSION=$(checkov --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        echo "✅ checkov: $CHECKOV_VERSION" >> docs/terraform-toolchain-verification.md
        echo "Result: PASS" >> docs/terraform-toolchain-verification.md
    elif command_exists tfsec; then
        TFSEC_VERSION=$(tfsec --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        echo "✅ tfsec: $TFSEC_VERSION" >> docs/terraform-toolchain-verification.md
        echo "Result: PASS" >> docs/terraform-toolchain-verification.md
    else
        echo "❌ Security Scanner: NOT INSTALLED" >> docs/terraform-toolchain-verification.md
        echo "Result: FAIL" >> docs/terraform-toolchain-verification.md
    fi

    echo "" >> docs/terraform-toolchain-verification.md
    echo "## Installation Status" >> docs/terraform-toolchain-verification.md
    echo "All tools have been installed and verified for KB-037 preflight." >> docs/terraform-toolchain-verification.md

    # Determine overall result
    TERRAFORM_OK="no"
    TFLINT_OK="no"
    SECURITY_OK="no"

    if command_exists terraform; then
        TF_VER=$(terraform version | head -1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]*')
        TF_MAJOR=$(echo "$TF_VER" | cut -d. -f1)
        TF_MINOR=$(echo "$TF_VER" | cut -d. -f2)
        if [[ "$TF_MAJOR" -gt 1 ]] || [[ "$TF_MAJOR" -eq 1 && "$TF_MINOR" -ge 5 ]]; then
            TERRAFORM_OK="yes"
        fi
    fi

    if command_exists tflint; then
        TFLINT_OK="yes"
    fi

    if command_exists checkov || command_exists tfsec; then
        SECURITY_OK="yes"
    fi

    if [[ "$TERRAFORM_OK" == "yes" ]] && [[ "$TFLINT_OK" == "yes" ]] && [[ "$SECURITY_OK" == "yes" ]]; then
        echo "## Overall Result: PASS" >> docs/terraform-toolchain-verification.md
        echo "✅ All tools verified successfully" >> docs/terraform-toolchain-verification.md
    else
        echo "## Overall Result: FAIL" >> docs/terraform-toolchain-verification.md
        echo "❌ Some tools failed verification" >> docs/terraform-toolchain-verification.md
    fi

    # Display summary
    echo -e "\n${GREEN}=== Installation Complete ===${NC}"
    echo "Terraform CLI: $(command_exists terraform && terraform --version | head -n1 || echo 'FAILED')"
    echo "tflint: $(command_exists tflint && tflint --version | head -n1 || echo 'FAILED')"
    if command_exists checkov; then
        echo "checkov: $(checkov --version | head -n1)"
    elif command_exists tfsec; then
        echo "tfsec: $(tfsec --version | head -n1)"
    else
        echo "checkov/tfsec: NOT INSTALLED"
    fi
    echo -e "\nVerification report: ${GREEN}docs/terraform-toolchain-verification.md${NC}"
}

# Main installation process
main() {
    log_info "Starting Terraform CLI toolchain installation for KB-037 preflight"
    log_info "This installation unblocks critical-path dependencies: KB-037 → KB-053 → KB-047"

    # Install tools in sequence
    install_terraform
    install_tflint
    install_security_tools
    verify_installation

    log_info "✅ Terraform toolchain installation completed successfully!"
}

# Run main function
main