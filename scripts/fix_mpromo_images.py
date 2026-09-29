#!/usr/bin/env python3
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'data' / 'cards.json'
BASE = 'https://www.30th.pokemon-card.com/images/cardset/cards/'
FILES = {
    '101':'promo_101_aumftuat.png','102':'promo_102_pt9obsca.png','103':'promo_103_4ewh05a9.png',
    '104':'promo_104_0hjzlyap.png','105':'promo_105_d69y7lqp.png','106':'promo_106_cn01nfwy.png',
    '107':'promo_107_fo9kbv0z.png','108':'promo_108_w8uo5010.png','109':'promo_109_tddzzzgs.png',
    '110':'promo_110_8vcdtj1b.png','111':'promo_111_k6lf6kih.png','112':'promo_112_omlkqn9k.png',
    '113':'promo_113_hu6x7wmd.png','114':'promo_114_n28qwgxs.png','115':'promo_115_mnrfal5b.png',
    '116':'promo_116_ot4rv5w3.png','117':'promo_117_4wk6z26d.png','118':'promo_118_s38jcptz.png',
    '119':'promo_119_7t38ep1y.png','120':'promo_120_f25bwe3z.png','121':'promo_121_4bs8bu09.png',
    '122':'promo_122_k336sfa5.png','123':'promo_123_m073z7hq.png','124':'promo_124_nth0rgfs.png',
    '125':'promo_125_b775ygf7.png','126':'promo_126_i1s034lw.png','127':'promo_127_m6p8f3c0.png',
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
        url = BASE + FILES[number]
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
