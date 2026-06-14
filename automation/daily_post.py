#!/usr/bin/env python3
"""
mentviro Daily Instagram Automation
=====================================
RUN_MODE env var controls what gets posted:
  carousel  → evening carousel post + attached story   (18:00 CET)
  reel      → morning reel post + attached story        (07:00 CET)
  stories   → standalone quote story + tips story       (12:00 CET)

Content generated as daily pairs (1 reel + 1 carousel + 1 story-pair per day).
Engagement tracked, trends fetched, optimal posting times analysed.
"""

import os, sys, json, io, time, random, requests, base64, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Windows cp1252 stdout breaks on non-ASCII characters (arrows, umlauts in log lines).
# Force UTF-8 output so print() never crashes the whole script.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Cross-platform temp dir
TMPDIR   = tempfile.gettempdir()
RUN_MODE = os.getenv("RUN_MODE", "carousel")   # carousel | reel | stories
# DRY_RUN: rendert + lädt zur Vorschau auf Cloudinary hoch, postet aber NICHT auf
# Instagram und markiert den Post NICHT als 'published'. Für sichere Test-Reels.
DRY_RUN  = os.getenv("DRY_RUN", "").strip().lower() in ("1", "true", "yes", "on")

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PLAN_FILE = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_FILE = os.path.join(os.path.dirname(__file__), "assets", "mentviro_logo.png")
LOGO_URL  = os.getenv("MENTVIRO_LOGO_URL", "")
_LOGO_B64 = ""

W, H   = 1080, 1350   # carousel / single image (4:5)
SW, SH = 1080, 1920   # story / reel (9:16)

# Optimal post times (CET) based on research — updated over time via engagement data
# Reel: 07:00  |  Stories: 12:00  |  Carousel: 18:00
SCHEDULE = {"reel": "07:00", "stories": "12:00", "carousel": "18:00"}

# ─── PLAN ────────────────────────────────────────────────────────────────────

def load_plan():
    with open(PLAN_FILE, encoding='utf-8-sig') as f:  # utf-8-sig handles BOM transparently
        return json.load(f)

def save_plan(plan):
    with open(PLAN_FILE, "w", encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

def get_todays_post(plan, post_type: str):
    """Return today's pending post of the given type, or next pending if none today.
    Guards against duplicate posting: skips posts published within last 6h."""
    today = date.today().isoformat()
    # Hard guard: if today's post was already published recently, never re-post
    for post in plan["posts"]:
        if post["date"] == today and post.get("type") == post_type and post["status"] == "published":
            pub = post.get("published_at", "")
            if pub:
                try:
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    age_h  = (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600
                    if age_h < 6:
                        print(f"  {post_type} for {today} already published {age_h:.1f}h ago — skipping.")
                        return None
                except Exception:
                    pass
    for post in plan["posts"]:
        if post["date"] == today and post["status"] == "pending" and post.get("type") == post_type:
            return post
    for post in plan["posts"]:
        if post["status"] == "pending" and post.get("type") == post_type:
            return post
    return None

def get_todays_stories(plan):
    """Return today's pending story-pair, or next pending if none today.
    Guards against duplicate posting: skips stories published within last 6h."""
    today = date.today().isoformat()
    sq = plan.get("story_queue", [])
    # Hard guard: if today's story was already published recently, never re-post
    for s in sq:
        if s["date"] == today and s["status"] == "published":
            pub = s.get("published_at", "")
            if pub:
                try:
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    age_h  = (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600
                    if age_h < 6:
                        print(f"  Stories for {today} already published {age_h:.1f}h ago — skipping.")
                        return None
                except Exception:
                    pass
    for s in sq:
        if s["date"] == today and s["status"] == "pending":
            return s
    for s in sq:
        if s["status"] == "pending":
            return s
    return None

# ─── TELEGRAM ────────────────────────────────────────────────────────────────

def send_telegram(message: str):
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass

# ─── META GRAPH API ──────────────────────────────────────────────────────────

GRAPH_API  = "https://graph.instagram.com/v21.0"
IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_TOKEN   = os.environ.get("IG_ACCESS_TOKEN", "")
CDN_CLOUD  = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CDN_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "")

def cloudinary_upload(data: bytes, resource_type: str = "image", suffix: str = ".jpg") -> str:
    """Upload image/video bytes to Cloudinary. Returns public HTTPS URL."""
    if not CDN_CLOUD or not CDN_PRESET:
        raise RuntimeError("CLOUDINARY_CLOUD_NAME / CLOUDINARY_UPLOAD_PRESET nicht gesetzt")
    mime  = "image/jpeg" if resource_type == "image" else "video/mp4"
    fname = f"mentviro_{int(time.time())}{suffix}"
    r = requests.post(
        f"https://api.cloudinary.com/v1_1/{CDN_CLOUD}/{resource_type}/upload",
        files={"file": (fname, data, mime)},
        data={"upload_preset": CDN_PRESET, "folder": "mentviro"},
        timeout=180,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Cloudinary upload failed: {r.status_code} {r.text[:300]}")
    url = r.json().get("secure_url", "")
    print(f"  CDN: {url.split('/')[-1]}")
    return url

def ig_create_container(*, image_url: str = None, video_url: str = None,
                         caption: str = None, media_type: str = "IMAGE",
                         is_carousel_item: bool = False) -> str:
    """Create an IG media container. Returns container ID."""
    if not IG_TOKEN or not IG_USER_ID:
        raise RuntimeError("IG_ACCESS_TOKEN / IG_USER_ID nicht gesetzt")
    params: dict = {"access_token": IG_TOKEN, "media_type": media_type}
    if image_url:
        params["image_url"] = image_url
    if video_url:
        params["video_url"] = video_url
    if caption:
        params["caption"] = caption
    if is_carousel_item:
        params["is_carousel_item"] = "true"
    r = requests.post(f"{GRAPH_API}/{IG_USER_ID}/media", data=params, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ig_create_container ({media_type}): {r.status_code} {r.text}")
    return r.json()["id"]

def ig_create_carousel_container(child_ids: list, caption: str) -> str:
    """Create a carousel parent container. Returns container ID."""
    params = {
        "access_token": IG_TOKEN,
        "media_type":   "CAROUSEL",
        "children":     ",".join(child_ids),
        "caption":      caption,
    }
    r = requests.post(f"{GRAPH_API}/{IG_USER_ID}/media", data=params, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ig_create_carousel_container: {r.status_code} {r.text}")
    return r.json()["id"]

def ig_publish(container_id: str) -> str:
    """Publish a media container. Returns the live media ID."""
    r = requests.post(
        f"{GRAPH_API}/{IG_USER_ID}/media_publish",
        data={"access_token": IG_TOKEN, "creation_id": container_id},
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ig_publish: {r.status_code} {r.text}")
    return r.json()["id"]

def ig_wait_for_video(container_id: str, timeout_s: int = 300):
    """Poll until a video container is ready to publish (status=FINISHED)."""
    for _ in range(timeout_s // 10):
        r = requests.get(
            f"{GRAPH_API}/{container_id}",
            params={"fields": "status_code", "access_token": IG_TOKEN},
            timeout=30,
        )
        status = r.json().get("status_code", "IN_PROGRESS")
        print(f"  Video container status: {status}")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Video container error: {r.json()}")
        time.sleep(10)
    raise TimeoutError("Video container processing timed out")

def ig_get_insights(media_id: str) -> dict:
    """Fetch like/comment counts via Graph API."""
    r = requests.get(
        f"{GRAPH_API}/{media_id}",
        params={"fields": "like_count,comments_count", "access_token": IG_TOKEN},
        timeout=30,
    )
    if r.status_code != 200:
        return {}
    d = r.json()
    return {"likes": d.get("like_count", 0), "comments": d.get("comments_count", 0)}

def check_session_age():
    """Check if the IG access token needs refreshing (warn when < 10 days left)."""
    # Token expiry is stored locally after each refresh.
    # Since we can't query expiry from the env token, we refresh proactively each run.
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not token:
        send_telegram(
            "⚠️ <b>mentviro-bot</b>: IG_ACCESS_TOKEN nicht gesetzt!\n"
            "Bitte Token über Meta Developer Console erneuern und als GitHub Secret hinterlegen."
        )
        return
    # Attempt a lightweight API call to verify token is valid
    r = requests.get(
        f"{GRAPH_API}/{IG_USER_ID}",
        params={"fields": "id,name", "access_token": token},
        timeout=15,
    )
    if r.status_code == 200:
        print(f"  IG token valid — account: {r.json().get('name','?')}")
        # Proactively refresh to extend 60-day window
        ref = requests.get(
            "https://graph.instagram.com/refresh_access_token",
            params={"grant_type": "ig_refresh_token", "access_token": token},
            timeout=15,
        )
        if ref.status_code == 200:
            print("  IG token refreshed (60-day window extended)")
        else:
            print(f"  Token refresh skipped: {ref.status_code}")
    else:
        err = r.json().get("error", {})
        send_telegram(
            f"⛔ <b>mentviro-bot</b>: IG Access Token ungültig!\n"
            f"<code>{err.get('message','?')}</code>\n"
            "Bitte neuen Token generieren: developers.facebook.com → Graph API Explorer"
        )
        print(f"  IG token check FAILED: {r.status_code} {r.text[:200]}")

# ─── FONT ────────────────────────────────────────────────────────────────────

def fnt(size, bold=False):
    weight = "Bold" if bold else "Regular"
    candidates = [
        f"/usr/share/fonts/truetype/Montserrat-{weight}.ttf",
        f"/usr/local/share/fonts/Montserrat-{weight}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # extra fallback sans bold
        f"C:/Windows/Fonts/Montserrat-{weight}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        os.path.join(os.path.dirname(__file__), "assets", f"Montserrat-{weight}.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except (OSError, IOError):
                continue  # file exists but is invalid (e.g. failed download) — try next
    return ImageFont.load_default()

# ─── LOGO ────────────────────────────────────────────────────────────────────

_logo_cache = None

def get_logo_asset(size=90):
    global _logo_cache
    if _logo_cache and _logo_cache[0] == size:
        return _logo_cache[1]
    for src in [
        (lambda: Image.open(LOGO_FILE).convert("RGBA") if os.path.exists(LOGO_FILE) else None),
        (lambda: Image.open(io.BytesIO(base64.b64decode(_LOGO_B64))).convert("RGBA") if _LOGO_B64 else None),
        (lambda: Image.open(io.BytesIO(requests.get(LOGO_URL, timeout=10).content)).convert("RGBA") if LOGO_URL else None),
    ]:
        try:
            logo = src()
            if logo:
                logo.thumbnail((size, size), Image.LANCZOS)
                _logo_cache = (size, logo)
                return logo
        except Exception:
            pass
    # Fallback symbol
    sym = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(sym)
    s, col = size, (192, 192, 192, 140)
    lw = max(2, s // 22)
    for off in range(lw):
        d.ellipse([s*.04+off, s*.40+off, s*.96-off, s*.62-off], outline=col)
    pts = [(s*.18,s*.80),(s*.18,s*.20),(s*.50,s*.55),(s*.82,s*.20),(s*.82,s*.80)]
    d.line([(int(x), int(y)) for x, y in pts], fill=col, width=lw+1)
    ax2, ay2 = int(s*.90), int(s*.02)
    d.line([(int(s*.68), int(s*.22)), (ax2, ay2)], fill=col, width=lw)
    d.polygon([(ax2,ay2),(ax2-int(s*.12),ay2+int(s*.05)),(ax2-int(s*.04),ay2+int(s*.13))], fill=col)
    _logo_cache = (size, sym)
    return sym

def paste_logo(img_rgba, x, y, size=90):
    logo = get_logo_asset(size)
    img_rgba.alpha_composite(logo, (x - size // 2, y - size // 2))

# ─── COLORS ──────────────────────────────────────────────────────────────────

COLORS = None

def init_colors(plan):
    global COLORS
    c = plan["settings"]["colors"]
    COLORS = {
        "bg":     tuple(c["background"]),
        "white":  tuple(c["white"]),
        "silver": tuple(c["silver"]),
        "light":  tuple(c["light_silver"]),
        "dark":   tuple(c["dark_silver"]),
    }

# ─── DESIGN HELPERS ──────────────────────────────────────────────────────────

MARGIN = 90   # px — safe zone left & right, prevents text from touching edges

# ─── DESIGN VARIANTS ─────────────────────────────────────────────────────────
# Accent color alternates per post: silver (standard) vs gold (warm variant)
STYLE_ACCENTS = {
    "silver": (192, 192, 192),
    "gold":   (201, 168,  76),   # warm gold #C9A84C
}
_build_accent = (192, 192, 192)  # current accent — set via set_build_accent()

def set_build_accent(post_or_story):
    global _build_accent
    style = post_or_story.get("style", "silver") if isinstance(post_or_story, dict) else "silver"
    _build_accent = STYLE_ACCENTS.get(style, STYLE_ACCENTS["silver"])

def _strip_emoji(text: str) -> str:
    """Remove emoji/symbols fonts cannot render — Pillow draws box placeholders
    (white/black rectangles) for them."""
    import re
    # Remove characters outside BMP (U+10000+ — most emoji)
    text = re.sub("[\U00010000-\U0010FFFF]", "", text)
    # Remove BMP symbol blocks not in Latin fonts: Misc Symbols, Dingbats,
    # arrows/shapes, variation selectors, zero-width joiner
    text = re.sub("[\u2600-\u27BF\u2B00-\u2BFF\uFE00-\uFE0F\u200D]", "", text)
    return text.strip()

def text_width(text, font_size, bold=False):
    return fnt(font_size, bold).getbbox(_strip_emoji(text))[2]

def fit_font_size(text, max_width, start_size, bold=False, min_size=28):
    """Reduce font size until text fits within max_width pixels."""
    sz = start_size
    while sz > min_size and text_width(text, sz, bold) > max_width:
        sz -= 4
    return sz

def draw_base_frame(img_rgba, w=W, h=H, is_bw=False, slide_num=None, badge=None):
    d    = ImageDraw.Draw(img_rgba)
    ACC  = COLORS["white"] if is_bw else _build_accent
    BODY = (180, 180, 180) if is_bw else COLORS["dark"]
    d.rectangle([(0, 0), (w, 5)], fill=ACC)
    d.rectangle([(0, h-5), (w, h)], fill=ACC)
    d.text((MARGIN, 28), "MENTVIRO", font=fnt(28, True), fill=ACC)
    d.text((MARGIN, 62), "BUSINESS MINDSET", font=fnt(17), fill=BODY)
    d.rectangle([(MARGIN, 96), (w-MARGIN, 98)], fill=(70, 70, 70))
    if badge:
        d.text((MARGIN, 120), badge, font=fnt(30, True), fill=ACC)
    if slide_num:
        bb = fnt(26).getbbox(slide_num)
        d.text((w - MARGIN - (bb[2]-bb[0]), 124), slide_num, font=fnt(26), fill=BODY)
    d.rectangle([(MARGIN, h-120), (w-MARGIN, h-116)], fill=(60, 60, 60))
    d.text((MARGIN, h-100), "@mentviro", font=fnt(30, True), fill=COLORS["white"])
    # Logo komplett entfernt — Logo-PNG hat opaken Hintergrund → weißes Viereck auf allen Slides

def dark_overlay(base_rgb, w=W, h=H, strength=195):
    ov = Image.new("RGBA", (w, h))
    od = ImageDraw.Draw(ov)
    for y in range(h):
        a = int(strength - 30 + (y / h) * 30)
        od.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(base_rgb.convert("RGBA"), ov)

# ─── PEXELS ──────────────────────────────────────────────────────────────────

def pexels_portrait(query, target_w=W, target_h=H, exclude_ids: set = None):
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "orientation": "portrait", "per_page": 15, "size": "large"},
            timeout=30)
        if r.status_code != 200:
            return None
        photos = r.json().get("photos", [])
        if not photos:
            return None
        # Exclude already-used photos to avoid duplicates within the same carousel
        if exclude_ids:
            photos = [p for p in photos if p["id"] not in exclude_ids] or photos
        photo = random.choice(photos[:min(5, len(photos))])
        # Register this photo ID as used so subsequent calls skip it
        if exclude_ids is not None:
            exclude_ids.add(photo["id"])
        url   = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
        # Force JPEG format to avoid WEBP compatibility issues on Ubuntu
        if url and "?" not in url:
            url += "?auto=compress&cs=tinysrgb&fit=crop&fm=jpg"
        elif url:
            url += "&fm=jpg"
        img_resp = requests.get(url, timeout=30, headers={"Accept": "image/jpeg,image/*"})
        if img_resp.status_code != 200 or not img_resp.content:
            return None
        try:
            img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
        except Exception as e:
            print(f"  Pexels image decode error: {e}")
            return None
        sw, sh = img.size
        tr = target_w / target_h
        sr = sw / sh
        if sr > tr:
            nw = int(sh * tr); img = img.crop(((sw-nw)//2, 0, (sw-nw)//2+nw, sh))
        elif sr < tr:
            nh = int(sw / tr); img = img.crop((0, 0, sw, nh))
        return img.resize((target_w, target_h), Image.LANCZOS)
    except Exception as e:
        print(f"  Pexels error: {e}")
        return None

def pexels_video(query, pick_random=True):
    """Return a portrait MP4 URL from Pexels. pick_random=True returns a random result."""
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 8, "orientation": "portrait"},
            timeout=30)
        candidates = []
        for v in r.json().get("videos", []):
            # Prefer HD portrait files
            best = None
            for vf in sorted(v.get("video_files", []),
                             key=lambda x: x.get("height", 0), reverse=True):
                if "mp4" in vf.get("file_type", ""):
                    best = vf["link"]
                    break
            if best:
                candidates.append(best)
        if not candidates:
            return None
        return random.choice(candidates) if pick_random else candidates[0]
    except Exception as e:
        print(f"  Pexels video error: {e}")
    return None

# ─── CAROUSEL SLIDE BUILDER ──────────────────────────────────────────────────

def build_carousel_slide(slide, bg_img=None, w=W, h=H):
    is_cover = slide.get("is_cover", False)
    if bg_img is not None:
        bg  = bg_img.convert("L").convert("RGB") if is_cover else bg_img
        img = dark_overlay(bg, w=w, h=h, strength=198)
    elif is_cover:
        img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    else:
        img = Image.new("RGBA", (w, h), tuple(COLORS["bg"]) + (255,))

    draw_base_frame(img, w=w, h=h, is_bw=is_cover,
                    slide_num=slide.get("num"), badge=slide.get("badge"))
    d    = ImageDraw.Draw(img)
    BODY = (175, 175, 175)
    max_text_w = w - MARGIN * 2        # safe text width (never touch edges)
    content_top = 165 + (30 if slide.get("badge") else 0)
    if is_cover:
        # Kein Logo auf Slides (Logo-PNG hat opaken Hintergrund → weißes Viereck)
        content_top = int(h * 0.42)

    def _render_line(text, start_sz, bold, fill, max_y_limit):
        """Render text — strips emoji (no font support) and auto-wraps if too wide."""
        nonlocal y
        text = _strip_emoji(text)
        if not text:
            return
        sz = fit_font_size(text, max_text_w, start_sz, bold=bold)
        if text_width(text, sz, bold) <= max_text_w:
            # Fits on one line
            if y < max_y_limit:
                d.text((MARGIN, y), text, font=fnt(sz, bold), fill=fill)
            bb = fnt(sz, bold).getbbox(text)
            y += (bb[3] - bb[1]) + (14 if bold else 12)
        else:
            # Still too wide — split at spaces and render sub-lines
            words = text.split()
            current = []
            for word in words:
                test = " ".join(current + [word])
                if text_width(test, sz, bold) > max_text_w and current:
                    sub = " ".join(current)
                    if y < max_y_limit:
                        d.text((MARGIN, y), sub, font=fnt(sz, bold), fill=fill)
                    bb = fnt(sz, bold).getbbox(sub)
                    y += (bb[3] - bb[1]) + (14 if bold else 12)
                    current = [word]
                else:
                    current.append(word)
            if current:
                sub = " ".join(current)
                if y < max_y_limit:
                    d.text((MARGIN, y), sub, font=fnt(sz, bold), fill=fill)
                bb = fnt(sz, bold).getbbox(sub)
                y += (bb[3] - bb[1]) + (14 if bold else 12)

    y = content_top + 30
    bottom_safe = h - 130    # stop before footer separator line
    base_title_sz = 74 if not is_cover else 68
    # Uniform font size for ALL title lines on this slide — avoids size-jumping effect
    title_lines = slide.get("title", [])
    uniform_title_sz = base_title_sz
    for line in title_lines:
        uniform_title_sz = min(uniform_title_sz, fit_font_size(line, max_text_w, base_title_sz, bold=True))
    for line in title_lines:
        _render_line(line, uniform_title_sz, bold=True, fill=COLORS["white"], max_y_limit=bottom_safe)
    y += 36
    for line in slide.get("body", []):
        _render_line(line, 40, bold=False, fill=BODY, max_y_limit=bottom_safe)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

# ─── STORY BUILDERS ──────────────────────────────────────────────────────────

def build_attached_story(post):
    """Story that gets attached to a carousel/reel post."""
    query = (post.get("pexels_queries") or [post.get("pexels_video_query", "dark city cinematic")])[0]
    bg    = pexels_portrait(query, target_w=SW, target_h=SH) or Image.new("RGB", (SW, SH), (0,0,0))

    ov = Image.new("RGBA", (SW, SH))
    od = ImageDraw.Draw(ov)
    for y in range(SH):
        od.line([(0, y), (SW, y)], fill=(0, 0, 0, int(155 + (y / SH) * 80)))
    img = Image.alpha_composite(bg.convert("RGBA"), ov)
    d   = ImageDraw.Draw(img)
    SIL = _build_accent
    d.rectangle([(0, 0), (SW, 7)], fill=SIL)
    d.text((MARGIN, 55), "@mentviro", font=fnt(40, True), fill=SIL)
    d.rectangle([(MARGIN, 108), (MARGIN + 140, 115)], fill=SIL)

    texts = post.get("story_text", ["NEU", post.get("topic", ""), "Jetzt ansehen"])
    max_text_w = SW - MARGIN * 2
    y = SH // 2 - 60
    for j, line in enumerate(texts):
        line = _strip_emoji(line)
        sz   = 34 if j == 0 else (84 if j < len(texts)-1 else 46)
        bold = j > 0
        col  = SIL if j == 0 else (COLORS["white"] if j < len(texts)-1 else SIL)
        sz   = fit_font_size(line, max_text_w, sz, bold=bold)
        d.text((MARGIN, y), line, font=fnt(sz, bold), fill=col)
        bb = fnt(sz, bold).getbbox(line)
        y += (bb[3] - bb[1]) + 12
    d.rectangle([(0, SH-7), (SW, SH)], fill=SIL)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

def build_quote_story(story_data: dict):
    """
    Zitat-Story: dark bg, large centered quote, silver author line.
    story_data = {"quote": {"text": "...", "author": "..."}, ...}
    """
    q_data = story_data.get("quote", {})
    text   = _strip_emoji(q_data.get("text", ""))
    author = _strip_emoji(q_data.get("author", ""))
    topic  = story_data.get("topic", "dark minimal")

    bg = pexels_portrait(topic, target_w=SW, target_h=SH) or Image.new("RGB", (SW, SH), (0,0,0))
    ov = Image.new("RGBA", (SW, SH))
    od = ImageDraw.Draw(ov)
    for y in range(SH):
        od.line([(0, y), (SW, y)], fill=(0, 0, 0, int(185 + (y / SH) * 50)))
    img = Image.alpha_composite(bg.convert("RGBA"), ov)
    d   = ImageDraw.Draw(img)
    SIL = _build_accent
    WHT = COLORS["white"]

    # Top bar + badge
    d.rectangle([(0, 0), (SW, 7)], fill=SIL)
    d.text((MARGIN, 28), "MENTVIRO", font=fnt(28, True), fill=SIL)
    d.text((MARGIN, 62), "BUSINESS MINDSET", font=fnt(17), fill=COLORS["dark"])
    d.rectangle([(MARGIN, 96), (SW-MARGIN, 98)], fill=(70, 70, 70))

    # "ZITAT DES TAGES" badge
    d.text((MARGIN, 130), "ZITAT DES TAGES", font=fnt(26, True), fill=SIL)

    # Decorative large quotation mark
    d.text((MARGIN - 20, 260), "“", font=fnt(180, True), fill=(255, 255, 255, 30))

    # Quote text — pixel-aware wrapping within safe zone
    max_q_w = SW - MARGIN * 2
    words = text.split()
    lines, cur = [], []
    for word in words:
        test = " ".join(cur + [word])
        if text_width(test, 64, bold=True) > max_q_w and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))

    y = SH // 2 - (len(lines) * 80) // 2 - 40
    for line in lines[:6]:
        sz = fit_font_size(line, max_q_w, 64, bold=True)
        d.text((MARGIN, y), line, font=fnt(sz, True), fill=WHT)
        bb = fnt(sz, True).getbbox(line)
        y += (bb[3] - bb[1]) + 16

    # Author
    if author:
        y += 24
        d.text((80, y), f"— {author}", font=fnt(38), fill=SIL)

    # Footer (Logo weggelassen — kollidiert mit @mentviro-Text und erzeugt weisses Viereck)
    d.text((SW // 2 - 90, SH - 100), "@mentviro", font=fnt(30, True), fill=SIL)
    d.rectangle([(0, SH-7), (SW, SH)], fill=SIL)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

def build_tips_story(story_data: dict):
    """
    3-Tipps-Story: dark bg, numbered tips, branded.
    story_data = {"tips": {"title": "...", "items": ["tip1", "tip2", "tip3"]}, ...}
    """
    t_data = story_data.get("tips", {})
    title  = _strip_emoji(t_data.get("title", "3 Tipps"))
    items  = [_strip_emoji(it) for it in t_data.get("items", ["", "", ""])[:3]]
    topic  = story_data.get("topic", "dark minimal abstract")

    bg = pexels_portrait(topic, target_w=SW, target_h=SH) or Image.new("RGB", (SW, SH), (0,0,0))
    ov = Image.new("RGBA", (SW, SH))
    od = ImageDraw.Draw(ov)
    for y in range(SH):
        od.line([(0, y), (SW, y)], fill=(0, 0, 0, int(190 + (y / SH) * 45)))
    img = Image.alpha_composite(bg.convert("RGBA"), ov)
    d   = ImageDraw.Draw(img)
    SIL = _build_accent
    WHT = COLORS["white"]

    # Top bar
    d.rectangle([(0, 0), (SW, 7)], fill=SIL)
    d.text((MARGIN, 28), "MENTVIRO", font=fnt(28, True), fill=SIL)
    d.text((MARGIN, 62), "BUSINESS MINDSET", font=fnt(17), fill=COLORS["dark"])
    d.rectangle([(MARGIN, 96), (SW - MARGIN, 98)], fill=(70, 70, 70))

    # "3 TIPPS" hero text
    d.text((MARGIN, 145), "3 TIPPS", font=fnt(90, True), fill=WHT)

    # Subtitle
    max_text_w = SW - MARGIN * 2
    title_sz = fit_font_size(title, max_text_w, 36, bold=False)
    d.text((MARGIN, 260), title, font=fnt(title_sz), fill=SIL)
    d.rectangle([(MARGIN, 310), (MARGIN + 140, 313)], fill=SIL)

    # Tips
    numbers = ["01", "02", "03"]
    y = 370
    for i, (num, tip) in enumerate(zip(numbers, items)):
        # Number accent
        d.text((MARGIN, y), num, font=fnt(44, True), fill=SIL)
        y += 52

        # Tip text — pixel-aware word wrapping within safe zone
        tip_words = tip.split()
        tip_lines, cur = [], []
        for w in tip_words:
            test = " ".join(cur + [w])
            if text_width(test, 46, bold=True) > max_text_w and cur:
                tip_lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            tip_lines.append(" ".join(cur))
        for tl in tip_lines[:2]:
            sz = fit_font_size(tl, max_text_w, 46, bold=True)
            d.text((MARGIN, y), tl, font=fnt(sz, True), fill=WHT)
            bb = fnt(sz, True).getbbox(tl)
            y += (bb[3] - bb[1]) + 8
        y += 50  # gap between tips

    # Footer (Logo weggelassen — kollidiert mit @mentviro-Text und erzeugt weisses Viereck)
    d.text((SW // 2 - 90, SH - 100), "@mentviro", font=fnt(30, True), fill=SIL)
    d.rectangle([(0, SH-7), (SW, SH)], fill=SIL)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

# (instagrapi removed — posting via official Meta Graph API)

# ─── ENGAGEMENT TRACKING ─────────────────────────────────────────────────────

def fetch_and_store_insights(plan):
    updated = False
    cutoff  = (date.today() - timedelta(days=30)).isoformat()
    for post in plan["posts"]:
        if post.get("status") != "published" or not post.get("post_id"):
            continue
        if post.get("insights") or post.get("date", "9999") < cutoff:
            continue
        try:
            ins = ig_get_insights(post["post_id"])
            if not ins:
                continue
            post["insights"] = ins
            score = ins.get("likes", 0) * 2 + ins.get("comments", 0) * 5
            print(f"  Insights Day {post['day']} ({post['type']}): "
                  f"{ins.get('likes',0)}L {ins.get('comments',0)}C score={score}")
            updated = True
        except Exception as e:
            print(f"  Insights Day {post['day']}: {e}")
    if updated:
        save_plan(plan)

def get_engagement_context(plan):
    scored = []
    for p in plan["posts"]:
        ins = p.get("insights")
        if not ins or p.get("status") != "published":
            continue
        score = ins.get("likes", 0) * 2 + ins.get("comments", 0) * 5
        scored.append((score, p))
    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)
    lines = ["\nPERFORMANCE LETZTER POSTS (Engagement-Score):"]
    for score, p in scored[:6]:
        ins = p["insights"]
        lines.append(f"  {'OK' if score > 20 else '-'} '{p['topic']}' ({p['type']}) "
                     f"— {ins.get('likes',0)} Likes, {ins.get('comments',0)} Comments [Score {score}]")
    lines.append("\n-> Orientiere dich an Themen mit hohem Score.")
    return "\n".join(lines) + "\n"

# ─── POSTING TIME ANALYSIS ───────────────────────────────────────────────────

def update_posting_time_stats(plan):
    hour_scores: dict = {}
    for p in plan["posts"]:
        if p.get("status") != "published" or not p.get("insights") or not p.get("published_at"):
            continue
        try:
            hour  = int(p["published_at"][11:13])
            score = p["insights"].get("likes", 0) * 2 + p["insights"].get("comments", 0) * 5
            hour_scores.setdefault(p.get("type", "carousel"), {}).setdefault(hour, []).append(score)
        except Exception:
            pass
    if not hour_scores:
        return
    recommendations = {}
    for post_type, hours in hour_scores.items():
        if len(hours) < 3:
            continue
        avg = {h: sum(v)/len(v) for h, v in hours.items()}
        best = max(avg, key=avg.get)
        recommendations[post_type] = best
        scheduled_utc = {"reel": 5, "carousel": 16}.get(post_type, 16)
        total_posts = sum(len(v) for v in hours.values())
        if best != scheduled_utc and total_posts >= 5:
            cet_best = best + 2
            cet_curr = scheduled_utc + 2
            print(f"  Posting-time tip [{post_type}]: best avg at {best}:00 UTC ({cet_best}:00 CET), "
                  f"currently {scheduled_utc}:00 UTC.")
            send_telegram(
                f"📊 <b>mentviro-bot</b>: Bessere Posting-Zeit für {post_type.upper()}\n"
                f"Aktuell: {cet_curr}:00 Uhr CET\n"
                f"Empfehlung: {cet_best}:00 Uhr CET\n"
                f"(Basierend auf {total_posts} Posts)"
            )
    plan["settings"]["posting_stats"] = recommendations
    save_plan(plan)

# ─── TRENDING + HASHTAG CONTEXT ──────────────────────────────────────────────

HASHTAG_POOL = [
    "#geldanlage", "#finanztipps", "#investieren", "#etfinvestor", "#aktien",
    "#vermögensaufbau", "#passiveseinkommen", "#finanziellefreiheit", "#richwerden",
    "#businessmindset", "#erfolgsmentalität", "#unternehmertum", "#selbstständig",
    "#motivation", "#erfolgreich", "#mindset", "#successmindset", "#entrepreneur",
    "#finanzbildung", "#sparplan", "#depot", "#dividenden", "#börsenwissen",
    "#reichtum", "#wohlstand", "#businesstips", "#mentaltraining", "#zielsetzung",
    "#mentviro", "#moneyminds", "#wealthbuilding",
]

def get_trending_context():
    import xml.etree.ElementTree as ET
    lines   = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mentviro-bot/1.0)"}
    try:
        r = requests.get("https://trends.google.com/trending/rss?geo=DE", timeout=12, headers=headers)
        if r.status_code == 200:
            root     = ET.fromstring(r.content)
            trending = [item.findtext("title","").strip() for item in root.findall(".//item")[:12]
                        if item.findtext("title","").strip()]
            if trending:
                lines.append("GOOGLE TRENDS Deutschland (heute):")
                for t in trending:
                    lines.append(f"  - {t}")
    except Exception as e:
        print(f"  Google Trends failed: {e}")
    feeds = [
        ("Handelsblatt", "https://www.handelsblatt.com/rss/finanzen"),
        ("NTV",          "https://www.n-tv.de/wirtschaft/rss"),
        ("Focus Money",  "https://rss.focus.de/fol/xml/rss_folnews.xml"),
    ]
    headlines = []
    for name, url in feeds:
        try:
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:4]:
                t = item.findtext("title","").strip()
                if t:
                    headlines.append(t)
        except Exception:
            pass
    if headlines:
        lines.append("\nAKTUELLE WIRTSCHAFTS-HEADLINES:")
        for h in headlines[:10]:
            lines.append(f"  - {h}")
    return ("\n" + "\n".join(lines) + "\n") if lines else ""

# ─── CONTENT GENERATION ──────────────────────────────────────────────────────

def check_and_refill_content(plan):
    """Generate content when queue runs low. Always creates PAIRS: 1 reel + 1 carousel per day,
    plus a story_queue entry for each day."""
    pending_reels     = [p for p in plan["posts"] if p["status"]=="pending" and p.get("type")=="reel"]
    pending_carousels = [p for p in plan["posts"] if p["status"]=="pending" and p.get("type")=="carousel"]
    pending_stories   = [s for s in plan.get("story_queue",[]) if s["status"]=="pending"]

    # Date-based check: also refill if latest pending post is within 5 days
    try:
        latest_date = max(
            date.fromisoformat(p["date"]) for p in plan["posts"] if p["status"] == "pending"
        ) if any(p["status"] == "pending" for p in plan["posts"]) else date.today()
        days_remaining = (latest_date - date.today()).days
    except Exception:
        days_remaining = 0

    if (len(pending_reels) >= 3 and len(pending_carousels) >= 3 and
            len(pending_stories) >= 3 and days_remaining >= 5):
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set — skipping generation")
        return

    print("Generating new content pairs via Gemini...")
    trend_context      = get_trending_context()
    engagement_context = get_engagement_context(plan)
    hashtag_sample     = random.sample(HASHTAG_POOL, min(20, len(HASHTAG_POOL)))

    existing_topics = [p["topic"] for p in plan["posts"]]
    last_day   = max((p["day"] for p in plan["posts"]), default=0)
    last_date  = max((date.fromisoformat(p["date"]) for p in plan["posts"]),
                     default=date.today())
    last_date_sq = max((date.fromisoformat(s["date"]) for s in plan.get("story_queue",[])),
                       default=date.today())
    start_date = max(last_date, last_date_sq) + timedelta(days=1)

    DAYS = 3

    # ── Content-Pillar-Zuteilung ─────────────────────────────────────────────
    # MINDSET-FOKUS (alle 3 Pillars sind jetzt Mindset-orientiert, kein Finanz-Schwerpunkt).
    # Ausgewogenerer Mix für persönlicheren Content wie früher (vor der Automation):
    # Educational(Ed) ~43 % · Entertaining(En) ~28 % · Emotional(Em) ~28 %
    # Pro 7 Tage = 3× Ed, 2× En, 2× Em
    PILLAR_CYCLE = ["educational", "entertaining", "emotional",
                    "educational", "entertaining", "educational", "emotional"]
    existing_pillars = [p.get("content_pillar","educational") for p in plan["posts"]]
    ed_count  = existing_pillars.count("educational")
    en_count  = existing_pillars.count("entertaining")
    em_count  = existing_pillars.count("emotional")
    total     = ed_count + en_count + em_count
    # Next DAYS pillars from the cycle
    day_pillars = [PILLAR_CYCLE[(total + i) % len(PILLAR_CYCLE)] for i in range(DAYS)]

    # Per-pillar instructions for the prompt
    PILLAR_GUIDE = {
        "educational": """PILLAR: EDUCATIONAL 📚 (FOKUS: MINDSET & PERSÖNLICHKEITSENTWICKLUNG)
Ziel: Echten Mehrwert liefern — Denkweisen, Gewohnheiten und mentale Konzepte erklären.
Ton: klar, strukturiert, sachlich-motivierend
Themen: MINDSET & Selbstentwicklung im Zentrum — Disziplin, Fokus, Gewohnheiten,
        mentale Modelle, Selbstvertrauen, Umgang mit Rückschlägen, Zielsetzung,
        Prokrastination überwinden, Stoizismus/Gelassenheit, Selbstdisziplin,
        Produktivität, Klarheit, der eigene Weg. Gern auch ein starkes belegbares Zitat
        oder eine treffende Metapher. NUR SEHR SELTEN Geld-Mindset als Bildungsthema
        (Denkweise über Geld, Sparen als Disziplin) — kein Schwerpunkt. NIE konkrete
        Finanzprodukte/ETF-Namen, Kaufempfehlungen oder Renditeversprechen.
Hook-Stil: neugierig-sachlich, z.B. „Warum gewinnen disziplinierte Menschen?", „Was steckt hinter mentaler Stärke?"
Carousel: nummerierte Punkte, klare Struktur, Lerneffekt pro Slide
Reel-Script: erklärender Aufbau, jeder Satz baut auf dem vorherigen auf""",

        "entertaining": """PILLAR: ENTERTAINING 😄 (FOKUS: MINDSET & LIFESTYLE)
Ziel: Hohe Shares & Saves durch Unterhaltung mit Mehrwert (Edutainment).
Ton: locker, witzig, relatable — aber mit echtem Insight am Ende
Themen: Mindset & Lifestyle relatable verpackt — „POV: Du...", „Zeichen dass du mental wächst",
        „5 Dinge die disziplinierte Menschen anders machen", „Gewohnheiten die dein Leben ändern",
        Produktivität, Fokus, Selbstdisziplin, mentale Stärke im Alltag, Vergleiche
        diszipliniert vs. undiszipliniert / Macher vs. Träumer (OHNE Geld-/Renditeversprechen),
        überraschende psychologische Fakten. KEINE arm-vs-reich oder Money-Vergleiche mehr.
Hook-Stil: direkt, provokant-freundlich, Schmunzel-Faktor
Carousel: Chart/Liste-Style, visuelle Kontraste, jeder Slide ein Aha-Moment
Reel-Script: kurze Sätze, Rhythmus, überraschende Wendung am Ende
Pexels: lebhafter, kontrastreicher — z.B. neon, urban, energetisch""",

        "emotional": """PILLAR: EMOTIONAL ❤️
Ziel: Tiefe Verbindung aufbauen, Kommentare & Saves durch Resonanz auslösen.
Ton: persönlich, authentisch, verletzlich — KEINE Geldversprechen
Themen: persönliche Wachstumsgeschichten (ohne Eigenlob), Lebensweisheiten,
        Rückschläge und was man daraus lernt, Brief-an-mein-18-jähriges-Ich-Stil,
        Werte statt Zahlen, Warum Geld NICHT das einzige Ziel ist,
        Dankbarkeit, Geduld, der Weg (nicht das Ziel)
Hook-Stil: Story-Opener, z.B. „Es gab einen Moment, der alles veränderte.",
           „Ich hätte das früher wissen müssen.", „Niemand redet darüber, aber..."
Carousel: stimmungsvolle Bilder, poetischere Texte, weniger Bullet-Points
Reel-Script: storytelling-Aufbau, emotional peak in der Mitte, ruhiger Abschluss
Pexels: stimmungsvoll, warm, natürlich — z.B. sunrise, forest, ocean, rain"""
    }

    # Build per-day pillar block for the prompt
    day_pillar_block = "\n".join(
        f"  Tag {i+1} ({(start_date + timedelta(days=i)).isoformat()}): "
        f"{day_pillars[i].upper()} — {PILLAR_GUIDE[day_pillars[i]].splitlines()[0]}"
        for i in range(DAYS)
    )

    prompt = f"""Du bist Content Creator für @mentviro — ein deutschsprachiger Instagram-Account über Mindset, persönliche Entwicklung, Lifestyle und Erfolg. Finanzen sind NUR EIN Thema von vielen.

WICHTIG — ZEICHENKODIERUNG:
- Verwende IMMER echte deutsche Umlaute: ä, ö, ü, Ä, Ö, Ü, ß
- Verwende IMMER echte Unicode-Emojis (z.B. 🔑 💡 📊 🧠 ⚡ 🎯 😄 ❤️ 🌱 🔥 💪 ✨), NIEMALS ? als Platzhalter
- Das JSON muss gültige UTF-8 Strings enthalten, keine Ersatzzeichen

═══ THEMEN-UNIVERSUM (ABWECHSLUNG IST PFLICHT) ═══════════════════════════════
Wähle Themen aus ALLEN dieser Kategorien — nicht nur Finanzen:

💡 MINDSET & PSYCHOLOGIE
Gewohnheiten, Denkfehler, kognitive Verzerrungen, Resilienz, Fokus, Prokrastination,
Entscheidungen treffen, Selbstsabotage überwinden, Wachstumsdenken

🌱 PERSÖNLICHE ENTWICKLUNG
Disziplin, Morgenroutinen, Deep Work, Lernen lernen, Komfortzone, Selbstreflexion,
Identität & Werte, persönliche Vision, Lebensphilosophie

💪 PRODUKTIVITÄT & LIFESTYLE
Zeit-Management, Energie-Management, digitale Minimalismus, Work-Life-Integration,
Schlaf & Performance, Sport als Mindset-Tool, Nein sagen, Priorisierung

🤝 BEZIEHUNGEN & KOMMUNIKATION
Netzwerken authentisch, Kommunikation, Einfluss & Überzeugung, Mentoren finden,
Umfeld gestalten, toxische vs. förderliche Beziehungen

🚀 UNTERNEHMERDENKEN & KREATIVITÄT
Ideen entwickeln, Risiko & Sicherheit, Scheitern & lernen, Side Projects,
kreatives Denken, Innovation, von Angestellten- zu Unternehmermindset

💰 FINANZEN & GELD-MINDSET (SEHR SELTEN — höchstens ca. 1 von 10 Posts)
Nur ganz gelegentlich Geld als MINDSET-Thema: Denkweise über Geld, Geduld beim
Vermögensaufbau, Sparen als Disziplin, langfristiges Denken. Kein Schwerpunkt, fällt
kaum auf. NIEMALS konkrete Produkte/Broker/ETF-Namen, Kaufempfehlungen, Renditeversprechen
oder "verdiene X Euro". Der Account hat eine aktive Einschränkung wegen Finanz-/Scam-
Verdacht — Finanz IMMER als Bildung/Mindset framen, im Zweifel lieber weglassen.

💬 ZITATE & METAPHERN (Trend-Format — gern öfter)
Kurze, kraftvolle Zitate bekannter, BELEGBARER Personen (Stoiker, Unternehmer, Denker)
oder eigene prägnante Metaphern/Analogien. Im Trend: ästhetische Zitat-Posts, "ein Satz
der hängenbleibt", Metaphern die ein Konzept auf den Punkt bringen. Reel: Zitat langsam
aufbauen + kurz erklären, warum es trifft. Carousel: 1 starkes Zitat groß + Kontext.
NUR echte, belegbare Zitate — keine erfundenen.

📚 WISSEN & PERSPEKTIVEN
Philosophie (Stoiker, etc.), Geschichte von Erfolg, Psychologie-Studien,
überraschende Fakten über Erfolg/Misserfolg, Buchempfehlungen-Stil

═══ CONTENT-STRATEGIE ════════════════════════════════════════════════════════
@mentviro postet DREI Content-Pillars im Wechsel:
{PILLAR_GUIDE["educational"]}

{PILLAR_GUIDE["entertaining"]}

{PILLAR_GUIDE["emotional"]}

═══ AUFGABE ══════════════════════════════════════════════════════════════════
Erstelle GENAU {DAYS} Tages-Pakete mit folgender Pillar-Zuteilung:
{day_pillar_block}

Jedes Paket enthält: 1 REEL + 1 CAROUSEL + 1 STORY-PAAR
Reel und Carousel eines Tages teilen denselben Pillar und ergänzen sich thematisch.
WICHTIG: Wähle für jeden Tag ein anderes Themengebiet — Abwechslung zwischen den Kategorien oben.

BEREITS BEHANDELTE THEMEN (NICHT wiederholen):
{chr(10).join(f'- {t}' for t in existing_topics[-20:])}
{trend_context}{engagement_context}
═══ INSTAGRAM-RICHTLINIEN — PFLICHT ══════════════════════════════════════════
VERBOTEN:
- Konkrete Rendite- oder Gewinnversprechen ("verdiene X Euro", "X% Rendite garantiert")
- Passives-Einkommen-Formeln oder Anleitungen zum Geldverdienen
- Get-rich-quick-Aussagen
- FOMO-Taktiken ("nur heute", "letzte Chance")
- Falsche oder nicht belegbare Zitate
- Keine Links in Captions
- Keine konkreten Produkt-/Broker-/Plattform-Empfehlungen
ERLAUBT:
- Alle Themen aus dem Themen-Universum oben
- Mindset, Lifestyle, persönliche Entwicklung (SCHWERPUNKT — die Mehrheit der Posts)
- Geld-Mindset/Finanzbildung SEHR SELTEN (max ~1 von 10, immer als Bildung/Mindset framen)
- Zitate & Metaphern als Trend-Format (gern öfter — nur echte, belegbare Zitate)
- Humorvoller, authentischer, motivierender Ton

═══ FORMAT-REGELN ════════════════════════════════════════════════════════════
- Zielgruppe: 18-35 Jahre, Deutschland, ambitioniert, an persönlichem Wachstum interessiert
- PEXELS QUERIES: zum Pillar passend (Ed: dunkel/minimalistisch · En: energetisch/urban · Em: warm/stimmungsvoll). NIEMALS: businessman, office, suit, handshake
- Themen-Schwerpunkt: MINDSET & persönliche Entwicklung (wie ein authentischer Creator, der seine eigene Reise teilt). Geld-Mindset nur SEHR SELTEN (~1 von 10). Zitate/Metaphern gern als Trend-Format einstreuen.
- Caption: zum Pillar passender Ton, exakt 15 Hashtags aus: {' '.join(hashtag_sample)} plus immer #mentviro
- Zitat: NUR echte, belegbare Zitate bekannter Personen
- 3 Tipps: konkret, umsetzbar, max 12 Wörter pro Tipp
- story_poll: Ja/Nein oder Entweder/Oder, max 35 Zeichen

Gib NUR ein JSON-Array mit {DAYS} Objekten aus. Kein Text davor/danach.

Schema für jedes Objekt:
{{
  "day": {last_day+1},
  "date": "{(start_date).isoformat()}",
  "content_pillar": "educational|entertaining|emotional",
  "reel": {{
    "topic": "...", "status": "pending", "hook": "...",
    "script": ["Satz 1","Satz 2","Satz 3","Satz 4","Satz 5","Folge @mentviro."],
    "caption": "... #mentviro ...",
    "pexels_video_query": "passende dark cinematic query",
    "story_text": ["NEUES REEL","Zeile 1","Zeile 2","Jetzt anschauen"],
    "story_poll": "Kurze Frage?"
  }},
  "carousel": {{
    "topic": "...", "status": "pending", "hook": "...",
    "slides": [
      {{"badge":null,"num":null,"title":["..."],"body":["..."],"is_cover":true}},
      {{"badge":"PUNKT #1","num":"1 / N","title":["..."],"body":["..."]}},
      ...,
      {{"badge":"FOLGE UNS","num":null,"title":["Mehr Mindset","& Money Moves"],"body":["Folge @mentviro","für täglich mehr."]}}
    ],
    "caption": "... #mentviro ...",
    "pexels_queries": ["q1","q2","q3","q4","q5","q6"],
    "story_text": ["NEU AUF MENTVIRO","Zeile 1","Zeile 2","Jetzt ansehen"],
    "story_poll": "Kurze Frage?"
  }},
  "stories": {{
    "status": "pending",
    "topic": "dark minimal cinematic pexels query",
    "quote": {{
      "text": "Echtes Zitat. Max 25 Wörter.",
      "author": "Name"
    }},
    "tips": {{
      "title": "Kurzer Titel",
      "items": ["Tipp 1 max 12 Wörter","Tipp 2 max 12 Wörter","Tipp 3 max 12 Wörter"]
    }}
  }}
}}"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"content-type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": 10000, "temperature": 0.9}},
            timeout=120)
        if r.status_code != 200:
            print(f"Gemini error {r.status_code}: {r.text[:300]}")
            return
        text  = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start == -1 or end == 0:
            print("No JSON array in Gemini response")
            return

        packages = json.loads(text[start:end])
        new_posts   = []
        new_stories = []

        for i, pkg in enumerate(packages):
            d       = (start_date + timedelta(days=i)).isoformat()
            day_num = last_day + i + 1
            pillar  = pkg.get("content_pillar", day_pillars[i])

            # Visual style: emotional → gold (warm), entertaining → gold, educational → silver
            style = "gold" if pillar in ("emotional", "entertaining") else "silver"

            reel = pkg.get("reel", {})
            reel.update({"day": day_num, "date": d, "type": "reel",
                         "status": "pending", "style": style, "content_pillar": pillar})
            new_posts.append(reel)

            car = pkg.get("carousel", {})
            car.update({"day": day_num, "date": d, "type": "carousel",
                        "status": "pending", "style": style, "content_pillar": pillar})
            new_posts.append(car)

            stories = pkg.get("stories", {})
            stories.update({"day": day_num, "date": d,
                            "status": "pending", "style": style, "content_pillar": pillar})
            new_stories.append(stories)

        plan["posts"].extend(new_posts)
        plan.setdefault("story_queue", []).extend(new_stories)
        save_plan(plan)
        print(f"Generated {len(packages)} day-packages "
              f"({len(new_posts)} posts + {len(new_stories)} story-pairs)")

    except Exception as e:
        import traceback
        print(f"Generation failed: {e}")
        traceback.print_exc()

# ─── CAROUSEL WORKFLOW ───────────────────────────────────────────────────────

def run_carousel(post, plan):
    set_build_accent(post)
    print(f"Building carousel: {post['topic']}")
    pexels_queries = post.get("pexels_queries", [])
    used_photo_ids: set = set()   # Track used Pexels IDs — prevents duplicate photos
    child_ids: list = []
    try:
        for i, slide in enumerate(post["slides"]):
            print(f"  Slide {i+1}/{len(post['slides'])}...", end=" ", flush=True)
            bg_img = None
            if slide.get("is_cover"):
                # Cover gets a B&W Pexels photo (grayscale applied in build_carousel_slide)
                cover_query = (pexels_queries[0] if pexels_queries
                               else post.get("pexels_video_query", "dark minimal abstract cinematic"))
                bg_img = pexels_portrait(cover_query, exclude_ids=used_photo_ids)
            elif pexels_queries:
                # Cycle through queries (% len) so they never repeat the same query back-to-back
                q = pexels_queries[i % len(pexels_queries)]
                bg_img = pexels_portrait(q, exclude_ids=used_photo_ids)
            img_bytes = build_carousel_slide(slide, bg_img)
            img_url   = cloudinary_upload(img_bytes)
            child_id  = ig_create_container(image_url=img_url, is_carousel_item=True)
            child_ids.append(child_id)
            print(f"ok (container {child_id})")
            time.sleep(1)

        print("  Creating carousel container...")
        carousel_id = ig_create_carousel_container(child_ids, post["caption"])
        time.sleep(3)
        print("  Publishing...")
        media_id = ig_publish(carousel_id)
        print(f"  Carousel live! ID: {media_id}")
        return media_id
    except Exception:
        raise

# ─── REEL WORKFLOW ───────────────────────────────────────────────────────────

def _wrap_title(text, max_len=26):
    if len(text) <= max_len:
        return [text]
    words  = text.split()
    lines, cur = [], []
    for w in words:
        if sum(len(x)+1 for x in cur)+len(w) > max_len and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines[:3]

def _reel_as_carousel(post, plan):
    """Fallback: post reel script as a 9:16 carousel via Graph API."""
    print("  Building 9:16 carousel from reel script...")
    script = post.get("script", [post.get("hook", post["topic"])])
    slides = [{"badge": None, "num": None, "is_cover": True,
               "title": _wrap_title(post.get("hook", post["topic"])),
               "body":  ["Lies weiter."]}]
    n = len(script)
    for i, line in enumerate(script):
        slides.append({"badge": None, "num": f"{i+1} / {n}",
                       "title": _wrap_title(line), "body": []})
    slides.append({"badge": "FOLGE UNS", "num": None,
                   "title": ["Taegliches Mindset", "& Money Moves"],
                   "body":  ["Folge @mentviro", "fuer taeglich mehr."]})

    pq = post.get("pexels_video_query", "dark city cinematic night")
    child_ids: list = []
    for i, slide in enumerate(slides):
        print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
        # Cover → B&W photo; others → colour photo
        bg_img = (pexels_portrait(pq, target_w=SW, target_h=SH)
                  if True  # fetch for all slides; is_cover triggers B&W in build_carousel_slide
                  else None)
        img_bytes = build_carousel_slide(slide, bg_img, w=SW, h=SH)
        img_url   = cloudinary_upload(img_bytes)
        child_id  = ig_create_container(image_url=img_url, is_carousel_item=True)
        child_ids.append(child_id)
        print(f"ok (container {child_id})")
        time.sleep(1)
    carousel_id = ig_create_carousel_container(child_ids, post["caption"])
    time.sleep(3)
    media_id = ig_publish(carousel_id)
    print(f"  Reel-Carousel live! ID: {media_id}")
    return media_id

# ─── REEL HELPERS ────────────────────────────────────────────────────────────

def _parse_word_timings(alignment: dict) -> list:
    """Extract [(word, start_s, end_s)] from ElevenLabs alignment data."""
    chars  = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends   = alignment.get("character_end_times_seconds", [])
    words, cur, word_start = [], "", 0.0
    for c, s, e in zip(chars, starts, ends):
        if c in (" ", "\n", "\t"):
            if cur.strip():
                words.append((cur.strip(), word_start, e))
            cur = ""
        else:
            if not cur:
                word_start = s
            cur += c
    if cur.strip():
        words.append((cur.strip(), word_start, ends[-1] if ends else 0.0))
    return words


def _words_to_subtitle_chunks(words: list, max_chars: int = 24) -> list:
    """Group words into [(text, start_s, end_s)] chunks of max_chars each."""
    chunks, cur_words, cur_len = [], [], 0
    for word, start, end in words:
        needed = len(word) + (1 if cur_words else 0)
        if cur_len + needed > max_chars and cur_words:
            text = " ".join(w[0] for w in cur_words)
            chunks.append((text, cur_words[0][1], cur_words[-1][2]))
            cur_words, cur_len = [(word, start, end)], len(word)
        else:
            cur_words.append((word, start, end))
            cur_len += needed
    if cur_words:
        chunks.append((" ".join(w[0] for w in cur_words), cur_words[0][1], cur_words[-1][2]))
    return chunks


def _reel_find_font():
    """Return path to best available bold TTF font, or None."""
    candidates = [
        "/usr/share/fonts/truetype/Montserrat-Regular.ttf",
        "/usr/local/share/fonts/Montserrat-Regular.ttf",
        "C:/Windows/Fonts/Montserrat-Regular.ttf",
        os.path.join(os.path.dirname(__file__), "assets", "Montserrat-Regular.ttf"),
        "/usr/share/fonts/truetype/Montserrat-Bold.ttf",
        "/usr/local/share/fonts/Montserrat-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/Montserrat-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
        os.path.join(os.path.dirname(__file__), "assets", "Montserrat-Bold.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                ImageFont.truetype(p, 20)
                return p
            except (OSError, IOError):
                continue
    return None

def _reel_wrap_text(text, max_chars=20):
    """Split sentence into lines of max_chars each (safe up to 20 chars at subtitle fontsize 54)."""
    import textwrap
    return textwrap.wrap(text, width=max_chars) or [text]

def _reel_sentence_queries(post):
    """Return a Pexels query per script sentence.
    Uses the post's pexels_video_query as base for consistent aesthetics.
    Varies by clip index so each clip fetches a different video."""
    script = post.get("script", [post.get("hook", "")])
    base   = post.get("pexels_video_query", "dark cinematic minimal person")
    # Keep the base aesthetic query for all clips — pick_random=True in pexels_video()
    # already gives variety. Per-sentence keyword extraction produced off-topic results.
    return [base for _ in script]

def _reel_probe_duration(path):
    """Return video duration in seconds via ffprobe."""
    import subprocess
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=20)
        return float(p.stdout.strip().split("\n")[0] or "0")
    except Exception:
        return 0.0

def _reel_make_clip(out_path, raw_video, duration, day, idx):
    """Build one 1080x1920 video clip — no text overlay (subtitles added later as separate pass)."""
    import subprocess
    # fps=30 + format=yuv420p erzwingen einheitliche Framerate/Pixelformat über ALLE
    # Clips. Sonst haben Pexels-Clips gemischte fps (24/25/30/60) und der spätere
    # concat -c copy bekommt Timestamp-Sprünge → Clip friert am Ende ein, nächster
    # startet verzögert.
    scale_crop = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
        "setsar=1,fps=30,format=yuv420p,"
        "eq=brightness=-0.15:contrast=1.0"
    )
    # Einheitliche Encoding-Parameter für sauberen concat -c copy (gleiche fps + timebase)
    enc = ["-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-r", "30", "-pix_fmt", "yuv420p", "-video_track_timescale", "90000"]
    t = str(round(duration, 2))
    raw_dur   = _reel_probe_duration(raw_video) if raw_video else 0
    loop_args = ["-stream_loop", "-1"] if raw_dur > 0 and raw_dur < duration * 1.1 else []

    if raw_video and os.path.exists(raw_video):
        try:
            subprocess.run(
                ["ffmpeg", "-y"] + loop_args + [
                    "-i", raw_video, "-vf", scale_crop] + enc + [
                    "-an", "-t", t, out_path],
                check=True, capture_output=True, timeout=180)
            return
        except Exception:
            pass

    # Fallback: plain black background (gleiche Encoding-Parameter)
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", "color=black:size=1080x1920:rate=30"] + enc + [
         "-an", "-t", t, out_path],
        check=True, capture_output=True, timeout=60)


def _reel_overlay_subtitles(concat_path, out_path, sub_chunks, day, font_path):
    """Burn timed word-chunks as drawtext enable-expressions onto the full video.

    Windows-Falle: im ffmpeg-Filtergraph ist ':' der Options-Trenner. Ein absoluter
    Pfad wie textfile='C:/Users/...' oder fontfile=C:/Windows/Fonts/arial.ttf enthält
    Doppelpunkte → der drawtext-Filter bricht ab (exit 4294967274), Reel ging bisher
    OHNE Untertitel raus. Fix: ffmpeg mit cwd=TMPDIR ausführen und Textdateien + Font
    NUR über bare Dateinamen (ohne Laufwerk/Pfad) referenzieren → kein Doppelpunkt im
    Filtergraph. Der Filtergraph wird zusätzlich in eine Datei geschrieben
    (-filter_script:v) statt als Riesen-Argument, um das Windows-Kommandozeilenlimit
    zu umgehen, wenn viele Untertitel-Chunks verkettet sind.
    """
    import subprocess, shutil
    if not sub_chunks:
        return concat_path

    tmp_files = []

    # Font in TMPDIR unter bare Namen kopieren (kein Doppelpunkt im Filtergraph)
    font_name = ""
    if font_path and os.path.exists(font_path):
        font_name = f"reel_{day}_font.ttf"
        try:
            shutil.copyfile(font_path, os.path.join(TMPDIR, font_name))
            tmp_files.append(os.path.join(TMPDIR, font_name))
        except Exception:
            font_name = ""

    dt_parts = []
    for i, (text, start, end) in enumerate(sub_chunks):
        txt_name = f"reel_{day}_sub{i}.txt"            # bare name, liegt in TMPDIR
        txt_path = os.path.join(TMPDIR, txt_name)
        tmp_files.append(txt_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(_strip_emoji(text))
        font_arg = f":fontfile={font_name}" if font_name else ""
        dt_parts.append(
            f"drawtext=textfile={txt_name}{font_arg}"
            f":enable='between(t,{start:.3f},{end:.3f})'"
            f":fontcolor=white:fontsize=54"
            f":x=(w-text_w)/2:y=h-220"
            f":borderw=3:bordercolor=black"
            f":fix_bounds=1"
        )

    # Filtergraph in Datei schreiben (bare name, in TMPDIR)
    filter_name = f"reel_{day}_filter.txt"
    filter_path = os.path.join(TMPDIR, filter_name)
    with open(filter_path, "w", encoding="utf-8") as f:
        f.write(",".join(dt_parts))
    tmp_files.append(filter_path)

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", concat_path,
             "-filter_script:v", filter_name,
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-r", "30", "-pix_fmt", "yuv420p", "-video_track_timescale", "90000",
             "-an", out_path],
            check=True, capture_output=True, timeout=300, cwd=TMPDIR)
        print(f"  Subtitles burned: {len(sub_chunks)} chunks")
        return out_path
    except Exception as e:
        err = getattr(e, "stderr", b"")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        print(f"  Subtitle overlay failed: {e} — {err[-300:]} — continuing without text")
        return concat_path
    finally:
        for f in tmp_files:
            try: os.unlink(f)
            except: pass

def run_reel(post, plan):
    set_build_accent(post)
    import subprocess
    print(f"Building reel: {post['topic']}")

    script  = post.get("script", [post.get("hook", "")])
    day     = post["day"]
    cleanup = []

    # ── Step 1: TTS with word-level timestamps ────────────────────────────────
    audio_path = f"{TMPDIR}/reel_{day}_voice.mp3"
    audio_ok   = False
    audio_dur  = 0.0
    sub_chunks = []   # [(text, start_s, end_s)] for subtitle overlay
    try:
        el_key = os.environ.get("ELEVENLABS_API_KEY",
                                "1071b6e53cb6e950c63d8e11a05dfa7b07764275cab9fda0ce63104a421c2d37")
        el_r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB/with-timestamps",
            headers={"xi-api-key": el_key, "Content-Type": "application/json"},
            json={"text": " ".join(script),
                  "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.75, "similarity_boost": 0.55, "style": 0.2, "use_speaker_boost": False}},
            timeout=90)
        if el_r.status_code == 200:
            ts_data    = el_r.json()
            audio_bytes = base64.b64decode(ts_data.get("audio_base64", ""))
            with open(audio_path, "wb") as af:
                af.write(audio_bytes)
            audio_ok  = True
            audio_dur = _reel_probe_duration(audio_path)
            cleanup.append(audio_path)
            # Parse word-level timing for synced subtitles
            alignment  = ts_data.get("alignment", {})
            word_times = _parse_word_timings(alignment)
            sub_chunks = _words_to_subtitle_chunks(word_times, max_chars=24)
            print(f"  Voiceover: OK ({len(audio_bytes)//1024} KB, {audio_dur:.1f}s, {len(sub_chunks)} subtitle chunks)")
        else:
            print(f"  Voiceover: {el_r.status_code} — {el_r.text[:100]}")
    except Exception as e:
        print(f"  Voiceover error: {e}")

    if audio_dur < 1:
        # Fallback estimate: ~75ms per character
        audio_dur = sum(len(s) for s in script) * 0.075

    # ── Step 1b: Background music ─────────────────────────────────────────────
    # Default: "Serene View" by Mixkit (CC0, royalty-free)
    _DEFAULT_BG = "https://assets.mixkit.co/music/443/443.mp3"
    bg_music_path = None
    bg_music_url  = os.environ.get("BACKGROUND_MUSIC_URL", _DEFAULT_BG)
    if bg_music_url:
        try:
            bm_r = requests.get(bg_music_url, timeout=30)
            if bm_r.status_code == 200:
                bg_music_path = f"{TMPDIR}/reel_{day}_bgmusic.mp3"
                with open(bg_music_path, "wb") as bf:
                    bf.write(bm_r.content)
                cleanup.append(bg_music_path)
                print(f"  BG music: OK ({len(bm_r.content)//1024} KB)")
            else:
                print(f"  BG music: {bm_r.status_code} — skipped")
        except Exception as e:
            print(f"  BG music download failed: {e} — skipped")

    # ── Step 2: Per-sentence duration (proportional to char count) ───────────
    char_counts = [max(len(s), 10) for s in script]
    total_chars = sum(char_counts)
    durations   = [audio_dur * (c / total_chars) for c in char_counts]
    print(f"  Script: {len(script)} sentences, total ~{audio_dur:.1f}s")

    # ── Step 3: Download one Pexels video per sentence ───────────────────────
    font_path   = _reel_find_font()   # still needed for subtitle overlay
    vid_queries = _reel_sentence_queries(post)
    raw_videos  = []
    for i, (sent, query) in enumerate(zip(script, vid_queries)):
        url = pexels_video(query, pick_random=True)
        raw = f"{TMPDIR}/reel_{day}_raw{i}.mp4"
        if url:
            try:
                resp = requests.get(url, timeout=90, stream=True)
                with open(raw, "wb") as f:
                    for chunk in resp.iter_content(65536): f.write(chunk)
                raw_videos.append(raw)
                cleanup.append(raw)
                print(f"  Video {i+1}/{len(script)}: '{query[:40]}' -> {os.path.getsize(raw)/1024:.0f} KB")
            except Exception as e:
                print(f"  Video {i+1} download error: {e}")
                raw_videos.append(None)
        else:
            print(f"  Video {i+1}: no result for '{query[:40]}' — black bg")
            raw_videos.append(None)

    # ── Step 4: Build per-sentence clips ────────────────────────────────────
    clip_paths = []
    for i, (sentence, raw, dur) in enumerate(zip(script, raw_videos, durations)):
        clip_out = f"{TMPDIR}/reel_{day}_clip{i}.mp4"
        clip_dur = max(dur, 2.0)  # minimum 2s per clip
        try:
            _reel_make_clip(clip_out, raw, clip_dur, day, i)
            clip_paths.append(clip_out)
            cleanup.append(clip_out)
            print(f"  Clip {i+1}: '{sentence[:40]}' ({clip_dur:.1f}s)")
        except Exception as e:
            print(f"  Clip {i+1} failed ({e}) — building black fallback")
            # Always build a fallback so total duration matches audio
            try:
                import subprocess as _sp
                _sp.run(
                    ["ffmpeg", "-y", "-f", "lavfi",
                     "-i", f"color=black:size=1080x1920:rate=30",
                     "-t", str(round(clip_dur, 2)), "-c:v", "libx264",
                     "-preset", "fast", "-crf", "28",
                     "-r", "30", "-pix_fmt", "yuv420p", "-video_track_timescale", "90000",
                     "-an", clip_out],
                    check=True, capture_output=True, timeout=60)
                clip_paths.append(clip_out)
                cleanup.append(clip_out)
            except Exception as e2:
                print(f"  Fallback clip also failed: {e2}")

    if not clip_paths:
        print("  No clips built — fallback to carousel")
        return _reel_as_carousel(post, plan)

    # ── Step 5: Concatenate clips ────────────────────────────────────────────
    concat_list = f"{TMPDIR}/reel_{day}_concat.txt"
    concat_path = f"{TMPDIR}/reel_{day}_concat.mp4"
    with open(concat_list, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")
    cleanup += [concat_list, concat_path]
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", concat_path],
            check=True, capture_output=True, timeout=180)
        print(f"  Concatenated: {len(clip_paths)} clips -> {os.path.getsize(concat_path)/1024/1024:.1f} MB")
    except subprocess.CalledProcessError as e:
        print(f"  Concat failed: {e.stderr[-300:]} — fallback carousel")
        return _reel_as_carousel(post, plan)

    # ── Step 5b: Burn synced subtitles onto concatenated video ───────────────
    subtitled_path = f"{TMPDIR}/reel_{day}_subtitled.mp4"
    cleanup.append(subtitled_path)
    concat_path = _reel_overlay_subtitles(concat_path, subtitled_path, sub_chunks, day, font_path)

    # ── Step 6: Mix voiceover ────────────────────────────────────────────────
    final_path = f"{TMPDIR}/reel_{day}_final.mp4"
    cleanup.append(final_path)
    if audio_ok and os.path.exists(audio_path):
        try:
            video_dur = _reel_probe_duration(concat_path)
            # If video is shorter than audio, loop last frame to fill gap
            # Use -t audio_dur so video exactly matches voiceover length
            mix_t = max(audio_dur, video_dur)
            if bg_music_path and os.path.exists(bg_music_path):
                # Voiceover + looped background music at 10% volume
                subprocess.run(
                    ["ffmpeg", "-y",
                     "-i", concat_path,
                     "-i", audio_path,
                     "-stream_loop", "-1", "-i", bg_music_path,
                     "-filter_complex",
                     f"[2:a]volume=0.10,atrim=duration={round(mix_t, 2)}[bg];"
                     f"[1:a][bg]amix=inputs=2:duration=first:weights=1 1[aout]",
                     "-map", "0:v:0", "-map", "[aout]",
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                     "-t", str(round(mix_t, 2)), final_path],
                    check=True, capture_output=True, timeout=180)
            else:
                subprocess.run(
                    ["ffmpeg", "-y",
                     "-i", concat_path,
                     "-i", audio_path,
                     "-map", "0:v:0", "-map", "1:a:0",
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                     "-t", str(round(mix_t, 2)), final_path],
                    check=True, capture_output=True, timeout=180)
            print(f"  Final with audio: {os.path.getsize(final_path)/1024/1024:.1f} MB")
        except Exception as e:
            print(f"  Audio mix failed: {e} — using silent video")
            final_path = concat_path
    else:
        final_path = concat_path

    # ── Step 7: Upload & publish ─────────────────────────────────────────────
    try:
        print("  Uploading to Cloudinary...")
        with open(final_path, "rb") as vf:
            cdn_url = cloudinary_upload(vf.read(), resource_type="video", suffix=".mp4")

        # DRY_RUN: nur Vorschau hochladen, NICHT auf Instagram posten
        if DRY_RUN:
            print(f"  DRY_RUN aktiv — KEIN Instagram-Post. Vorschau-Link: {cdn_url}")
            send_telegram(
                f"🧪 <b>mentviro DRY_RUN</b> — Reel-Vorschau (NICHT gepostet)\n"
                f"Tag {post['day']}: {post.get('topic','')}\n"
                f"Untertitel-Chunks: {len(sub_chunks)} · Audio: {'ja' if audio_ok else 'nein'}\n"
                f'<a href="{cdn_url}">▶ Vorschau ansehen</a>'
            )
            return None

        print("  Creating REELS container...")
        container_id = ig_create_container(
            video_url=cdn_url,
            caption=post["caption"],
            media_type="REELS",
        )
        ig_wait_for_video(container_id, timeout_s=300)
        print("  Publishing reel...")
        media_id = ig_publish(container_id)
        print(f"  Reel live! ID: {media_id}")
        return media_id
    except Exception as e:
        print(f"  Reel upload failed ({type(e).__name__}): {e} — fallback carousel")
        return _reel_as_carousel(post, plan)
    finally:
        for p in cleanup:
            try:
                if p and os.path.exists(p): os.unlink(p)
            except Exception:
                pass

# ─── STORY WORKFLOWS ─────────────────────────────────────────────────────────

def run_attached_story(post):
    """Post the story attached to a carousel/reel via Graph API."""
    print("  Posting attached story...")
    story_bytes = build_attached_story(post)
    img_url     = cloudinary_upload(story_bytes)
    container   = ig_create_container(image_url=img_url, media_type="STORIES")
    time.sleep(2)
    media_id    = ig_publish(container)
    print(f"  Story live! ID: {media_id}")
    return media_id

def run_daily_stories(plan):
    """Post today's standalone quote story + tips story."""
    sd = get_todays_stories(plan)
    if not sd:
        print("No pending stories for today.")
        return None, None

    set_build_accent(sd)
    print(f"Building daily stories for: {sd.get('date')}")

    # Quote story
    print("  Quote story...", end=" ", flush=True)
    quote_id = None
    try:
        qbytes      = build_quote_story(sd)
        img_url     = cloudinary_upload(qbytes)
        container   = ig_create_container(image_url=img_url, media_type="STORIES")
        quote_id    = ig_publish(container)
        print(f"ok (ID: {quote_id})")
    except Exception as e:
        print(f"failed: {e}")

    time.sleep(3)

    # Tips story
    print("  Tips story...", end=" ", flush=True)
    tips_id = None
    try:
        tbytes      = build_tips_story(sd)
        img_url     = cloudinary_upload(tbytes)
        container   = ig_create_container(image_url=img_url, media_type="STORIES")
        tips_id     = ig_publish(container)
        print(f"ok (ID: {tips_id})")
    except Exception as e:
        print(f"failed: {e}")

    # Mark as published
    sd["status"]      = "published"
    sd["quote_id"]    = quote_id
    sd["tips_id"]     = tips_id
    sd["published_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_plan(plan)

    return quote_id, tips_id

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def generate_dashboard(plan):
    today    = date.today().isoformat()
    upcoming = [p for p in plan["posts"] if p["status"] == "pending"][:14]
    recent   = sorted([p for p in plan["posts"] if p["status"] == "published"],
                      key=lambda p: p.get("date",""), reverse=True)[:10]
    sq_upcoming = [s for s in plan.get("story_queue",[]) if s["status"]=="pending"][:7]

    def badge(t):
        colors = {"reel": "#e8175d", "carousel": "#1a73e8", "stories": "#0f9d58"}
        c = colors.get(t, "#888")
        return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{t.upper()}</span>'

    def ins_html(p):
        ins = p.get("insights", {})
        if not ins: return ""
        return f' <span style="color:#888;font-size:12px">❤ {ins.get("likes",0)} 💬 {ins.get("comments",0)}</span>'

    rows_up = "".join(f'<tr><td>{p["date"]}</td><td>{badge(p["type"])}</td>'
                      f'<td>{p.get("topic","")}</td></tr>' for p in upcoming)
    rows_re = "".join(f'<tr><td>{p["date"]}</td><td>{badge(p["type"])}</td>'
                      f'<td>{p.get("topic","")}{ins_html(p)}</td></tr>' for p in recent)

    sched_html = "".join(
        f'<tr><td>{s["date"]}</td><td>{badge("stories")}</td>'
        f'<td>{s.get("quote",{}).get("text","")[:60]}...</td></tr>'
        for s in sq_upcoming)

    html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>mentviro Dashboard</title>
<style>body{{font-family:-apple-system,sans-serif;background:#0d0d0d;color:#e0e0e0;margin:0;padding:24px}}
h1{{color:#fff;margin-bottom:4px}}.sub{{color:#888;margin-bottom:32px;font-size:14px}}
h2{{color:#c0c0c0;border-bottom:1px solid #333;padding-bottom:6px}}
table{{border-collapse:collapse;width:100%;margin-bottom:40px}}
th{{text-align:left;color:#888;font-weight:600;font-size:13px;padding:8px 12px;border-bottom:1px solid #333}}
td{{padding:10px 12px;border-bottom:1px solid #222;font-size:14px}}
tr:hover td{{background:#1a1a1a}}</style></head><body>
<h1>mentviro Content Dashboard</h1>
<p class="sub">Stand: {today} &nbsp;·&nbsp;
  Posting: Reel 07:00 | Stories 12:00 | Carousel 18:00 CET &nbsp;·&nbsp;
  {len(upcoming)} Posts + {len(sq_upcoming)} Story-Pairs ausstehend</p>
<h2>📅 Kommende Posts</h2>
<table><tr><th>Datum</th><th>Typ</th><th>Thema</th></tr>
{rows_up or '<tr><td colspan="3" style="color:#666">Keine ausstehenden Posts</td></tr>'}
</table>
<h2>💬 Kommende Story-Paare</h2>
<table><tr><th>Datum</th><th>Typ</th><th>Zitat (Vorschau)</th></tr>
{sched_html or '<tr><td colspan="3" style="color:#666">Keine ausstehenden Story-Paare</td></tr>'}
</table>
<h2>✅ Zuletzt veröffentlicht</h2>
<table><tr><th>Datum</th><th>Typ</th><th>Thema + Performance</th></tr>
{rows_re or '<tr><td colspan="3" style="color:#666">Noch nichts veröffentlicht</td></tr>'}
</table></body></html>"""

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Dashboard updated")

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  mentviro [{RUN_MODE.upper()}] --- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    plan = load_plan()
    init_colors(plan)
    check_session_age()

    # Fetch insights + timing stats
    try:
        fetch_and_store_insights(plan)
        plan = load_plan()
        update_posting_time_stats(plan)
    except Exception as e:
        print(f"Insights/stats error: {e}")

    # Refill content if low
    check_and_refill_content(plan)
    plan = load_plan()

    # ── REEL MODE ────────────────────────────────────────────────────────────
    if RUN_MODE == "reel":
        post = get_todays_post(plan, "reel")
        if not post:
            print("No pending reel. Skipping.")
            return
        today = date.today().isoformat()
        if post["date"] < today:
            days_late = (date.today() - date.fromisoformat(post["date"])).days
            print(f"  Catching up: Day {post['day']} from {post['date']} ({days_late}d late)")
            send_telegram(
                f"♻️ <b>mentviro-bot</b>: Hole verpassten REEL nach\n"
                f"Tag {post['day']} · {days_late} Tag(e) Verzögerung\n"
                f"Thema: {post.get('topic','')}"
            )
        print(f"Day {post['day']} REEL: {post['topic']}\n")
        try:
            media_id = run_reel(post, plan)
            if DRY_RUN:
                print("\nDRY_RUN: Reel-Vorschau erstellt, NICHTS gepostet. "
                      f"Post Tag {post['day']} bleibt 'pending'.")
                return
            story_id = run_attached_story(post)
            post["status"]       = "published"
            post["post_id"]      = media_id
            post["story_id"]     = story_id
            post["published_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            save_plan(plan)
            generate_dashboard(load_plan())
            send_telegram(f"Reel Day {post['day']} live!\n{post['topic']}\nID: <code>{media_id}</code>")
            print(f"\nDone! Reel: {media_id} | Story: {story_id}")
        except Exception as e:
            import traceback; traceback.print_exc()
            send_telegram(f"FEHLER Reel Day {post.get('day','?')}\n<code>{type(e).__name__}: {e}</code>")
            sys.exit(1)

    # ── CAROUSEL MODE ────────────────────────────────────────────────────────
    elif RUN_MODE == "carousel":
        post = get_todays_post(plan, "carousel")
        if not post:
            print("No pending carousel. Skipping.")
            return
        today = date.today().isoformat()
        if post["date"] < today:
            days_late = (date.today() - date.fromisoformat(post["date"])).days
            print(f"  Catching up: Day {post['day']} from {post['date']} ({days_late}d late)")
            send_telegram(
                f"♻️ <b>mentviro-bot</b>: Hole verpassten CAROUSEL nach\n"
                f"Tag {post['day']} · {days_late} Tag(e) Verzögerung\n"
                f"Thema: {post.get('topic','')}"
            )
        print(f"Day {post['day']} CAROUSEL: {post['topic']}\n")
        try:
            media_id = run_carousel(post, plan)
            story_id = run_attached_story(post)
            post["status"]       = "published"
            post["post_id"]      = media_id
            post["story_id"]     = story_id
            post["published_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            save_plan(plan)
            generate_dashboard(load_plan())
            send_telegram(f"Carousel Day {post['day']} live!\n{post['topic']}\nID: <code>{media_id}</code>")
            print(f"\nDone! Carousel: {media_id} | Story: {story_id}")
        except Exception as e:
            import traceback; traceback.print_exc()
            send_telegram(f"FEHLER Carousel Day {post.get('day','?')}\n<code>{type(e).__name__}: {e}</code>")
            sys.exit(1)

    # ── STORIES MODE ─────────────────────────────────────────────────────────
    elif RUN_MODE == "stories":
        plan = load_plan()
        sd = get_todays_stories(plan)
        if not sd:
            print("No pending story-pair. Skipping.")
            return
        print(f"Day {sd.get('day','?')} STORIES\n")
        try:
            quote_id, tips_id = run_daily_stories(plan)
            generate_dashboard(load_plan())
            send_telegram(
                f"Stories Day {sd.get('day','?')} live!\n"
                f"Zitat: <code>{quote_id}</code>\n"
                f"Tipps: <code>{tips_id}</code>"
            )
            print(f"\nDone! Quote: {quote_id} | Tips: {tips_id}")
        except Exception as e:
            import traceback; traceback.print_exc()
            send_telegram(f"FEHLER Stories\n<code>{type(e).__name__}: {e}</code>")
            sys.exit(1)

    else:
        print(f"Unknown RUN_MODE: {RUN_MODE}")
        sys.exit(1)

if __name__ == "__main__":
    main()
