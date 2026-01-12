import requests, gzip, json, os, logging, uuid, time, shutil
from io import BytesIO

# --- Configuration ---
OUTPUT_DIR = "playlists"
CHANNELS_LIST_FILE = "plutotv_us_kids.txt"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 30 

# FEATURE 1: Specify exactly which regions to scrape
TARGET_REGIONS = ['us'] 

# FEATURE 2: Specify the starting channel number
START_CH_NO = 1200

REGION_MAP = {
    'us': 'United States', 'gb': 'United Kingdom', 'ca': 'Canada',
    'de': 'Germany', 'at': 'Austria', 'ch': 'Switzerland',
    'es': 'Spain', 'fr': 'France', 'it': 'Italy', 'br': 'Brazil',
    'mx': 'Mexico', 'ar': 'Argentina', 'cl': 'Chile', 'co': 'Colombia',
    'pe': 'Peru', 'se': 'Sweden', 'no': 'Norway', 'dk': 'Denmark',
    'in': 'India', 'jp': 'Japan', 'kr': 'South Korea', 'au': 'Australia'
}

TOP_REGIONS = ['United States', 'Canada', 'United Kingdom']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions (Preserved) ---

def cleanup_output_dir():
    if os.path.exists(OUTPUT_DIR):
        logging.info(f"Cleaning up old playlists in {OUTPUT_DIR}...")
        for filename in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logging.error(f"Failed to delete {file_path}: {e}")
    else:
        os.makedirs(OUTPUT_DIR)

def fetch_url(url, is_json=True, is_gzipped=False, headers=None, stream=False, retries=3):
    headers = headers or {'User-Agent': USER_AGENT}
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, stream=stream)
            if response.status_code == 429:
                time.sleep((i + 1) * 10)
                continue
            response.raise_for_status()
            content = response.content
            if is_gzipped:
                with gzip.GzipFile(fileobj=BytesIO(content), mode='rb') as f:
                    content = f.read()
            content = content.decode('utf-8')
            return json.loads(content) if is_json else content
        except Exception as e:
            if i < retries - 1: time.sleep(2)
    return None

def write_m3u_file(filename, content):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def format_extinf(channel_id, tvg_id, tvg_chno, tvg_name, tvg_logo, group_title, display_name):
    return (f'#EXTINF:-1 channel-id="{channel_id}" tvg-id="{tvg_id}" tvg-chno="{tvg_chno}" '
            f'tvg-name="{tvg_name.replace(chr(34), chr(39))}" tvg-logo="{tvg_logo}" '
            f'group-title="{group_title.replace(chr(34), chr(39))}",{display_name.replace(",", "")}\n')

# --- Service Generator ---

def generate_pluto_m3u():
    data = fetch_url('https://github.com/matthuisman/i.mjh.nz/raw/refs/heads/master/PlutoTV/.channels.json.gz', is_json=True, is_gzipped=True)
    if not data or 'regions' not in data: return
    
    keywords = []
    if os.path.exists(CHANNELS_LIST_FILE):
        with open(CHANNELS_LIST_FILE, 'r', encoding='utf-8') as f:
            keywords = [line.strip().lower() for line in f if line.strip()]

    if not keywords:
        logging.info("!!! DISCOVERY MODE: Listing names for target regions...")
        for r_code in TARGET_REGIONS:
            r_data = data['regions'].get(r_code, {})
            print(f"\n--- {r_code.upper()} ---")
            for c_id, c_info in sorted(r_data.get('channels', {}).items(), key=lambda x: x[1]['name']):
                print(c_info['name'])
        with open(CHANNELS_LIST_FILE, 'w') as f: pass 
        return

    # Initialization for the global playlist
    # We use 'all' for the EPG to cover the merged regions
    epg_url = 'https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/all.xml.gz'
    output_lines = [f'#EXTM3U url-tvg="{epg_url}"\n']
    
    current_chno = START_CH_NO
    channels_added = 0

    # We iterate only through the TARGET_REGIONS
    for r_code in TARGET_REGIONS:
        r_data = data['regions'].get(r_code, {})
        display_group = REGION_MAP.get(r_code.lower(), r_code.upper())
        
        region_channels = r_data.get('channels', {})
        # Sorting channels by name within the region
        sorted_keys = sorted(region_channels.keys(), key=lambda k: region_channels[k]['name'])

        for c_id in sorted_keys:
            c_info = region_channels[c_id]
            if any(k in c_info['name'].lower() for k in keywords):
                # Use our custom numbering instead of the default JSON one
                extinf = format_extinf(f"{c_id}-{r_code}", c_id, current_chno, c_info['name'], c_info['logo'], f"Pluto {display_group}", c_info['name'])
                
                url = (f'https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/{c_id}/master.m3u8'
                       f'?advertisingId=channel&appName=web&appVersion=9.1.2&deviceDNT=0&deviceId={uuid.uuid4()}'
                       f'&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=126.0.0&sid={uuid.uuid4()}'
                       f'&userId=&serverSideAds=true|User-Agent={USER_AGENT}\n')
                
                output_lines.extend([extinf, url])
                current_chno += 1
                channels_added += 1
    
    if channels_added > 0:
        write_m3u_file("plutotv_custom.m3u", "".join(output_lines))
        logging.info(f"Generated plutotv_custom.m3u with {channels_added} channels starting at {START_CH_NO}.")

if __name__ == "__main__":
    cleanup_output_dir()
    generate_pluto_m3u()
    logging.info("Process complete.")