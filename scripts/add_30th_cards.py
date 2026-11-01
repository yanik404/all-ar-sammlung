#!/usr/bin/env python3
"""Preserve the 2026 30th Celebration additions after the regular AR rebuild.

Only explicit Japanese card numbers are added. When the upstream Japanese
database contains the exact print, use its official image. Otherwise show
a labeled image placeholder instead of a broken/misidentified card image.
"""
import json
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cards.json"
IMAGE_MANIFEST = ROOT / "data" / "recent_image_sources.json"
BUNDLED_IMAGES = json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8")) if IMAGE_MANIFEST.exists() else {}
NAMES = [
    ("Alolan Exeggutor", "アローラナッシー"), ("Moltres", "ファイヤー"),
    ("Lapras", "ラプラス"), ("Articuno", "フリーザー"),
    ("Zapdos", "サンダー"), ("Toxtricity", "ストリンダー"),
    ("Morpeko", "モルペコ"), ("Drifloon", "フワンテ"),
    ("Chandelure", "シャンデラ"), ("Lycanroc", "ルガルガン"),
    ("Nidorina", "ニドリーナ"), ("Alolan Meowth", "アローラニャース"),
    ("Scraggy", "ズルッグ"), ("Galarian Meowth", "ガラルニャース"),
    ("Gholdengo", "サーフゴー"), ("Kommo-o", "ジャラランガ"),
    ("Meowth", "ニャース"), ("Ditto", "メタモン"),
    ("Hisuian Zorua", "ヒスイゾロア"), ("Maushold", "イッカネズミ"),
]
EXTRA = [
    ("MF", 41, "Victini", "ビクティニ", 50591),
    ("MF", 42, "Zeraora", "ゼラオラ", 50592),
]

def placeholder(name, number):
    from html import escape
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="630" height="880">'
           '<rect width="630" height="880" fill="#1e293b"/>'
           '<rect x="24" y="24" width="582" height="832" rx="24" fill="#29384e" stroke="#94a3b8"/>'
           f'<text x="315" y="375" text-anchor="middle" font-family="Arial" font-size="29" fill="white">{escape(name)}</text>'
           f'<text x="315" y="435" text-anchor="middle" font-family="Arial" font-size="27" fill="white">{number}</text>'
           '<text x="315" y="490" text-anchor="middle" font-family="Arial" font-size="22" fill="#93c5fd">Kartenbild folgt</text>'
           '</svg>')
    return 'data:image/svg+xml;charset=utf-8,' + quote(svg, safe='')

def upstream_records():
    root = Path(tempfile.mkdtemp(prefix="allar-30th-"))
    try:
        subprocess.run(["git","clone","--depth","1","--filter=blob:none","--sparse",
                        "https://github.com/type-null/PTCG-database.git",str(root)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git","-C",str(root),"sparse-checkout","set","data_jp"],
                       check=True, stdout=subprocess.DEVNULL)
        records = {}
        for code in ("M6a","MF"):
            for path in (root/"data_jp"/code).glob("*.json"):
                try:
                    d = json.loads(path.read_text(encoding="utf-8"))
                    n = str(d.get("number") or "")
                    if n.isdigit():
                        records[(code,int(n))] = d
                except (ValueError, OSError):
                    pass
        return records
    except Exception as e:
        print(f"WARN upstream images unavailable; keeping labeled placeholders: {e}")
        return {}
    finally:
        shutil.rmtree(root, ignore_errors=True)

def main():
    payload=json.loads(OUT.read_text(encoding="utf-8"))
    cards=payload["cards"]
    by_key={(c["set_code"],int(c["number"])):c for c in cards if str(c.get("number","")).isdigit()}
    upstream=upstream_records()
    for num,(name,ja) in enumerate(NAMES,104):
        insert(by_key,upstream,"M6a",num,name,ja,"AR",f"{num}/103",
               "30th CELEBRATION",None)
    for code,num,name,ja,official_id in EXTRA:
        insert(by_key,upstream,code,num,name,ja,"AR Promo",
               f"{num:03d}/040","30th CELEBRATION Premium Deck Set Espeon & Umbreon",
               official_id)
    # Fix the existing mislabel; 073/071 SV5K is Snom, not Bronzor.
    if ("SV5K",73) in by_key:
        by_key[("SV5K",73)]["name"]="Snom"
    cards=list(by_key.values())
    cards.sort(key=lambda c:(c.get("kind")=="AR Promo",
             int(c.get("jp_id") or 0),c.get("set_code",""),int(c.get("number") or 0)))
    payload["cards"]=cards
    payload["count"]=len(cards)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"30th update: {len(cards)} cards, {sum(bool(c.get('image_status')) for c in cards)} image placeholders")

def insert(by_key,upstream,code,num,name,ja,kind,display,set_name,official_id):
    d=upstream.get((code,num),{})
    old=by_key.get((code,num),{})
    bundled=BUNDLED_IMAGES.get(f"{code}-{num:03d}", {})
    image=bundled.get("image") or d.get("img") or old.get("image")
    if bundled and not (ROOT / image).is_file():
        raise RuntimeError(f"Bundled card image missing: {image}")
    if not image or image.startswith("data:"):
        image=placeholder(name,display)
        image_status="placeholder_pending_official_image"
    else:
        image_status=None
    url=d.get("url") or old.get("source_url") or bundled.get("source_url")
    if official_id:
        url=f"https://www.pokemon-card.com/card-search/details.php/card/{official_id}"
    obj={**old,
        "id":old.get("id") or d.get("print_key") or f"asia:{code}-{num}",
        "set_code":code,"set_name":set_name,
        "number":f"{num:03d}","number_display":display,
        "name":name,"name_ja":ja,"rarity":kind,"kind":kind,
        "image":image,
        "source_url":url or "https://www.pokemon-card.com/card-search/",
        "jp_id":d.get("jp_id") or old.get("jp_id") or (800000+num)}
    if bundled:
        obj["image_source_url"]=bundled["image_source_url"]
    if image_status: obj["image_status"]=image_status
    else: obj.pop("image_status",None)
    by_key[(code,num)]=obj

if __name__=="__main__":
    main()
