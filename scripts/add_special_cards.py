#!/usr/bin/env python3
"""Add verified Japanese illustration cards from special decks/products.

These cards belong to the Illustration/Art Rare reference list, but some official
pokemon-card.com records do not carry the normal `rare_ar` field. Keeping them
in this explicit allow-list prevents ordinary deck cards, Energy, SR/SAR/CHR,
etc. from leaking into All AR.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

UPSTREAM = "https://github.com/type-null/PTCG-database.git"
OUT = Path(__file__).resolve().parents[1] / "data" / "cards.json"

# (official Japanese set code, card number): (English name, display set, printed number)
# Verified against the Japanese card database (pokemon-card.com data) and the
# Bulbapedia Illustration Rare reference list.
SPECIAL = {
    ("SVG", "050"): ("Bulbasaur", "Special Deck Set ex Venusaur & Charizard & Blastoise", "050/049"),
    ("SVG", "051"): ("Charmander", "Special Deck Set ex Venusaur & Charizard & Blastoise", "051/049"),
    ("SVG", "052"): ("Squirtle", "Special Deck Set ex Venusaur & Charizard & Blastoise", "052/049"),
    ("SVOM", "020"): ("Marnie's Morpeko", "ex Starter Set Marnie's Morpeko & Grimmsnarl ex", "020/019"),
    ("SVOD", "019"): ("Steven's Beldum", "ex Starter Set Steven's Beldum & Metagross ex", "019/018"),
    ("MEM", "018"): ("Sprigatito", "ex Starter Set Sprigatito & Meowscarada ex", "018/017"),
    ("MEE", "020"): ("Eevee", "ex Starter Set Eevee ex", "020/019"),
    ("MEZ", "020"): ("Zorua", "ex Starter Set Zorua & Zoroark ex", "020/019"),
    ("MBD", "022"): ("Meloetta", "MEGA Starter Set Mega Diancie ex", "022/021"),
    ("MBG", "022"): ("Haunter", "MEGA Starter Set Mega Gengar ex", "022/021"),
    ("MC", "743"): ("Erika's Tangela", "Start Deck 100 Battle Collection", "743/742"),
    ("MC", "744"): ("Salazzle", "Start Deck 100 Battle Collection", "744/742"),
    ("MC", "745"): ("Scorbunny", "Start Deck 100 Battle Collection", "745/742"),
    ("MC", "746"): ("Weavile", "Start Deck 100 Battle Collection", "746/742"),
    ("MC", "747"): ("Vikavolt", "Start Deck 100 Battle Collection", "747/742"),
    ("MC", "748"): ("Marill", "Start Deck 100 Battle Collection", "748/742"),
    ("MC", "749"): ("Banette", "Start Deck 100 Battle Collection", "749/742"),
    ("MC", "750"): ("Slurpuff", "Start Deck 100 Battle Collection", "750/742"),
    ("MC", "751"): ("Hitmontop", "Start Deck 100 Battle Collection", "751/742"),
    ("MC", "752"): ("Carbink", "Start Deck 100 Battle Collection", "752/742"),
    ("MC", "753"): ("Mightyena", "Start Deck 100 Battle Collection", "753/742"),
    ("MC", "754"): ("Mawile", "Start Deck 100 Battle Collection", "754/742"),
    ("MC", "755"): ("Eevee", "Start Deck 100 Battle Collection", "755/742"),
    ("MC", "756"): ("Larry's Staraptor", "Start Deck 100 Battle Collection", "756/742"),
    ("SV-P", "192"): ("Meowth", "SV-P Promotional cards", "192/SV-P"),
    ("SV-P", "193"): ("Paldean Wooper", "SV-P Promotional cards", "193/SV-P"),
    ("SV-P", "232"): ("Iono's Wattrel", "SV-P Promotional cards", "232/SV-P"),
}


def clone_upstream(dest: Path):
    subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", UPSTREAM, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "data_jp"], check=True)


def load_matching(root: Path):
    wanted = set(SPECIAL)
    found = {}
    for path in (root / "data_jp").glob("*/*.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        set_code = str(d.get("set_name") or "")
        number = str(d.get("number") or "")
        if not number.isdigit():
            continue
        key = (set_code, str(int(number)).zfill(3))
        if key in wanted:
            found[key] = d
    missing = sorted(wanted - set(found))
    if missing:
        raise RuntimeError("Verified special cards missing from upstream: " + ", ".join(f"{s} {n}" for s, n in missing))
    return found


def to_card(key, d):
    name, set_name, number_display = SPECIAL[key]
    number = str(d.get("number") or "")
    return {
        "id": d.get("print_key") or f"asia:{key[0]}-{number}",
        "set_code": key[0],
        "set_name": set_name,
        "number": number,
        "number_display": number_display,
        "name": name,
        "name_ja": d.get("name") or "",
        "rarity": "AR Promo",
        "kind": "AR Promo",
        "image": d.get("img"),
        "source_url": d.get("url"),
        "jp_id": d.get("jp_id") or 0,
    }


def main():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    cards = data.get("cards", [])
    seen = {c.get("id") for c in cards}

    tmp = Path(tempfile.mkdtemp(prefix="allar-special-upstream-"))
    try:
        clone_upstream(tmp)
        found = load_matching(tmp)
        added = 0
        for key in SPECIAL:
            obj = to_card(key, found[key])
            if obj["id"] in seen:
                continue
            cards.append(obj)
            seen.add(obj["id"])
            added += 1

        # Keep the app's existing split: official set AR first, associated/special
        # illustration cards in the dedicated promo/special binder area.
        cards.sort(key=lambda c: (
            c.get("kind") == "AR Promo",
            int(c.get("jp_id") or 0),
            str(c.get("set_code") or ""),
            int(c.get("number")) if str(c.get("number") or "").isdigit() else 9999,
        ))
        data["cards"] = cards
        data["count"] = len(cards)
        sources = data.setdefault("generated_from", {})
        sources["special_illustration_allowlist"] = "Bulbapedia Illustration Rare reference + pokemon-card.com Japanese records"
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Added {added} missing verified special illustration cards; total {len(cards)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
