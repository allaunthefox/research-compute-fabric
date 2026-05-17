#!/bin/sh
podman run -it --rm \
  --dns 100.101.247.127 --dns 1.1.1.1 --dns 8.8.8.8 \
  research-stack:latest "$@"
