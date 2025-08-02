#!/bin/bash
# wait-for-it.sh
# Script to wait for a service to become available
# Based on the popular wait-for-it script

# Default values
host=""
port=""
timeout=30
strict=false
quiet=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        *:* )
            hostport=(${1//:/ })
            host=${hostport[0]}
            port=${hostport[1]}
            shift
            ;;
        -h|--help)
            echo "Usage: wait-for-it.sh host:port [-s] [-t timeout] [-- command args]"
            echo "  -s, --strict         Only execute subcommand if the test succeeds"
            echo "  -q, --quiet          Don't output any status messages"
            echo "  -t, --timeout=timeout  Timeout in seconds, zero for no timeout"
            echo "  -- command args       Execute command with args after the test finishes"
            exit 0
            ;;
        -s|--strict)
            strict=true
            shift
            ;;
        -q|--quiet)
            quiet=true
            shift
            ;;
        -t)
            timeout="$2"
            shift 2
            ;;
        --timeout=*)
            timeout="${1#*=}"
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Check if host and port are set
if [[ -z "$host" || -z "$port" ]]; then
    echo "Error: you need to provide a host and port to test." >&2
    exit 1
fi

# Convert timeout to integer
timeout=${timeout:-30}

# Function to check if the service is available
check_service() {
    if command -v nc &> /dev/null; then
        nc -z "$host" "$port"
    elif command -v bash &> /dev/null; then
        (echo > /dev/tcp/"$host"/"$port") >/dev/null 2>&1
    else
        echo "Error: nc (netcat) not found and bash is not available" >&2
        return 1
    fi
}

# Wait for the service to become available
start_ts=$(date +%s)
while :
do
    if check_service; then
        end_ts=$(date +%s)
        if [ "$quiet" = false ]; then
            echo "Service is available after $((end_ts - start_ts)) seconds"
        fi
        break
    else
        current_ts=$(date +%s)
        if [ $timeout -gt 0 ] && [ $((current_ts - start_ts)) -gt $timeout ]; then
            if [ "$quiet" = false ]; then
                echo "Timeout occurred after waiting $timeout seconds for $host:$port"
            fi
            if [ "$strict" = true ]; then
                exit 1
            else
                exit 0
            fi
        fi
        sleep 1
    fi
done

# Execute the command if provided
if [ $# -gt 0 ]; then
    exec "$@"
fi
