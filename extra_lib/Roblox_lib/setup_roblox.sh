#!/bin/bash
DIR_ATUAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$DIR_ATUAL/roblox_pkg.txt"
PIP_FILE="$DIR_ATUAL/roblox_pip.txt"

echo "[*] Diagnosticando ambiente nativo (Termux)..."

# 1. Verifica pacotes do Termux (apt)
MISSING_PKGS=""
if [ -f "$PKG_FILE" ]; then
    for pkg in $(cat "$PKG_FILE"); do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS $pkg"
        fi
    done
fi
if [ -n "$MISSING_PKGS" ]; then
    echo "[!] Instalando pacotes nativos faltantes:$MISSING_PKGS"
    pkg update -y
    pkg install -y $MISSING_PKGS
fi

# 2. Verifica pacotes Python no Termux
MISSING_TERMUX_PIP=""
if [ -f "$PIP_FILE" ]; then
    for pkg in $(cat "$PIP_FILE"); do
        if ! python3 -m pip show "$pkg" >/dev/null 2>&1; then
            MISSING_TERMUX_PIP="$MISSING_TERMUX_PIP $pkg"
        fi
    done
fi
if [ -n "$MISSING_TERMUX_PIP" ]; then
    echo "[!] Instalando dependências Python faltantes (Termux):$MISSING_TERMUX_PIP"
    python3 -m pip install $MISSING_TERMUX_PIP --user --break-system-packages || python3 -m pip install $MISSING_TERMUX_PIP --user
fi

# 3. Garante que o PRoot e Ubuntu existam
if ! command -v proot-distro >/dev/null 2>&1; then
    echo "[*] Instalando motor de virtualização (proot-distro)..."
    pkg install -y proot-distro
fi
if [ ! -d "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/ubuntu" ]; then
    echo "[*] Instalando Ubuntu (isso pode demorar)..."
    proot-distro install ubuntu
fi

# 4. Entra no Ubuntu e audita as bibliotecas internas
proot-distro login ubuntu --bind "$DIR_ATUAL:/lib_setup" -- bash -c "
export DEBIAN_FRONTEND=noninteractive
export TZ=America/Sao_Paulo

if ! dpkg -s python3-pip >/dev/null 2>&1 || ! dpkg -s libxcomposite1 >/dev/null 2>&1; then
    echo '[*] Instalando base estrutural do Ubuntu (Python3 e Libs Gráficas Playwright)...'
    apt-get update -y
    apt-get upgrade -y
    
    # Previne que a instalação pare pedindo localização
    apt-get install -y tzdata
    
    apt-get install -y python3 python3-dev python3-pip libnss3 libatk1.0-0t64 libcups2t64 libgbm1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxkbcommon0 libasound2t64 libatspi2.0-0t64 || \
    apt-get install -y python3 python3-dev python3-pip libnss3 libatk1.0-0 libcups2 libgbm1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxkbcommon0 libasound2 libatspi2.0-0
fi

MISSING_UBUNTU_PIP=\"\"
if [ -f '/lib_setup/roblox_pip.txt' ]; then
    for pkg in \$(cat /lib_setup/roblox_pip.txt); do
        if ! python3 -m pip show \"\$pkg\" >/dev/null 2>&1; then
            MISSING_UBUNTU_PIP=\"\$MISSING_UBUNTU_PIP \$pkg\"
        fi
    done
fi

if [ -n \"\$MISSING_UBUNTU_PIP\" ]; then
    echo -e \"\n[!] Baixando e Instalando bibliotecas faltantes no Ubuntu:\$MISSING_UBUNTU_PIP\"
    python3 -m pip install \$MISSING_UBUNTU_PIP --break-system-packages
else
    echo '[V] Bibliotecas Python do Ubuntu estao 100% OK.'
fi

if [ ! -d \"\$HOME/.cache/ms-playwright\" ]; then
    echo '[*] Baixando navegadores em segundo plano (Patchright Chromium)...'
    python3 -m patchright install chromium
    echo '[*] Acionando dependências nativas via patchright...'
    python3 -m patchright install-deps
fi
"
