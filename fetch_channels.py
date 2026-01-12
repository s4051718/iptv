import requests
import gzip
import json
import logging
from io import BytesIO

# --- Configuration ---
# Only look at the regions you care about
TARGET_REGIONS = ['us', 'gb', 'ca'] 
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

REGION_NAMES = {
    'us': 'UNITED STATES',
    'gb': 'UNITED KINGDOM',
    'ca': 'CANADA'
}

logging.basicConfig(level=logging.INFO, format='%(message)s')

def fetch_data():
    url = 'https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/PlutoTV/.channels.json.gz'
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        with gzip.GzipFile(fileobj=BytesIO(response.content), mode='rb') as f:
            return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        logging.error(f"Error connecting to Pluto source: {e}")
        return None

def enumerate_channels():
    data = fetch_data()
    if not data or 'regions' not in data:
        return

    print("="*60)
    print("      PLUTO TV CHANNEL EXPLORER (Targeted Regions)")
    print("="*60)
    print("Copy the names below and paste them into your channels.txt file.")

    total_count = 0

    for r_code in TARGET_REGIONS:
        r_data = data['regions'].get(r_code, {})
        region_display = REGION_NAMES.get(r_code, r_code.upper())
        
        channels = r_data.get('channels', {})
        if not channels:
            continue

        print(f"\n[ {region_display} ] - {len(channels)} Channels Available")
        print("-" * 40)

        # Sort alphabetically so it's easier to browse
        sorted_channels = sorted(channels.values(), key=lambda x: x['name'].lower())
        
        for ch in sorted_channels:
            print(f"{ch['name']}")
            total_count += 1

    print("\n" + "="*60)
    print(f"Total Channels Found across {len(TARGET_REGIONS)} regions: {total_count}")
    print("="*60)

if __name__ == "__main__":
    enumerate_channels()