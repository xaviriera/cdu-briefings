#!/bin/bash
# Arranque Acer: copia el cargador de Ubuntu a la ruta que esta BIOS si mira
set -e
mountpoint -q /mnt || mount /dev/sda1 /mnt
mkdir -p /mnt/EFI/Microsoft/Boot
cp /mnt/EFI/ubuntu/* /mnt/EFI/Microsoft/Boot/
mv -f /mnt/EFI/Microsoft/Boot/shimx64.efi /mnt/EFI/Microsoft/Boot/bootmgfw.efi
sync
umount /mnt
echo
echo "======================================"
echo " LISTO. Apaga, saca el pen y enciende."
echo "======================================"
