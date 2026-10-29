#!/usr/bin/env python3
"""Gera catalog.json e as miniaturas a partir da pasta fundos/.

Roda sozinho no GitHub (Actions) a cada envio; tambem pode rodar no PC: python tools/gerar_catalogo.py
Informacoes extras (nome, autor, tags) ficam opcionais em fundos.json:
  { "sakura-noite": { "name": "Sakura à noite", "author": "Fulano", "tags": ["japão", "noite"] } }
"""
import hashlib, json, os, re, sys, unicodedata
from datetime import datetime, timezone
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDOS, THUMBS = os.path.join(ROOT, 'fundos'), os.path.join(ROOT, 'thumbs')
CATALOG, META = os.path.join(ROOT, 'catalog.json'), os.path.join(ROOT, 'fundos.json')
THUMB_W = 360


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9_-]+', '-', s).strip('-')
    return (s or 'fundo')[:64]


def title(stem):
    return re.sub(r'[-_]+', ' ', stem).strip().capitalize()


def sha(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()[:10]


def main():
    os.makedirs(FUNDOS, exist_ok=True); os.makedirs(THUMBS, exist_ok=True)
    old = {}
    if os.path.exists(CATALOG):
        try:
            old = {x['id']: x for x in json.load(open(CATALOG, encoding='utf-8')).get('backgrounds', [])}
        except Exception:
            pass
    meta = json.load(open(META, encoding='utf-8')) if os.path.exists(META) else {}
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    items, used, keep_thumbs = [], set(), set()
    for fn in sorted(os.listdir(FUNDOS)):
        src = os.path.join(FUNDOS, fn)
        if not fn.lower().endswith('.webp') or not os.path.isfile(src):
            continue
        stem = fn[:-5]
        fid = slug(stem)
        while fid in used:
            fid += '-2'
        used.add(fid)
        try:
            im = Image.open(src); w, h = im.size
            im.seek(0); im = im.convert('RGB')
        except Exception as e:
            print('ignorado (nao e WEBP valido):', fn, e, file=sys.stderr); continue
        v = sha(src)
        thumb = f'{fid}.webp'
        tpath = os.path.join(THUMBS, thumb)
        if old.get(fid, {}).get('v') != v or not os.path.exists(tpath):
            t = im.copy(); t.thumbnail((THUMB_W, THUMB_W * 2)); t.save(tpath, 'WEBP', quality=78, method=6)
        keep_thumbs.add(thumb)
        m = meta.get(fid) or meta.get(stem) or {}
        items.append({
            'id': fid, 'name': m.get('name') or old.get(fid, {}).get('name') or title(stem),
            'file': 'fundos/' + fn, 'thumb': 'thumbs/' + thumb, 'v': v,
            'author': m.get('author', ''), 'tags': m.get('tags', []),
            'added': old.get(fid, {}).get('added') or today,
            'bytes': os.path.getsize(src), 'width': w, 'height': h,
        })
    for f in os.listdir(THUMBS):
        if f.endswith('.webp') and f not in keep_thumbs:
            os.remove(os.path.join(THUMBS, f))
    items.sort(key=lambda x: (x['added'], x['id']), reverse=True)  # mais novos primeiro
    cat = {'version': 1, 'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'backgrounds': items}
    prev = json.load(open(CATALOG, encoding='utf-8')) if os.path.exists(CATALOG) else {}
    if prev.get('backgrounds') == items:
        print('catalogo sem mudancas'); return
    json.dump(cat, open(CATALOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'catalog.json: {len(items)} fundo(s)')


if __name__ == '__main__':
    main()
