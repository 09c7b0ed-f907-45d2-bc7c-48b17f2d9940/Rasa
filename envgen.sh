#!/bin/sh

CONFIG_FILE="envgen.config"
TARGET_DIR="."
OUTPUT_FILE=".env"

# Function to generate a sample config file if it doesn't exist
generate_config() {
    cat > "$CONFIG_FILE" <<EOF
# Extension | Regex Pattern      | Description
.yml        | \\\${([A-Z_][A-Z0-9_]*)[:?-]?.*?} | YAML config files
EOF
    echo "[+] Config file generated: $CONFIG_FILE"
}

# Function to print usage
usage() {
    echo "Usage: $0 [-d target_directory]"
    exit 1
}

# Parse options (-d <directory>) (-f <output file>) (-c <config file>)
while getopts "d:h" opt; do
    case "$opt" in
        d) TARGET_DIR="$OPTARG" ;;
        f) OUTPUT_FILE="$OPTARG" ;;
        c) CONFIG_FILE="$OPTARG" ;;
        h) usage ;;
        ?) usage ;;
    esac
done

echo "envgen.sh not yet implemented, would scan $TARGET_DIR based on $CONFIG_FILE to find environment variables and create a template env file called $OUTPUT_FILE"