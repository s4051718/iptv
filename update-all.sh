#!/bin/bash

# 1. Cleanup
rm -rf ./playlists/*.m3u
rm -rf ./temp/*.m3u
mkdir -p temp playlists

# Function to update python config and run generator
generate() {
    local region=$1
    local category=$2
    local start_ch=$3
    local filename="plutotv_${region}_${category}.txt"
    
    echo "Generating: $filename (Ch: $start_ch)"

    # Update the python file
    sed -E -i "s/^[[:space:]]*CHANNELS_LIST_FILE[[:space:]]*=[[:space:]]*\".*\"/CHANNELS_LIST_FILE = \"$filename\"/" generate_playlist.py
    sed -E -i "s/^[[:space:]]*TARGET_REGIONS[[:space:]]*=[[:space:]]*\[.*\]/TARGET_REGIONS = ['$region']/" generate_playlist.py
    sed -E -i "s/^[[:space:]]*START_CH_NO[[:space:]]*=.*$/START_CH_NO = $start_ch/" generate_playlist.py
    
    # Run the script
    python3 generate_playlist.py
    
    # Move result to temp
    mv playlists/plutotv_custom.m3u "temp/plutotv_${region}_${category}.m3u"
}

# 2. RUN GENERATIONS
# FILM
generate "gb" "film" 100
generate "ca" "film" 200
generate "us" "film" 300

# TV
generate "gb" "tv" 400
generate "ca" "tv" 500
generate "us" "tv" 600

# SERIES
generate "gb" "series" 700
generate "ca" "series" 800
generate "us" "series" 900

# KIDS
generate "gb" "kids" 1000
generate "ca" "kids" 1100
generate "us" "kids" 1200

# 3. STITCH FILES TOGETHER
EPG_URL="https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/all.xml.gz"

for region in gb ca us; do
    MASTER="playlists/plutotv_${region}_master.m3u"
    
    # Create header (Fixed the double #EXTM3U bug in your original)
    echo "#EXTM3U url-tvg=\"$EPG_URL\"" > "$MASTER"
    
    # Append files for this specific region
    # Check if files exist first to avoid errors
    if ls temp/*${region}*.m3u >/dev/null 2>&1; then
        for f in temp/*${region}*.m3u; do
            grep -v '#EXTM3U' "$f" >> "$MASTER"
        done
        echo "Created $MASTER"
    fi
done

echo "All master playlists created successfully."