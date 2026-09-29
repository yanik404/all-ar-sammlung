#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA = Path(__file__).resolve().parents[1] / 'data' / 'cards.json'
UA = 'Mozilla/5.0 (compatible; AllARCollectionImageAudit/1.0)'

def check(card):
    url = card.get('image') or ''
    if not url:
        return card, 'missing-url'
    try:
        req = Request(url, headers={'User-Agent': UA, 'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})
        with urlopen(req, timeout=20) as r:
            status = getattr(r, 'status', 200)
            ctype = (r.headers.get('Content-Type') or '').lower()
            # Read a little so redirects/edge failures surface.
            r.read(64)
            if status >= 400:
                return card, f'http-{status}'
            if ctype and 'image' not in ctype and 'octet-stream' not in ctype:
                return card, f'content-type:{ctype}'
            return card, None
    except HTTPError as e:
        return card, f'http-{e.code}'
    except URLError as e:
        return card, f'urlerror:{e.reason}'
    except Exception as e:
        return card, f'{type(e).__name__}:{e}'

def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    cards = data.get('cards', [])
    bad = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(check, c) for c in cards]
        for fut in as_completed(futs):
            card, err = fut.result()
            if err:
                bad.append((card, err))
    bad.sort(key=lambda x: (x[0].get('set_code',''), str(x[0].get('number',''))))
    print(f'Checked {len(cards)} card images; broken={len(bad)}')
    for c, err in bad:
        print(f"BROKEN\t{c.get('id')}\t{c.get('name')}\t{c.get('set_code')} {c.get('number_display')}\t{err}\t{c.get('image')}")
    if bad:
        sys.exit(1)

if __name__ == '__main__':
    main()
