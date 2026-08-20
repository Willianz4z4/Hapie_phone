#!/bin/bash
DIR_ATUAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$DIR_ATUAL/roblox_pkg.txt"
PIP_FILE="$DIR_ATUAL/roblox_pip.txt"

echo "[*] Verificando pacotes do sistema..."
MISSING_PKGS=""
if [ -f "$PKG_FILE" ]; then
    for pkg in $(cat "$PKG_FILE"); do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS $pkg"
        fi
    done
fi

if [ -n "$MISSING_PKGS" ]; then
    echo "[!] Instalando pacotes faltantes:$MISSING_PKGS"
    pkg update -y
    pkg install -y $MISSING_PKGS
fi

if ! command -v proot-distro >/dev/null 2>&1; then
    echo "[*] Instalando proot-distro..."
    pkg install -y proot-distro
fi

if [ ! -d "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/ubuntu" ]; then
    echo "[*] Instalando Ubuntu (isso pode demorar)..."
    proot-distro install ubuntu
fi

echo "[*] Configurando ambiente Ubuntu e dependências Python..."
proot-distro login ubuntu --bind "$DIR_ATUAL:/lib_setup" -- bash -c "
export DEBIAN_FRONTEND=noninteractive
echo '[*] Atualizando repositórios no Ubuntu...'
apt-get update -y
echo '[*] Instalando dependências de navegador...'
apt-get install -y python3 python3-pip libnss3 libatk1.0-0 libcups2 libgbm1
if [ -f '/lib_setup/roblox_pip.txt' ]; then
    echo '[*] Instalando bibliotecas Python (patchright, etc)...'
    python3 -m pip install -r /lib_setup/roblox_pip.txt --break-system-packages
fi
echo '[*] Instalando binários do Chromium (isso pode demorar)...'
python3 -m patchright install chromium
"
echo "[*] Setup concluído com sucesso!"
