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

# Raging Surf SV3a AR cards 063/062–074/062, confirmed by Limitless.
# The upstream rarity feed currently omits these; keep a verified fallback.
RAGING_SURF_FALLBACK = {
    '063': ('Snorunt', 'ユキワラシ'),
    '064': ('Mantyke', 'タマンタ'),
    '065': ('Plusle', 'プラスル'),
    '066': ('Minun', 'マイナン'),
    '067': ('Joltik', 'バチュル'),
    '068': ('Gimmighoul', 'コレクレー'),
    '069': ('Groudon', 'グラードン'),
    '070': ('Minior', 'メテノ'),
    '071': ('Yveltal', 'イベルタル'),
    '072': ('Ferrothorn', 'ナットレイ'),
    '073': ('Aegislash', 'ギルガルド'),
    '074': ('Cyclizar', 'モトトカゲ'),
}

# Independently checked numbering of all released Japanese AR sets.
# If an upstream feed omits an entire set, stop the build instead of
# publishing an incomplete binder. New sets should be added to this baseline.
REQUIRED_AR_RANGES = {
    'S12a': (173, 209),
    'SV1S': (79, 90), 'SV1V': (79, 90), 'SV1a': (74, 85),
    'SV2P': (72, 83), 'SV2D': (72, 83), 'SV2a': (166, 183),
    'SV3': (109, 120), 'SV3a': (63, 74),
    'SV4K': (67, 78), 'SV4M': (67, 78), 'SV4a': (338, 341),
    'SV5K': (72, 83), 'SV5M': (72, 83), 'SV5a': (67, 78),
    'SV6': (102, 113), 'SV6a': (65, 76), 'SV7': (103, 114),
    'SV7a': (65, 76), 'SV8': (107, 118),
    # SV8a / Terastal Festival ex has 0 AR cards.
    'SV9': (101, 112), 'SV9a': (64, 75), 'SV10': (99, 110),
    'SV11B': (87, 158), 'SV11W': (87, 158),
    'M1L': (64, 75), 'M1S': (64, 75), 'M2': (81, 92),
    'M2a': (194, 213), 'M3': (81, 92), 'M4': (84, 95),
    'M5': (82, 93), 'M6': (77, 88), 'M6a': (104, 123),
}
REQUIRED_PROMO_NUMBERS = {
    'M-P': list(range(101, 128)),
    'MC': list(range(743, 757)),
    'SVG': [50, 51, 52],
    'SV-P': [1, 48, 49, 98, 148, 192, 193, 218, 232],
    'SVOM': [20], 'SVOD': [19], 'MBG': [22], 'MBD': [22],
    'MEE': [20], 'MEZ': [20], 'MEM': [18], 'MF': [41, 42],
}

def validate_known_collection(cards):
    seen = set()
    for card in cards:
        set_code = str(card.get('set_code') or '')
        number = str(card.get('number') or '')
        card_key = (set_code, number.lstrip('0') or '0')
        if card_key in seen:
            raise RuntimeError(f'Duplicate card number for the same set: {card_key}')
        seen.add(card_key)
        if not card.get('image') or not card.get('name') or not card.get('id'):
            raise RuntimeError(f'Incomplete card record: {card_key}')
    by_kind = {
        kind: {(str(c['set_code']), int(c['number'])) for c in cards
               if c['kind'] == kind and str(c['number']).isdigit()}
        for kind in ('AR', 'AR Promo')
    }
    errors = []
    for set_code, (first, last) in REQUIRED_AR_RANGES.items():
        missing = [str(n).zfill(3) for n in range(first, last + 1)
                   if (set_code, n) not in by_kind['AR']]
        if missing:
            errors.append(f'{set_code}: missing AR cards {", ".join(missing)}')
    for set_code, numbers in REQUIRED_PROMO_NUMBERS.items():
        missing = [str(n).zfill(3) for n in numbers
                   if (set_code, n) not in by_kind['AR Promo']]
        if missing:
            errors.append(f'{set_code}: missing AR promo cards {", ".join(missing)}')
    if errors:
        raise RuntimeError('Incomplete verified AR checklist:\\n' + '\\n'.join(errors))

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
        # Fallback only for the 12 independently verified Raging Surf ARs
        # missing from the upstream rarity feed (not for arbitrary card numbers).
        existing_raging_numbers = {
            str(int(c['number'])) for c in cards
            if c['set_code'] == 'SV3a' and c['kind'] == 'AR'
        }
        for number, (name_en, name_ja) in RAGING_SURF_FALLBACK.items():
            if str(int(number)) in existing_raging_numbers:
                continue
            n = int(number)
            cards.append({
                'id': f'asia:SV3a-{n}',
                'set_code': 'SV3a',
                'set_name': 'Raging Surf',
                'number': str(n),
                'number_display': f'{number}/062',
                'name': names.get(('SV3a', number), name_en),
                'name_ja': name_ja,
                'rarity': 'AR',
                'kind': 'AR',
                'image': f'https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/tpc/SV3a/SV3a_{n}_R_JP.png',
                'source_url': f'https://www.pokemon-card.com/card-search/details.php/card/{44379 + n - 63}',
                'jp_id': 44379 + (n - 63),
            })
        # Registration order for normal cards / promo dates.
        cards.sort(key=lambda c: (c['kind'] == 'AR Promo', int(c.get('jp_id') or 0), c['set_code'], int(c['number']) if str(c['number']).isdigit() else 9999))
        # Fallback entries have no official JP ID: keep SV3a between SV3 and SV4.
        surf = [c for c in cards if c['kind'] == 'AR' and c['set_code'] == 'SV3a']
        if surf:
            cards = [c for c in cards if not (c['kind'] == 'AR' and c['set_code'] == 'SV3a')]
            before_sv4 = next((i for i, c in enumerate(cards)
                               if c['kind'] == 'AR' and c['set_code'] in ('SV4K', 'SV4M')), len(cards))
            cards[before_sv4:before_sv4] = sorted(surf, key=lambda c: int(c['number']))
        validate_known_collection(cards)
        # Safety check: an upstream parsing problem must never silently erase
        # previously verified cards (including whole sets or promo groups).
        if OUT.exists():
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            old_cards = {c['id']: c for c in previous.get('cards', [])}
            new_cards = {c['id']: c for c in cards}
            vanished = sorted(set(old_cards) - set(new_cards))
            changed_kind = sorted(
                card_id for card_id in old_cards.keys() & new_cards.keys()
                if old_cards[card_id].get('kind') != new_cards[card_id].get('kind')
            )
            if vanished or changed_kind:
                raise RuntimeError(
                    'Card data check failed; refusing to overwrite verified collection. '
                    f'Missing cards: {vanished[:20]} (total {len(vanished)}). '
                    f'Changed rarity category: {changed_kind[:20]} '
                    f'(total {len(changed_kind)}).'
                )
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({'generated_from': {'official_jp':'type-null/PTCG-database (pokemon-card.com)','art_rare_reference':BULBA_URL}, 'count': len(cards), 'cards': cards}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Wrote {len(cards)} verified AR/AR-promo cards -> {OUT}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    main()
