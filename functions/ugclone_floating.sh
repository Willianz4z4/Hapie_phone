#!/bin/sh
# ==========================================================
# ugclone_floating - Window & Fullscreen Injector for Clones
# ==========================================================

# Função para injetar o layout de tela cheia sem cortar os botões (Não abre o app)
fullscreen_clone() {
    local pkg="$1"
    if [ -z "$pkg" ]; then
        echo "[-] Erro: Informe o pacote. Ex: fullscreen_clone com.roblox.clienw"
        return 1
    fi

    echo "===> Aplicando layout otimizado para: $pkg"
    su -c "am force-stop '$pkg'" 2>/dev/null

    local res=$(su -c "wm size" | grep -oE "[0-9]+x[0-9]+" | head -n 1)
    local w=$(echo $res | cut -dx -f1)
    local h=$(echo $res | cut -dx -f2)
    
    if [ -z "$w" ] || [ -z "$h" ]; then
        w=720
        h=1280
    fi

    local bar_height=85
    local new_h=$(( h - bar_height ))

    su -c "
        find /data /sdcard/Android/data -name '*$pkg*' -type d 2>/dev/null | while read dir; do
            pref_dir=\"\$dir/shared_prefs\"
            mkdir -p \"\$pref_dir\" 2>/dev/null
            
            for name in '${pkg}_preferences.xml' 'FreeFormWindow.xml' 'freeform.xml'; do
                target=\"\$pref_dir/\$name\"
                chmod 666 \"\$target\" 2>/dev/null
                
                cat << 'INNER_EOF' > \"\$target\"
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <int name='free_form_window_left' value='0' />
    <int name='free_form_window_top' value='$bar_height' />
    <int name='free_form_window_right' value='$w' />
    <int name='free_form_window_bottom' value='$h' />
    <int name='free_form_window_width' value='$w' />
    <int name='free_form_window_height' value='$new_h' />
    <int name='app_cloner_current_window_left' value='0' />
    <int name='app_cloner_current_window_top' value='$bar_height' />
    <int name='app_cloner_current_window_right' value='$w' />
    <int name='app_cloner_current_window_bottom' value='$h' />
</map>
INNER_EOF
                chmod 666 \"\$target\" 2>/dev/null
                chown 10115:10115 \"\$target\" 2>/dev/null
            done
        done
    "
    echo "[+] Configuração aplicada com sucesso!"
}

# Função para verificar se o app usa preferências flutuantes (Retorna True ou False)
clone_floating() {
    local pkg="$1"
    if [ -z "$pkg" ]; then
        echo "False"
        return 1
    fi

    local result=$(su -c "
        if [ -d '/data/data/$pkg/shared_prefs' ] && [ \"\$(ls -A /data/data/$pkg/shared_prefs 2>/dev/null)\" ]; then
            echo 'True'
        else
            echo 'False'
        fi
    ")
    echo "$result"
}
