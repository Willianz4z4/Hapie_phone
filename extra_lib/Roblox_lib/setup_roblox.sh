#!/bin/bash
DIR_ATUAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$DIR_ATUAL/roblox_pkg.txt"
PIP_FILE="$DIR_ATUAL/roblox_pip.txt"
LOCK_FILE="$DIR_ATUAL/.setup_concluido_v2"

# Se o arquivo de trava existir, sai silenciosamente (Boot rápido)
if [ -f "$LOCK_FILE" ]; then
    exit 0
fi

echo "[*] Verificando pacotes do sistema no Termux..."
MISSING_PKGS=""
if [ -f "$PKG_FILE" ]; then
    for pkg in $(cat "$PKG_FILE"); do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS $pkg"
        fi
    done
fi

if [ -n "$MISSING_PKGS" ]; then
    echo "[!] Instalando pacotes faltantes no Termux:$MISSING_PKGS"
    pkg update -y >/dev/null 2>&1
    pkg install -y $MISSING_PKGS >/dev/null 2>&1
fi

echo "[*] Instalando dependências Python NATIVAS no Termux..."
python3 -m pip install --upgrade pip --user --break-system-packages >/dev/null 2>&1 || python3 -m pip install --upgrade pip --user >/dev/null 2>&1

if [ -f "$PIP_FILE" ]; then
    python3 -m pip install -r "$PIP_FILE" --user --break-system-packages >/dev/null 2>&1 || python3 -m pip install -r "$PIP_FILE" --user >/dev/null 2>&1
fi

if ! command -v proot-distro >/dev/null 2>&1; then
    echo "[*] Instalando proot-distro..."
    pkg install -y proot-distro >/dev/null 2>&1
fi

if [ ! -d "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/ubuntu" ]; then
    echo "[*] Instalando Ubuntu (isso pode demorar)..."
    proot-distro install ubuntu >/dev/null 2>&1
fi

echo "[*] Configurando ambiente Ubuntu e dependências de Navegador..."
proot-distro login ubuntu --bind "$DIR_ATUAL:/lib_setup" -- bash -c "
export DEBIAN_FRONTEND=noninteractive
echo '[*] Atualizando repositórios e forçando upgrade (Sincronizando Python)...'
apt-get update -y >/dev/null 2>&1
apt-get upgrade -y >/dev/null 2>&1

echo '[*] Instalando dependências C++ e bibliotecas gráficas...'
apt-get install -y python3 python3-dev python3-pip libnss3 libatk1.0-0t64 libcups2t64 libgbm1 >/dev/null 2>&1 || apt-get install -y python3 python3-dev python3-pip libnss3 libatk1.0-0 libcups2 libgbm1 >/dev/null 2>&1

if [ -f '/lib_setup/roblox_pip.txt' ]; then
    echo '[*] Instalando bibliotecas Python (patchright, etc) no Ubuntu...'
    python3 -m pip install -r /lib_setup/roblox_pip.txt --break-system-packages >/dev/null 2>&1
fi

echo '[*] Instalando binários do Chromium (Patchright)...'
python3 -m patchright install chromium >/dev/null 2>&1
"

# Cria a trava para não rodar as instalações nas próximas vezes
touch "$LOCK_FILE"
echo "[*] Setup automático concluído com sucesso nas duas camadas!"
