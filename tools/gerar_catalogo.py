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
THUMB_W = 240          # largura da miniatura (os cartoes tem ~150-200 px)
THUMB_MAX_FRAMES = 120
THUMB_GEN = 2           # muda quando o jeito de gerar miniaturas muda (forca regerar) # miniatura animada: no maximo isso de quadros (pula quadros e soma a duracao)


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9_-]+', '-', s).strip('-')
    return (s or 'fundo')[:64]


def split_tags(stem):
    """'Nezuko Kamado [demon slayer, fogo]' -> ('Nezuko Kamado', ['demon slayer', 'fogo'])"""
    m = re.match(r'^(.*?)\s*\[([^\]]*)\]\s*$', stem)
    if not m:
        return stem, []
    return m.group(1), [t.strip() for t in m.group(2).split(',') if t.strip()][:8]


def title(stem):
    t = re.sub(r'[-_]+', ' ', stem).strip()
    # nome escrito pelo usuario (com maiusculas) fica como esta; senao so a 1a letra maiuscula
    return t if t != t.lower() else t.capitalize()


def webp_durations(path):
    """Duracao (ms) de cada quadro de um WEBP animado, lida direto dos blocos ANMF (o Pillow nem sempre informa)."""
    out = []
    with open(path, 'rb') as f:
        head = f.read(12)
        if head[:4] != b'RIFF' or head[8:12] != b'WEBP':
            return out
        while True:
            h = f.read(8)
            if len(h) < 8:
                break
            tag, size = h[:4], int.from_bytes(h[4:], 'little')
            if tag == b'ANMF':
                payload = f.read(16)
                out.append(int.from_bytes(payload[12:15], 'little'))
                f.seek(size - 16 + (size & 1), 1)
            else:
                f.seek(size + (size & 1), 1)
    return out


def make_thumb(im, frames, dest, durations=None):
    """Miniatura: animada quando o fundo e animado (mesmo movimento, menor e mais leve)."""
    if frames <= 1:
        im.seek(0); t = im.convert('RGB'); t.thumbnail((THUMB_W, THUMB_W * 2)); t.save(dest, 'WEBP', quality=78, method=6); return
    step = max(1, -(-frames // THUMB_MAX_FRAMES))
    out, durs = [], []
    for i in range(0, frames, step):
        dur = 0
        for j in range(i, min(i + step, frames)):
            dur += (durations[j] if durations and j < len(durations) and durations[j] > 0 else int(im.info.get('duration') or 40))
        im.seek(i); t = im.convert('RGB'); t.thumbnail((THUMB_W, THUMB_W * 2))
        out.append(t); durs.append(max(20, dur))
    out[0].save(dest, 'WEBP', save_all=True, append_images=out[1:], duration=durs, loop=0, quality=60, method=4)


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
        stem, file_tags = split_tags(fn[:-5])
        fid = slug(stem)
        while fid in used:
            fid += '-2'
        used.add(fid)
        try:
            im = Image.open(src); w, h = im.size
            frames = getattr(im, 'n_frames', 1)
        except Exception as e:
            print('ignorado (nao e WEBP valido):', fn, e, file=sys.stderr); continue
        v = sha(src)
        thumb = f'{fid}.webp'
        tpath = os.path.join(THUMBS, thumb)
        if old.get(fid, {}).get('v') != v or old.get(fid, {}).get('tg') != THUMB_GEN or not os.path.exists(tpath):
            make_thumb(im, frames, tpath, webp_durations(src))
        keep_thumbs.add(thumb)
        m = meta.get(fid) or meta.get(stem) or meta.get(fn[:-5]) or {}
        items.append({
            'id': fid, 'name': m.get('name') or title(stem),
            'file': 'fundos/' + fn, 'thumb': 'thumbs/' + thumb, 'v': v, 'tv': sha(tpath), 'tg': THUMB_GEN,
            'author': m.get('author', ''), 'tags': m.get('tags') or file_tags,
            'added': old.get(fid, {}).get('added') or today,
            'bytes': os.path.getsize(src), 'width': w, 'height': h, 'animated': frames > 1,
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
