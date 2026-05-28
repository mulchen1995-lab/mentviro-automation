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

# Cross-platform temp dir
TMPDIR   = tempfile.gettempdir()
RUN_MODE = os.getenv("RUN_MODE", "carousel")   # carousel | reel | stories

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
    with open(PLAN_FILE, encoding='utf-8') as f:
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

# ─── SESSION AGE CHECK ───────────────────────────────────────────────────────

def check_session_age():
    session_json = os.environ.get("IG_SESSION", "")
    if not session_json:
        return
    try:
        data      = json.loads(session_json)
        last_login = data.get("last_login", 0)
        if not last_login:
            return
        age_days = (time.time() - last_login) / 86400
        print(f"  IG session age: {age_days:.0f} days", end="")
        if age_days > 45:
            send_telegram(
                f"<b>mentviro-bot</b>: IG-Session ist <b>{age_days:.0f} Tage</b> alt!\n"
                "Bitte <code>refresh_ig_session.py</code> ausfuehren."
            )
            print(" — ALERT sent")
        else:
            print(" — OK")
    except Exception as e:
        print(f"\n  Session-age check failed: {e}")

# ─── FONT ────────────────────────────────────────────────────────────────────

def fnt(size, bold=False):
    weight = "Bold" if bold else "Regular"
    candidates = [
        f"/usr/share/fonts/truetype/Montserrat-{weight}.ttf",
        f"/usr/local/share/fonts/Montserrat-{weight}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"C:/Windows/Fonts/Montserrat-{weight}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        os.path.join(os.path.dirname(__file__), "assets", f"Montserrat-{weight}.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
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

def text_width(text, font_size, bold=False):
    return fnt(font_size, bold).getbbox(text)[2]

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
    paste_logo(img_rgba, w - MARGIN + 10, h - 78, size=80)

def dark_overlay(base_rgb, w=W, h=H, strength=195):
    ov = Image.new("RGBA", (w, h))
    od = ImageDraw.Draw(ov)
    for y in range(h):
        a = int(strength - 30 + (y / h) * 30)
        od.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(base_rgb.convert("RGBA"), ov)

# ─── PEXELS ──────────────────────────────────────────────────────────────────

def pexels_portrait(query, target_w=W, target_h=H):
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "orientation": "portrait", "per_page": 5, "size": "large"},
            timeout=30)
        if r.status_code != 200:
            return None
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos[:min(3, len(photos))])
        url   = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
        img   = Image.open(io.BytesIO(requests.get(url, timeout=30).content)).convert("RGB")
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

def pexels_video(query):
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 5, "orientation": "portrait"},
            timeout=30)
        for v in r.json().get("videos", []):
            for vf in v.get("video_files", []):
                if "mp4" in vf.get("file_type", ""):
                    return vf["link"]
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
        paste_logo(img, w // 2, int(h * 0.23), size=200)
        content_top = int(h * 0.42)

    y = content_top + 30
    base_title_sz = 74 if not is_cover else 68
    for line in slide.get("title", []):
        # Auto-shrink font until line fits within safe area
        sz = fit_font_size(line, max_text_w, base_title_sz, bold=True)
        d.text((MARGIN, y), line, font=fnt(sz, True), fill=COLORS["white"])
        bb = fnt(sz, True).getbbox(line)
        y += (bb[3] - bb[1]) + 14
    y += 36
    for line in slide.get("body", []):
        sz = fit_font_size(line, max_text_w, 40, bold=False)
        d.text((MARGIN, y), line, font=fnt(sz), fill=BODY)
        bb = fnt(sz).getbbox(line)
        y += (bb[3] - bb[1]) + 12

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
    paste_logo(img, SW // 2, SH // 2 - 260, size=200)

    texts = post.get("story_text", ["NEU", post.get("topic", ""), "Jetzt ansehen"])
    max_text_w = SW - MARGIN * 2
    y = SH // 2 - 60
    for j, line in enumerate(texts):
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
    text   = q_data.get("text", "")
    author = q_data.get("author", "")
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

    # Logo + footer
    paste_logo(img, SW // 2, SH - 160, size=90)
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
    title  = t_data.get("title", "3 Tipps")
    items  = t_data.get("items", ["", "", ""])[:3]
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

    # Logo + footer
    paste_logo(img, SW // 2, SH - 160, size=90)
    d.text((SW // 2 - 90, SH - 100), "@mentviro", font=fnt(30, True), fill=SIL)
    d.rectangle([(0, SH-7), (SW, SH)], fill=SIL)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

# ─── INSTAGRAM CLIENT ────────────────────────────────────────────────────────

_ig_client      = None
_ig_login_error = None   # Set once login fails — prevents repeated retry spam

def get_ig_client():
    global _ig_client, _ig_login_error
    # If we already know login is broken this run, raise immediately (no spam)
    if _ig_login_error is not None:
        raise _ig_login_error
    if _ig_client is not None:
        return _ig_client
    from instagrapi import Client
    username = os.environ.get("IG_USERNAME", "mentviro")
    password = os.environ.get("IG_PASSWORD")
    if not password:
        raise RuntimeError("IG_PASSWORD not set")
    session_json = os.environ.get("IG_SESSION", "")
    if session_json:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(session_json)
            tmp_path = f.name
        cl = Client()
        cl.delay_range = [1, 3]
        cl.load_settings(tmp_path)
        os.unlink(tmp_path)
        # Validate the session — if it's dead, try one relogin
        try:
            cl.get_timeline_feed()
            print("  IG session loaded + validated OK")
        except Exception as val_err:
            print(f"  IG session stale ({val_err}) — attempting relogin...")
            send_telegram(
                "<b>mentviro-bot</b>: IG-Session abgelaufen — versuche Relogin...\n"
                f"<code>{val_err}</code>"
            )
            try:
                cl = Client()
                cl.delay_range = [1, 3]
                cl.login(username, password)
                print("  IG relogin OK")
                send_telegram("<b>mentviro-bot</b>: Relogin erfolgreich! ✅")
            except Exception as relogin_err:
                msg = (
                    "<b>mentviro-bot</b>: ⛔ Relogin fehlgeschlagen — IP geblockt!\n"
                    f"<code>{relogin_err}</code>\n\n"
                    "Führe aus (reconnectet Fritz!Box + erneuert Session):\n"
                    "<code>python \"D:\\Claude Council\\refresh_ig_session.py\" --fritz</code>"
                )
                send_telegram(msg)
                print(f"  Relogin failed: {relogin_err}")
                _ig_login_error = relogin_err
                raise relogin_err
        _ig_client = cl
        return cl
    cl = Client()
    cl.delay_range = [1, 3]
    try:
        cl.login(username, password)
        print("  IG login OK")
    except Exception as login_err:
        _ig_login_error = login_err
        raise login_err
    _ig_client = cl
    return cl

# ─── ENGAGEMENT TRACKING ─────────────────────────────────────────────────────

def fetch_and_store_insights(plan):
    updated = False
    cl      = None
    cutoff  = (date.today() - timedelta(days=30)).isoformat()
    for post in plan["posts"]:
        if post.get("status") != "published" or not post.get("post_id"):
            continue
        if post.get("insights") or post.get("date", "9999") < cutoff:
            continue
        try:
            if cl is None:
                cl = get_ig_client()
            info = cl.media_info(int(post["post_id"]))
            post["insights"] = {
                "likes":    getattr(info, "like_count",    0),
                "comments": getattr(info, "comment_count", 0),
            }
            score = post["insights"]["likes"] * 2 + post["insights"]["comments"] * 5
            print(f"  Insights Day {post['day']} ({post['type']}): "
                  f"{post['insights']['likes']}L {post['insights']['comments']}C score={score}")
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
    scored.sort(reverse=True)
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
    prompt = f"""Du bist viraler Content Creator fuer @mentviro (Business Mindset, Instagram, Deutsch).

Erstelle GENAU {DAYS} Tages-Pakete. Jedes Paket enthaelt:
  1. Ein REEL
  2. Ein CAROUSEL
  3. Ein STORY-PAAR (Zitat + 3 Tipps)

BEREITS BEHANDELTE THEMEN (NICHT wiederholen):
{chr(10).join(f'- {t}' for t in existing_topics[-20:])}
{trend_context}{engagement_context}
REGELN:
- Hooks: "Niemand redet darueber", "Das sagt dir kein Banker", "Bittere Wahrheit", "Hoer sofort damit auf"
- Zahlen-Listicles, Curiosity-Gap, kontroverse Aussagen
- Zielgruppe: 20-40 Jahre, Vermoegensaufbau, Deutschland
- PEXELS QUERIES: cinematic, dunkel, aesthetisch. NIEMALS: businessman, office, suit, handshake
- Caption: emotional, provokant, exakt 15 Hashtags aus: {' '.join(hashtag_sample)} plus immer #mentviro
- Zitat: echtes oder passendes fiktives Zitat, max 25 Woerter, Business/Erfolg/Mindset-Thema
- 3 Tipps: kurz, actionable, max 12 Woerter pro Tipp
- story_poll: kurze Ja/Nein oder Entweder/Oder Frage (max 35 Zeichen)

Gib NUR ein JSON-Array mit {DAYS} Objekten aus. Kein Text davor/danach.

Schema fuer jedes Objekt:
{{
  "day": {last_day+1},
  "date": "{(start_date).isoformat()}",
  "reel": {{
    "topic": "...", "status": "pending", "hook": "...",
    "script": ["Satz 1","Satz 2","Satz 3","Satz 4","Satz 5","Folge @mentviro."],
    "caption": "... #mentviro ...",
    "pexels_video_query": "dark cinematic query",
    "story_text": ["NEUES REEL","Zeile 1","Zeile 2","Jetzt anschauen"],
    "story_poll": "Kurze Frage?"
  }},
  "carousel": {{
    "topic": "...", "status": "pending", "hook": "...",
    "slides": [
      {{"badge":null,"num":null,"title":["..."],"body":["..."],"is_cover":true}},
      {{"badge":"PUNKT #1","num":"1 / N","title":["..."],"body":["..."]}},
      ...,
      {{"badge":"FOLGE UNS","num":null,"title":["Mehr Mindset","& Money Moves"],"body":["Folge @mentviro","fuer taeglich mehr."]}}
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
      "text": "Das Zitat hier. Max 25 Woerter.",
      "author": "Name oder @mentviro"
    }},
    "tips": {{
      "title": "Kurzer Titel fuer den Tag",
      "items": ["Tipp 1 max 12 Woerter","Tipp 2 max 12 Woerter","Tipp 3 max 12 Woerter"]
    }}
  }}
}}"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
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
            d = (start_date + timedelta(days=i)).isoformat()
            day_num = last_day + i + 1

            style = "gold" if day_num % 2 == 0 else "silver"

            reel = pkg.get("reel", {})
            reel.update({"day": day_num, "date": d, "type": "reel", "status": "pending", "style": style})
            new_posts.append(reel)

            car = pkg.get("carousel", {})
            car.update({"day": day_num, "date": d, "type": "carousel", "status": "pending", "style": style})
            new_posts.append(car)

            stories = pkg.get("stories", {})
            stories.update({"day": day_num, "date": d, "status": "pending", "style": style})
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
    tmp_paths      = []
    try:
        for i, slide in enumerate(post["slides"]):
            print(f"  Slide {i+1}/{len(post['slides'])}...", end=" ", flush=True)
            bg_img = None
            if not slide.get("is_cover") and pexels_queries:
                bg_img = pexels_portrait(pexels_queries[min(i, len(pexels_queries)-1)])
            img_bytes = build_carousel_slide(slide, bg_img)
            path = f"{TMPDIR}/mentviro_d{post['day']}_s{i+1}.jpg"
            with open(path, "wb") as f:
                f.write(img_bytes)
            tmp_paths.append(path)
            print("ok")
            time.sleep(0.4)

        print("  Uploading carousel...")
        cl    = get_ig_client()
        media = cl.album_upload(tmp_paths, caption=post["caption"])
        print(f"  Carousel live! ID: {media.pk}")
        return str(media.pk)
    finally:
        for p in tmp_paths:
            try: os.unlink(p)
            except Exception: pass

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
    tmp_paths = []
    try:
        for i, slide in enumerate(slides):
            print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
            bg_img = None if slide.get("is_cover") else pexels_portrait(pq, target_w=SW, target_h=SH)
            img_bytes = build_carousel_slide(slide, bg_img, w=SW, h=SH)
            path = f"{TMPDIR}/mentviro_reel_fb_d{post['day']}_s{i+1}.jpg"
            with open(path, "wb") as f:
                f.write(img_bytes)
            tmp_paths.append(path)
            print("ok")
            time.sleep(0.4)
        cl    = get_ig_client()
        media = cl.album_upload(tmp_paths, caption=post["caption"])
        print(f"  Reel-Carousel live! ID: {media.pk}")
        return str(media.pk)
    finally:
        for p in tmp_paths:
            try: os.unlink(p)
            except Exception: pass

def run_reel(post, plan):
    set_build_accent(post)
    import subprocess
    print(f"Building reel: {post['topic']}")

    # 1. Voiceover (ElevenLabs) — save to disk so ffmpeg can mix it in
    script_text = " ".join(post.get("script", [post.get("hook", "")]))
    audio_path  = f"{TMPDIR}/mentviro_reel_d{post['day']}_voice.mp3"
    audio_ok    = False
    try:
        el_key = os.environ.get("ELEVENLABS_API_KEY",
                                "1071b6e53cb6e950c63d8e11a05dfa7b07764275cab9fda0ce63104a421c2d37")
        el_r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
            headers={"xi-api-key": el_key, "Content-Type": "application/json"},
            json={"text": script_text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            timeout=60)
        if el_r.status_code == 200:
            with open(audio_path, "wb") as af:
                af.write(el_r.content)
            audio_ok = True
            print(f"  Voiceover: OK ({len(el_r.content)//1024} KB)")
        else:
            print(f"  Voiceover: {el_r.status_code}")
    except Exception as e:
        print(f"  Voiceover error: {e}")

    # 2. Pexels video
    video_url = pexels_video(post.get("pexels_video_query", "cinematic dark city night"))
    if not video_url:
        print("  No video found — fallback to 9:16 carousel")
        return _reel_as_carousel(post, plan)

    raw_path   = f"{TMPDIR}/mentviro_reel_d{post['day']}_raw.mp4"
    conv_path  = f"{TMPDIR}/mentviro_reel_d{post['day']}.mp4"
    thumb_path = conv_path + ".jpg"

    r = requests.get(video_url, timeout=120, stream=True)
    with open(raw_path, "wb") as f:
        for chunk in r.iter_content(65536): f.write(chunk)
    print(f"  Downloaded: {os.path.getsize(raw_path)/1024/1024:.1f} MB")

    # 3. ffmpeg: scale + loop + mix voiceover
    try:
        probe    = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", raw_path],
                                  capture_output=True, text=True, timeout=30)
        duration = float((probe.stdout.strip().split("\n")[0]) or "0")
        loop_args = []
        if duration < 5:
            loops     = max(1, int(20 / max(duration, 0.1)))
            loop_args = ["-stream_loop", str(loops)]

        if audio_ok:
            # Mix voiceover as audio track — video loops visually, audio plays once
            subprocess.run(
                ["ffmpeg", "-y"] + loop_args + [
                    "-i", raw_path,
                    "-i", audio_path,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-t", "60", conv_path],
                check=True, capture_output=True, timeout=240)
        else:
            # No audio — just scale/loop the video
            subprocess.run(
                ["ffmpeg", "-y"] + loop_args + [
                    "-i", raw_path,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                           "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-an", "-t", "30", conv_path],
                check=True, capture_output=True, timeout=240)

        subprocess.run(
            ["ffmpeg", "-y", "-i", conv_path, "-ss", "0", "-vframes", "1", "-q:v", "2", thumb_path],
            check=True, capture_output=True, timeout=30)
        print(f"  Re-encoded: {os.path.getsize(conv_path)/1024/1024:.1f} MB (audio: {audio_ok})")
        final_video = conv_path
    except Exception as e:
        print(f"  ffmpeg failed: {e} — using raw")
        final_video = raw_path
        thumb_path  = None

    try:
        cl    = get_ig_client()
        media = cl.clip_upload(final_video, caption=post["caption"],
                               thumbnail=thumb_path if thumb_path and os.path.exists(thumb_path) else None)
        print(f"  Reel live! ID: {media.pk}")
        return str(media.pk)
    except Exception as e:
        print(f"  clip_upload failed ({type(e).__name__}): {e} — fallback")
        return _reel_as_carousel(post, plan)
    finally:
        for p in [raw_path, conv_path, thumb_path, audio_path]:
            try:
                if p and os.path.exists(p): os.unlink(p)
            except Exception: pass

# ─── STORY WORKFLOWS ─────────────────────────────────────────────────────────

def run_attached_story(post):
    """Post the story that is attached to a carousel/reel."""
    print("  Posting attached story...")
    story_bytes = build_attached_story(post)
    path = f"{TMPDIR}/mentviro_story_d{post['day']}.jpg"
    with open(path, "wb") as f:
        f.write(story_bytes)
    try:
        cl = get_ig_client()
        stickers = []
        poll_q   = post.get("story_poll", "")
        if poll_q:
            try:
                from instagrapi.types import StoryPoll
                stickers = [StoryPoll(x=0.5, y=0.72, width=0.9, height=0.14,
                                      question=poll_q,
                                      tallies=[{"text": "Ja"}, {"text": "Nein"}])]
            except Exception:
                pass
        media = cl.photo_upload_to_story(path, stickers=stickers) if stickers \
            else cl.photo_upload_to_story(path)
        print(f"  Story live! ID: {media.pk}")
        return str(media.pk)
    finally:
        try: os.unlink(path)
        except Exception: pass

def run_daily_stories(plan):
    """Post today's standalone quote story + tips story."""
    sd = get_todays_stories(plan)
    if not sd:
        print("No pending stories for today.")
        return None, None

    set_build_accent(sd)
    print(f"Building daily stories for: {sd.get('date')}")
    cl = get_ig_client()

    # Quote story
    print("  Quote story...", end=" ", flush=True)
    quote_id = None
    try:
        qbytes = build_quote_story(sd)
        qpath  = f"{TMPDIR}/mentviro_quote_{sd['day']}.jpg"
        with open(qpath, "wb") as f:
            f.write(qbytes)
        media    = cl.photo_upload_to_story(qpath)
        quote_id = str(media.pk)
        print(f"ok (ID: {quote_id})")
        os.unlink(qpath)
    except Exception as e:
        print(f"failed: {e}")

    time.sleep(3)

    # Tips story
    print("  Tips story...", end=" ", flush=True)
    tips_id = None
    try:
        tbytes = build_tips_story(sd)
        tpath  = f"{TMPDIR}/mentviro_tips_{sd['day']}.jpg"
        with open(tpath, "wb") as f:
            f.write(tbytes)
        media   = cl.photo_upload_to_story(tpath)
        tips_id = str(media.pk)
        print(f"ok (ID: {tips_id})")
        os.unlink(tpath)
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
