"""Kemas kini data/kedai.json daripada suapan RSS kedai Etsy The SEN Corner.

Dijalankan oleh .github/workflows/kedai-etsy.yml. Fail hanya ditulis semula jika
senarai produk berubah, dan tidak disentuh langsung jika suapan gagal dibaca.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://www.etsy.com/shop/TheSENCorner/rss"
OUT = Path(__file__).resolve().parent.parent / "data" / "kedai.json"
LISTING = re.compile(r"^https://www\.etsy\.com/listing/(\d+)(/[a-z0-9-]*)?")
IMAGE = re.compile(r'<img[^>]+src="(https://i\.etsystatic\.com/[^"]+)"')


def fetch():
    req = urllib.request.Request(FEED, headers={
        "User-Agent": "Mozilla/5.0 (compatible; nazieraaziz.com shop sync)",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(xml_bytes):
    items = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        title = (it.findtext("title") or "").strip()
        title = re.sub(r"\s+by TheSENCorner$", "", title, flags=re.I)
        link = LISTING.match((it.findtext("link") or "").strip())
        if not title or not link:
            continue
        img = IMAGE.search(html.unescape(it.findtext("description") or ""))
        date = it.findtext("pubDate")
        items.append({
            "id": link.group(1),
            "tajuk": title,
            "pautan": f"https://www.etsy.com/listing/{link.group(1)}{link.group(2) or ''}",
            "gambar": img.group(1) if img else "",
            "tarikh": parsedate_to_datetime(date).isoformat() if date else "",
        })
    items.sort(key=lambda p: p["tarikh"], reverse=True)
    return items


def main():
    try:
        items = parse(fetch())
    except Exception as e:  # suapan gagal: kekalkan data sedia ada
        print(f"Gagal membaca suapan Etsy: {e}", file=sys.stderr)
        return 1
    if not items:
        print("Suapan Etsy kosong; data sedia ada dikekalkan.", file=sys.stderr)
        return 1
    old = json.loads(OUT.read_text()) if OUT.exists() else None
    if old == items:
        print(f"Tiada perubahan ({len(items)} produk).")
        return 0
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    print(f"data/kedai.json dikemas kini: {len(items)} produk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
