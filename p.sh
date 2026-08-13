#!/bin/bash
# Preparacion del equipo de obra - Torres de Cotillas (camaras + timelapse)
# Uso:  curl -sL <url> | bash
set -euo pipefail

CLAVE_MB="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBKLcvGy/U5U/UuP92TRMEcIU4dAiKyDYi5k/kfjoB/z mainbrain->obra-tdc"
HOST="obra-tdc"

echo "==> 1/9  Actualizando el sistema"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

echo "==> 2/9  Instalando paquetes"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq   openssh-server curl ffmpeg htop git jq unzip ca-certificates

echo "==> 3/9  Nombre del equipo: $HOST"
sudo hostnamectl set-hostname "$HOST"

echo "==> 4/9  Que NO se duerma nunca (tapa cerrada, inactividad)"
sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/99-obra.conf >/dev/null <<'EOF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
HandleLidSwitchExternalPower=ignore
HandleSuspendKey=ignore
HandleHibernateKey=ignore
IdleAction=ignore
EOF
sudo systemctl restart systemd-logind
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# Ahorro de energia del escritorio XFCE
for p in inactivity-on-ac inactivity-on-battery blank-on-ac blank-on-battery          dpms-on-ac-sleep dpms-on-ac-off dpms-on-battery-sleep dpms-on-battery-off; do
  xfconf-query -c xfce4-power-manager -p "/xfce4-power-manager/$p" -s 0 --create -t int 2>/dev/null || true
done
xfconf-query -c xfce4-screensaver -p /saver/enabled -s false --create -t bool 2>/dev/null || true
xfconf-query -c xfce4-screensaver -p /lock/enabled  -s false --create -t bool 2>/dev/null || true

echo "==> 5/9  Acceso SSH desde Main Brain"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys"
grep -qF "$CLAVE_MB" "$HOME/.ssh/authorized_keys" || echo "$CLAVE_MB" >> "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
sudo systemctl enable --now ssh

echo "==> 6/9  Reenvio de red (para anunciar la subred del local)"
sudo tee /etc/sysctl.d/99-tailscale.conf >/dev/null <<'EOF'
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf >/dev/null

echo "==> 7/9  Tailscale"
if ! command -v tailscale >/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "==> 8/9  RustDesk (escritorio remoto)"
cd /tmp
RD_URL=$(curl -fsSL https://api.github.com/repos/rustdesk/rustdesk/releases/latest   | jq -r '.assets[] | select(.name | endswith("x86_64.deb")) | .browser_download_url' | head -1)
if [ -n "$RD_URL" ]; then
  curl -fsSL -o rustdesk.deb "$RD_URL"
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ./rustdesk.deb
  sudo systemctl enable --now rustdesk || true
else
  echo "    AVISO: no se pudo obtener la URL de RustDesk. Instalalo a mano desde rustdesk.com"
fi

echo "==> 9/9  Inicio de sesion automatico (necesario para RustDesk tras un corte de luz)"
sudo groupadd -f autologin
sudo usermod -aG autologin "$USER"
sudo mkdir -p /etc/lightdm/lightdm.conf.d
sudo tee /etc/lightdm/lightdm.conf.d/50-autologin.conf >/dev/null <<EOF
[Seat:*]
autologin-user=$USER
autologin-user-timeout=0
EOF

echo
echo "================= LISTO ================="
echo "Usuario   : $USER"
echo "Equipo    : $HOST"
echo "IP local  : $(hostname -I | awk '{print $1}')"
echo
echo "AHORA FALTAN 2 PASOS QUE PIDEN NAVEGADOR:"
echo
echo "  A) Tailscale - pega esto y abre el enlace que salga:"
echo "     sudo tailscale up --advertise-routes=192.168.1.0/24 --accept-routes --ssh"
echo
echo "  B) RustDesk - abre la aplicacion RustDesk en el escritorio y apunta:"
echo "     - el ID (9 digitos)"
echo "     - la contrasena permanente (ponla tu en Ajustes > Seguridad)"
echo "========================================="
echo
echo "IMPORTANTE: reinicia al terminar para que el inicio automatico tenga efecto."
