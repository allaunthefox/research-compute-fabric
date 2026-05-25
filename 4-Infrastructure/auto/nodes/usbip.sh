#!/bin/bash
# usbip.sh — USB/IP capability probe for mesh USB export/import.
# Output: JSON only. Observe-only: does not bind, export, attach, or detach devices.

json_string() {
    printf '%s' "${1:-}" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g'
}

module_state() {
    name="$1"
    loaded=false
    available=false
    if lsmod 2>/dev/null | awk '{print $1}' | grep -qx "$name"; then
        loaded=true
    fi
    if modinfo "$name" >/dev/null 2>&1; then
        available=true
    fi
    printf '"%s":{"available":%s,"loaded":%s}' "$(json_string "$name")" "$available" "$loaded"
}

command_path() {
    command -v "$1" 2>/dev/null || true
}

service_active=false
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet usbipd 2>/dev/null; then
    service_active=true
fi

port_listening=false
if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE '(^|:)3240$'; then
    port_listening=true
fi

tailscale_ips=""
if command -v tailscale >/dev/null 2>&1; then
    tailscale_ips=$(tailscale ip -4 2>/dev/null | paste -sd, -)
elif ip -4 addr show tailscale0 >/dev/null 2>&1; then
    tailscale_ips=$(ip -4 -o addr show tailscale0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | paste -sd, -)
fi

devices="["
first=true
for dev in /sys/bus/usb/devices/[0-9]*; do
    [ -f "$dev/idVendor" ] || continue
    busid="${dev##*/}"
    vid=$(cat "$dev/idVendor" 2>/dev/null || true)
    pid=$(cat "$dev/idProduct" 2>/dev/null || true)
    speed=$(cat "$dev/speed" 2>/dev/null || true)
    product=$(cat "$dev/product" 2>/dev/null || true)
    manufacturer=$(cat "$dev/manufacturer" 2>/dev/null || true)
    class=$(cat "$dev/bDeviceClass" 2>/dev/null || true)
    driver=$(readlink "$dev/driver" 2>/dev/null | sed 's#.*/##' || true)

    $first && first=false || devices+=","
    devices+="{\"busid\":\"$(json_string "$busid")\",\"vid\":\"$(json_string "$vid")\",\"pid\":\"$(json_string "$pid")\",\"speed_mbps\":\"$(json_string "$speed")\",\"class\":\"$(json_string "$class")\",\"manufacturer\":\"$(json_string "$manufacturer")\",\"product\":\"$(json_string "$product")\",\"driver\":\"$(json_string "$driver")\"}"
done
devices+="]"

usbip_bin=$(command_path usbip)
usbipd_bin=$(command_path usbipd)

printf '{'
printf '"schema":"research_stack_usbip_capability_probe_v1",'
printf '"hostname":"%s",' "$(json_string "$(hostname 2>/dev/null || echo unknown)")"
printf '"kernel":"%s",' "$(json_string "$(uname -r 2>/dev/null || echo unknown)")"
printf '"tailscale_ips":"%s",' "$(json_string "$tailscale_ips")"
printf '"tools":{"usbip":"%s","usbipd":"%s"},' "$(json_string "$usbip_bin")" "$(json_string "$usbipd_bin")"
printf '"modules":{'
module_state usbip_core
printf ','
module_state usbip_host
printf ','
module_state vhci_hcd
printf '},'
printf '"server":{"usbipd_service_active":%s,"tcp_3240_listening":%s},' "$service_active" "$port_listening"
printf '"devices":%s,' "$devices"
printf '"claim_boundary":"observe_only_no_usbip_bind_export_attach_or_detach"'
printf '}\n'
