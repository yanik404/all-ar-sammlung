#!/usr/bin/env python3
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'data' / 'cards.json'
ROOT = OUT.parents[1]
IMAGE_MANIFEST = OUT.parent / 'recent_image_sources.json'
BUNDLED_IMAGES = json.loads(IMAGE_MANIFEST.read_text(encoding='utf-8')) if IMAGE_MANIFEST.exists() else {}
BASE = 'https://www.30th.pokemon-card.com/images/cardset/cards/'
FILES = {
    '101':'promo_101_aumftuat.webp','102':'promo_102_pt9obsca.webp','103':'promo_103_4ewh05a9.webp',
    '104':'promo_104_0hjzlyap.webp','105':'promo_105_d69y7lqp.webp','106':'promo_106_cn01nfwy.webp',
    '107':'promo_107_fo9kbv0z.webp','108':'promo_108_w8uo5010.webp','109':'promo_109_tddzzzgs.webp',
    '110':'promo_110_8vcdtj1b.webp','111':'promo_111_k6lf6kih.webp','112':'promo_112_omlkqn9k.webp',
    '113':'promo_113_hu6x7wmd.webp','114':'promo_114_n28qwgxs.webp','115':'promo_115_mnrfal5b.webp',
    '116':'promo_116_ot4rv5w3.webp','117':'promo_117_4wk6z26d.webp','118':'promo_118_s38jcptz.webp',
    '119':'promo_119_7t38ep1y.webp','120':'promo_120_f25bwe3z.webp','121':'promo_121_4bs8bu09.webp',
    '122':'promo_122_k336sfa5.webp','123':'promo_123_m073z7hq.webp','124':'promo_124_nth0rgfs.webp',
    '125':'promo_125_b775ygf7.webp','126':'promo_126_i1s034lw.webp','127':'promo_127_m6p8f3c0.webp',
}

def main():
    data = json.loads(OUT.read_text(encoding='utf-8'))
    changed = 0
    found = set()
    for card in data.get('cards', []):
        if card.get('set_code') != 'M-P':
            continue
        number = str(card.get('number') or '').zfill(3)
        if number not in FILES:
            continue
        found.add(number)
        bundled = BUNDLED_IMAGES.get(f'M-P-{number}', {})
        url = bundled.get('image') or BASE + FILES[number]
        if bundled:
            if not (ROOT / url).is_file():
                raise RuntimeError(f'Missing bundled promo image: {url}')
            card['image_source_url'] = bundled['image_source_url']
        if card.get('image') != url:
            card['image'] = url
            card['source_url'] = 'https://www.30th.pokemon-card.com/product/cardset'
            changed += 1
    missing = sorted(set(FILES)-found)
    if missing:
        raise RuntimeError('Missing M-P cards in cards.json: ' + ', '.join(missing))
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Updated {changed} M-P promo image URLs to official pokemon-card.com 30th assets')

if __name__ == '__main__':
    main()
