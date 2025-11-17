#!/bin/bash
set -euo pipefail
OUT="/usr/local/nagios/etc/objects/pc-lab-hosts.cfg"
{
  cat <<'HDR'
# Autogenerado – EC2 y PCs del LAB

define host{
  use                    linux-server-lab
  host_name              ec2-docker-host
  alias                  EC2 Docker Host (WireGuard)
  address                10.10.10.1
}
HDR

  for i in {11..60}; do
    ip="192.168.0.$i"
    cat <<EOM
define host{
  use                    generic-host-lab
  host_name              PC-LAB-${i}
  alias                  PC-LAB-${i}
  address                ${ip}
  parents                ec2-docker-host
}

define service{
  use                    generic-service-lab
  host_name              PC-LAB-${i}
  service_description    PING
  check_command          check-host-alive
}

define service{
  use                    generic-service-lab
  host_name              PC-LAB-${i}
  service_description    NRPE - CPU
  check_command          check_nrpe_custom!check_cpu
}

define service{
  use                    generic-service-lab
  host_name              PC-LAB-${i}
  service_description    NRPE - Mem
  check_command          check_nrpe_custom!check_mem
}

define service{
  use                    generic-service-lab
  host_name              PC-LAB-${i}
  service_description    NRPE - Uptime
  check_command          check_nrpe_custom!check_uptime
}
EOM
  done
} > "$OUT"

chown nagios:nagios "$OUT"
echo "Generado: $OUT"
