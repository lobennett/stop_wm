#!/bin/bash
#
# Download the raw data from the RDoC server.

# Check if EF_DOWNLOAD_KEY environment variable is set or ef_download file exists
if [ -n "$EF_DOWNLOAD_KEY" ]; then
    # Write the key to a temporary file
    echo "$EF_DOWNLOAD_KEY" > ef_download_temp
    chmod 600 ef_download_temp
    KEY_FILE="ef_download_temp"
    CLEANUP=true
elif [ -f ef_download ]; then
    KEY_FILE="$(dirname "$0")/ef_download"
    CLEANUP=false
else
    echo "Error: Neither ef_download file nor EF_DOWNLOAD_KEY environment variable found"
    exit 1
fi

# Create SSH config for host key bypass
mkdir -p ~/.ssh
echo "StrictHostKeyChecking no" > ~/.ssh/config
chmod 600 ~/.ssh/config

# Download the raw data from the RDoC server
rsync -avh --progress --stats -e "ssh -i $KEY_FILE -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" download@52.41.81.29:~/results_export ./raw_data

# Clean up temporary file if created
if [ "$CLEANUP" = true ]; then
    rm ef_download_temp
fi