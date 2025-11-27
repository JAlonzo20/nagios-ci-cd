# tools/add_pc_lab_hosts.py

import re
import argparse
from pathlib import Path

# Carpeta raíz de la config de Nagios dentro del repo
NAGIOS_CONF_DIR = Path("nagios_conf")

# Archivo donde están definidos los hosts PC-LAB 
PC_LAB_FILE = NAGIOS_CONF_DIR / "objects" / "pc-lab-hosts.cfg"

# Prefijo de los nombres de host
HOSTNAME_PREFIX = "PC-LAB-"

# Plantilla de host. Ajusta los campos si en tu archivo usas otros valores.
HOST_TEMPLATE = """define host{{
    use                     linux-server
    host_name               {hostname}
    alias                   {hostname}
    address                 {ip}
    max_check_attempts      5
    check_period            24x7
    notification_interval   30
    notification_period     24x7
}}

"""

def get_pc_hosts(text: str):
    """
    Regresa una lista de tuplas (pc_number, ip) para todos los PC-LAB-XX
    que tengan host_name y address en el archivo.
    """
    hosts = []
    # Busca bloques define host { ... }
    blocks = re.split(r"define\s+host\s*\{", text)
    for block in blocks:
        if "PC-LAB-" not in block:
            continue
        # Buscar host_name PC-LAB-XX
        hn_match = re.search(r"host_name\s+PC-LAB-(\d+)", block)
        ip_match = re.search(r"address\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", block)
        if hn_match and ip_match:
            num = int(hn_match.group(1))
            ip = ip_match.group(1)
            hosts.append((num, ip))
    return hosts

def main():
    parser = argparse.ArgumentParser(description="Agregar hosts PC-LAB automáticamente")
    parser.add_argument("--count", type=int, required=True,
                        help="Cantidad de PCs nuevas a agregar (ej. 5)")
    args = parser.parse_args()

    if not PC_LAB_FILE.exists():
        raise SystemExit(f"No encuentro el archivo {PC_LAB_FILE}")

    content = PC_LAB_FILE.read_text(encoding="utf-8")

    hosts = get_pc_hosts(content)
    if not hosts:
        print("No encontré hosts PC-LAB-XX, asumiendo que empezamos en 1 y IP base 192.168.0.1")
        current_max_num = 0
        base_ip = "192.168.0.1"
    else:
        # Tomamos el host con número más alto como referencia
        current_max_num, last_ip = max(hosts, key=lambda x: x[0])
        print(f"Último host encontrado: {HOSTNAME_PREFIX}{current_max_num} con IP {last_ip}")
        # De la IP del último host tomamos el prefijo a.b.c. y el último octeto
        parts = last_ip.split(".")
        if len(parts) != 4:
            raise SystemExit(f"IP inválida en el último host: {last_ip}")
        base_prefix = ".".join(parts[:3])
        last_octet = int(parts[3])
        base_ip = f"{base_prefix}.{last_octet}"

    start = current_max_num + 1
    end   = current_max_num + args.count

    new_blocks = []
    # A partir del último host, vamos aumentando el número y la IP
    # Si el último host era PC-LAB-60 con IP 192.168.0.60,
    # el siguiente será 61 con 192.168.0.61, etc.
    base_parts = base_ip.split(".")
    prefix = ".".join(base_parts[:3])
    last_octet = int(base_parts[3])

    for offset, num in enumerate(range(start, end + 1), start=1):
        hostname = f"{HOSTNAME_PREFIX}{num}"
        ip_octet = last_octet + offset
        ip = f"{prefix}.{ip_octet}"
        new_blocks.append(HOST_TEMPLATE.format(hostname=hostname, ip=ip))

    with PC_LAB_FILE.open("a", encoding="utf-8") as f:
        f.write("\n# --- Hosts generados automáticamente ---\n\n")
        for block in new_blocks:
            f.write(block)

    print(f"Agregados hosts desde {HOSTNAME_PREFIX}{start} hasta {HOSTNAME_PREFIX}{end}")

if __name__ == "__main__":
    main()
