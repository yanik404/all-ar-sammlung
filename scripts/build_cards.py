#!/usr/bin/env python3
import json, re, subprocess, tempfile, shutil
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

UPSTREAM = 'https://github.com/type-null/PTCG-database.git'
BULBA_URL = 'https://bulbapedia.bulbagarden.net/wiki/Illustration_rare_card_(TCG)'
BULBA_API_URL = 'https://bulbapedia.bulbagarden.net/w/api.php?action=parse&page=Illustration_rare_card_(TCG)&prop=text&format=json'
OUT = Path(__file__).resolve().parents[1] / 'data' / 'cards.json'
REFERENCE_CACHE = Path(__file__).resolve().parents[1] / 'data' / 'art_rare_reference.json'
M_PROMO_IMAGE_FILES = {
    '101':'BulbasaurMEPPromo37.jpg','102':'CharmanderMEPPromo38.jpg','103':'SquirtleMEPPromo39.jpg',
    '104':'ChikoritaMEPPromo46.jpg','105':'CyndaquilMEPPromo47.jpg','106':'TotodileMEPPromo48.jpg',
    '107':'TreeckoMEPPromo55.jpg','108':'TorchicMEPPromo56.jpg','109':'MudkipMEPPromo57.jpg',
    '110':'TurtwigMEPPromo40.jpg','111':'ChimcharMEPPromo41.jpg','112':'PiplupMEPPromo42.jpg',
    '113':'SnivyMEPPromo49.jpg','114':'TepigMEPPromo50.jpg','115':'OshawottMEPPromo51.jpg',
    '116':'ChespinMEPPromo58.jpg','117':'FennekinMEPPromo59.jpg','118':'FroakieMEPPromo60.jpg',
    '119':'RowletMEPPromo43.jpg','120':'LittenMEPPromo44.jpg','121':'PopplioMEPPromo45.jpg',
    '122':'GrookeyMEPPromo52.jpg','123':'ScorbunnyMEPPromo53.jpg','124':'SobbleMEPPromo54.jpg',
    '125':'SprigatitoMEPPromo61.jpg','126':'FuecocoMEPPromo62.jpg','127':'QuaxlyMEPPromo63.jpg',
}
M_PROMO_IMAGE_URLS = {
    '101':'https://archives.bulbagarden.net/media/upload/3/32/BulbasaurMEPPromo37.jpg', '102':'https://archives.bulbagarden.net/media/upload/b/b3/CharmanderMEPPromo38.jpg', '103':'https://archives.bulbagarden.net/media/upload/e/e9/SquirtleMEPPromo39.jpg',
    '104':'https://archives.bulbagarden.net/media/upload/4/41/ChikoritaMEPPromo46.jpg', '105':'https://archives.bulbagarden.net/media/upload/f/fb/CyndaquilMEPPromo47.jpg', '106':'https://archives.bulbagarden.net/media/upload/8/8c/TotodileMEPPromo48.jpg',
    '107':'https://archives.bulbagarden.net/media/upload/3/38/TreeckoMEPPromo55.jpg', '108':'https://archives.bulbagarden.net/media/upload/a/a8/TorchicMEPPromo56.jpg', '109':'https://archives.bulbagarden.net/media/upload/6/63/MudkipMEPPromo57.jpg',
    '110':'https://archives.bulbagarden.net/media/upload/b/ba/TurtwigMEPPromo40.jpg', '111':'https://archives.bulbagarden.net/media/upload/d/de/ChimcharMEPPromo41.jpg', '112':'https://archives.bulbagarden.net/media/upload/5/5f/PiplupMEPPromo42.jpg',
    '113':'https://archives.bulbagarden.net/media/upload/2/2f/SnivyMEPPromo49.jpg', '114':'https://archives.bulbagarden.net/media/upload/c/c2/TepigMEPPromo50.jpg', '115':'https://archives.bulbagarden.net/media/upload/0/02/OshawottMEPPromo51.jpg',
    '116':'https://archives.bulbagarden.net/media/upload/b/bb/ChespinMEPPromo58.jpg', '117':'https://archives.bulbagarden.net/media/upload/5/5b/FennekinMEPPromo59.jpg', '118':'https://archives.bulbagarden.net/media/upload/5/50/FroakieMEPPromo60.jpg',
    '119':'https://archives.bulbagarden.net/media/upload/5/5b/RowletMEPPromo43.jpg', '120':'https://archives.bulbagarden.net/media/upload/9/92/LittenMEPPromo44.jpg', '121':'https://archives.bulbagarden.net/media/upload/9/9c/PopplioMEPPromo45.jpg',
    '122':'https://archives.bulbagarden.net/media/upload/4/48/GrookeyMEPPromo52.jpg', '123':'https://archives.bulbagarden.net/media/upload/e/e5/ScorbunnyMEPPromo53.jpg', '124':'https://archives.bulbagarden.net/media/upload/3/37/SobbleMEPPromo54.jpg',
    '125':'https://archives.bulbagarden.net/media/upload/d/d6/SprigatitoMEPPromo61.jpg', '126':'https://archives.bulbagarden.net/media/upload/8/81/FuecocoMEPPromo62.jpg', '127':'https://archives.bulbagarden.net/media/upload/d/d9/QuaxlyMEPPromo63.jpg',
}

# Bulbapedia Japanese expansion label -> official Japanese set code used by pokemon-card.com
SET_MAP = {
    'VSTAR Universe':'S12a','Scarlet ex':'SV1S','Violet ex':'SV1V','Triplet Beat':'SV1a',
    'Snow Hazard':'SV2P','Clay Burst':'SV2D','Pokémon Card 151':'SV2a','Ruler of the Black Flame':'SV3',
    'Raging Surf':'SV3a','Ancient Roar':'SV4K','Future Flash':'SV4M','Shiny Treasure ex':'SV4a',
    'Wild Force':'SV5K','Cyber Judge':'SV5M','Crimson Haze':'SV5a','Transformation Mask':'SV6',
    'Night Wanderer':'SV6a','Stellar Miracle':'SV7','Paradise Dragona':'SV7a','Super Electric Breaker':'SV8',
    'Terastal Festival ex':'SV8a','Battle Partners':'SV9','Hot Wind Arena':'SV9a','Glory of the Rocket Gang':'SV10',
    'Black Bolt':'SV11B','White Flare':'SV11W','Mega Brave':'M1L','Mega Symphonia':'M1S',
    'Inferno X':'M2','MEGA Dream ex':'M2a','Mega Dream ex':'M2a','Nihil Zero':'M3','Ninja Spinner':'M4',
    'Abyss Eye':'M5','Storm Emeralda':'M6',
    'SV-P Promotional cards':'SV-P','M-P Promotional cards':'M-P',
}

def norm(s):
    return re.sub(r'\s+',' ',s.replace('\xa0',' ')).strip()

def fetch_bulba_rows():
    req = Request(BULBA_API_URL, headers={'User-Agent':'Mozilla/5.0 (compatible; AllARCollection/1.0; +https://github.com/yanik404/all-ar-sammlung)'})
    try:
        payload = json.loads(urlopen(req, timeout=60).read())
        html = payload['parse']['text']['*'].encode('utf-8')
    except (HTTPError, URLError) as exc:
        # GitHub-hosted runners can be blocked by Bulbapedia. The checked-in
        # reference snapshot preserves English names and only verified promos.
        cached = json.loads(REFERENCE_CACHE.read_text(encoding='utf-8'))
        name_map = {tuple(key.split('|', 1)): value for key, value in cached['names'].items()}
        promo_keys = {tuple(key.split('|', 1)) for key in cached['promo_keys']}
        print(f'WARN live Art Rare reference unavailable; using verified snapshot: {exc}')
        return name_map, promo_keys, {}
    soup = BeautifulSoup(html, 'html.parser')
    name_map = {}
    promo_keys = set()
    source_meta = {}
    for table in soup.find_all('table'):
        # Skip Trainer Gallery / CHR tables completely.
        h = table.find_previous(['h2','h3'])
        heading = norm(h.get_text(' ', strip=True)) if h else ''
        if 'Trainer Gallery' in heading:
            continue
        for tr in table.find_all('tr'):
            cells = tr.find_all(['td','th'])
            if len(cells) < 7:
                continue
            vals = [norm(c.get_text(' ', strip=True)) for c in cells]
            card_name = vals[0]
            jp_exp = vals[-3]
            jp_num = vals[-1]
            if not card_name or not jp_exp or not jp_num:
                continue
            # numbers: 079/078, 193/SV-P, 105/M-P, etc.
            m = re.search(r'(\d{1,3})\s*/\s*([A-Za-z0-9-]+)', jp_num)
            if not m:
                continue
            numerator = str(int(m.group(1))).zfill(3)
            set_code = SET_MAP.get(jp_exp)
            if not set_code:
                continue
            key = (set_code, numerator)
            name_map[key] = card_name
            source_meta[key] = {'bulbapedia_expansion': jp_exp, 'bulbapedia_number': jp_num}
            if set_code.endswith('-P'):
                promo_keys.add(key)
    return name_map, promo_keys, source_meta

def clone_upstream(dest: Path):
    subprocess.run(['git','clone','--depth','1','--filter=blob:none','--sparse',UPSTREAM,str(dest)], check=True)
    subprocess.run(['git','-C',str(dest),'sparse-checkout','set','data_jp'], check=True)

def load_records(root: Path):
    by_key = {}
    ar = []
    for p in (root/'data_jp').glob('*/*.json'):
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        set_code = str(d.get('set_name') or '')
        num = str(d.get('number') or '')
        if not set_code or not num:
            continue
        num3 = str(int(num)).zfill(3) if num.isdigit() else num
        by_key[(set_code,num3)] = d
        if d.get('rarity') == 'rare_ar':
            ar.append(d)
    return by_key, ar

def card_obj(d, name_en, kind, meta):
    num = str(d.get('number') or '')
    total = str(d.get('set_total') or '')
    display_num = f'{num}/{total}' if total and total != d.get('set_name') else (f'{num}/{total}' if total else num)
    return {
        'id': d.get('print_key') or f"asia:{d.get('set_name')}-{num}",
        'set_code': d.get('set_name'),
        'set_name': meta.get('bulbapedia_expansion') or d.get('set_name'),
        'number': num,
        'number_display': meta.get('bulbapedia_number') or display_num,
        'name': name_en or d.get('name'),
        'name_ja': d.get('name'),
        'rarity': 'AR' if kind == 'AR' else 'AR Promo',
        'kind': kind,
        'image': d.get('img'),
        'source_url': d.get('url'),
        'jp_id': d.get('jp_id') or 0,
    }

def archive_image_url(filename):
    redirect = 'https://archives.bulbagarden.net/wiki/Special:Redirect/file/' + filename
    try:
        return urlopen(Request(redirect, headers={'User-Agent':'AllARCollection/1.0'}), timeout=30).geturl()
    except (HTTPError, URLError) as exc:
        print(f'WARN archive image redirect unavailable for {filename}: {exc}')
        return redirect

def main():
    names, promo_keys, source_meta = fetch_bulba_rows()
    tmp = Path(tempfile.mkdtemp(prefix='allar-upstream-'))
    try:
        clone_upstream(tmp)
        by_key, ar_records = load_records(tmp)
        cards = []
        seen = set()
        # True official Japanese AR rarity only.
        for d in ar_records:
            num = str(d.get('number') or '')
            num3 = str(int(num)).zfill(3) if num.isdigit() else num
            key = (str(d.get('set_name') or ''), num3)
            obj = card_obj(d, names.get(key), 'AR', source_meta.get(key, {}))
            cards.append(obj); seen.add(obj['id'])
        # Promo cards explicitly associated with Illustration/Art Rare on Bulbapedia.
        for key in sorted(promo_keys):
            d = by_key.get(key)
            if not d:
                if key[0] == 'M-P' and key[1] in M_PROMO_IMAGE_FILES:
                    number = key[1]
                    cards.append({
                        'id': f'promo:M-P-{number}', 'set_code': 'M-P',
                        'set_name': '30th CELEBRATION Card Set', 'number': number,
                        'number_display': f'{number}/M-P', 'name': names.get(key, number),
                        'name_ja': '', 'rarity': 'AR Promo', 'kind': 'AR Promo',
                        'image': M_PROMO_IMAGE_URLS[number],
                        'source_url': BULBA_URL, 'jp_id': 1000000 + int(number),
                    })
                    continue
                print('WARN promo not found upstream:', key)
                continue
            obj = card_obj(d, names.get(key), 'AR Promo', source_meta.get(key, {}))
            if obj['id'] not in seen:
                cards.append(obj); seen.add(obj['id'])
        # Registration order is a reliable fallback until exact per-card promo dates are enriched.
        cards.sort(key=lambda c: (c['kind'] == 'AR Promo', int(c.get('jp_id') or 0), c['set_code'], int(c['number']) if str(c['number']).isdigit() else 9999))
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({'generated_from': {'official_jp':'type-null/PTCG-database (pokemon-card.com)','art_rare_reference':BULBA_URL}, 'count': len(cards), 'cards': cards}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Wrote {len(cards)} verified AR/AR-promo cards -> {OUT}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    main()
