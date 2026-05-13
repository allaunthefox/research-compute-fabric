#!/usr/bin/env bash
set -euo pipefail

module="qfox_topology_manager"
tracefs="/sys/kernel/tracing"
state="/run/${module}_ftrace_state"

if [[ ! -d "$tracefs" ]]; then
  tracefs="/sys/kernel/debug/tracing"
fi

if [[ ! -d "$tracefs" ]]; then
  echo "tracefs is not mounted" >&2
  exit 2
fi

cmd="${1:-snapshot}"

require_loaded() {
  if ! grep -q "^${module} " /proc/modules; then
    echo "${module} is not loaded" >&2
    exit 2
  fi
}

attach() {
  require_loaded
  mkdir -p "$(dirname "$state")"
  {
    printf 'tracer=%s\n' "$(cat "$tracefs/current_tracer")"
    printf 'filter=%s\n' "$(cat "$tracefs/set_ftrace_filter" 2>/dev/null || true)"
  } > "$state"

  echo 0 > "$tracefs/tracing_on"
  : > "$tracefs/trace"
  echo nop > "$tracefs/current_tracer"
  : > "$tracefs/set_ftrace_filter"
  {
    echo qfox_record
    echo qfox_record_from_buffer
    echo qfox_dev_read
    echo qfox_dev_write
    echo qfox_netdev_event
    echo qfox_reboot_event
  } > "$tracefs/set_ftrace_filter"
  echo function_graph > "$tracefs/current_tracer"
  echo 1 > "$tracefs/tracing_on"

  if [[ -w /sys/kernel/debug/dynamic_debug/control ]]; then
    # Harmless when there are no pr_debug callsites; useful if added later.
    echo "module ${module} +p" > /sys/kernel/debug/dynamic_debug/control || true
  fi

  echo "attached ${module} ftrace debugger"
  echo "trace: $tracefs/trace"
}

detach() {
  echo 0 > "$tracefs/tracing_on"
  echo nop > "$tracefs/current_tracer"
  : > "$tracefs/set_ftrace_filter"
  if [[ -f "$state" ]]; then
    # Restoring arbitrary previous filters can be surprising; keep this
    # conservative and leave the prior state recorded for inspection.
    echo "previous ftrace state preserved at $state"
  fi
  echo "detached ${module} ftrace debugger"
}

snapshot() {
  require_loaded
  echo "--- module ---"
  modinfo "$module" || true
  echo "--- sysfs/status ---"
  cat "/sys/kernel/${module}/status" 2>/dev/null || cat "/sys/kernel/qfox_topology_manager/status"
  echo "--- sysfs/slots ---"
  cat "/sys/kernel/${module}/slots" 2>/dev/null || cat "/sys/kernel/qfox_topology_manager/slots"
  echo "--- debugfs/events ---"
  cat "/sys/kernel/debug/${module}/events" 2>/dev/null || cat "/sys/kernel/debug/qfox_topology_manager/events" 2>/dev/null || true
  echo "--- ftrace tail ---"
  tail -n 80 "$tracefs/trace" 2>/dev/null || true
}

case "$cmd" in
  attach) attach ;;
  detach) detach ;;
  snapshot) snapshot ;;
  *)
    echo "usage: $0 {attach|snapshot|detach}" >&2
    exit 2
    ;;
esac
