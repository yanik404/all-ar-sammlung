#!/usr/bin/env python3
import re
from urllib.request import Request, urlopen
from urllib.parse import urljoin

URL='https://www.30th.pokemon-card.com/product/cardset'
html=urlopen(Request(URL,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','ignore')
print('HTML',len(html))
# Print every likely card/promo asset URL or path.
vals=set()
for m in re.finditer(r'''(?:src|href|data-src|data-original|srcset)\s*=\s*["']([^"']+)["']''',html,re.I):
    v=m.group(1)
    if any(x in v.lower() for x in ['promo','cardset','card_set','card-set','101','102','103','104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120','121','122','123','124','125','126','127']):
        vals.add(urljoin(URL,v.split()[0]))
for v in sorted(vals): print('ASSET',v)
# Also show local context around promo_### patterns if present.
for n in range(101,128):
    for pat in [f'promo_{n}',f'promo-{n}',f'promo{n}',str(n)]:
        i=html.lower().find(pat.lower())
        if i!=-1:
            print('CTX',n,html[max(0,i-180):i+260].replace('\n',' '))
            break
