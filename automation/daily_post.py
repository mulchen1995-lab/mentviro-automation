#!/usr/bin/env python3
"""
mentviro Daily Instagram Automation
Runs daily via GitHub Actions cron at 18:00 CET
Posts carousels, reels and stories to @mentviro via instagrapi.

Improvements:
  1. Session-age check + Telegram alert when session is aging
  2. Better reel fallback (9:16 vertical carousel slides)
  3. Telegram failure/success notifications
  4. Montserrat font (falls back to DejaVu)
  5. Engagement tracking + feedback loop into Gemini prompt
  6. Trending hashtag pool injected into Gemini
  7. Optimal posting-time tracking (data collection)
  8. Story poll sticker
  9. HTML dashboard (docs/index.html) committed after each run
"""

import os, sys, json, io, time, random, requests, base64, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Cross-platform temp directory (works on Linux CI and Windows self-hosted)
TMPDIR = tempfile.gettempdir()

# â”€â”€â”€ CONFIG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PLAN_FILE  = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_FILE  = os.path.join(os.path.dirname(__file__), "assets", "mentviro_logo.png")
LOGO_URL   = os.getenv("MENTVIRO_LOGO_URL", "")
_LOGO_B64  = ""

W, H   = 1080, 1350   # carousel / single image
SW, SH = 1080, 1920   # story / reel

# â”€â”€â”€ PLAN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_plan():
    with open(PLAN_FILE) as f:
        return json.load(f)

def save_plan(plan):
    with open(PLAN_FILE, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

def get_todays_post(plan):
    today = date.today().isoformat()
    for post in plan["posts"]:
        if post["date"] == today and post["status"] == "pending":
            return post
    for post in plan["posts"]:
        if post["status"] == "pending":
            return post
    return None

# â”€â”€â”€ TELEGRAM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def send_telegram(message: str):
    """Send a Telegram notification. Fails silently if not configured."""
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

# â”€â”€â”€ SESSION AGE CHECK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_session_age():
    """Warn via Telegram if the IG session is older than 45 days."""
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
            msg = (
                f"âš ï¸ <b>mentviro-bot</b>: IG-Session ist <b>{age_days:.0f} Tage</b> alt!\n"
                "Bitte <code>regen_ig_session.py</code> ausfÃ¼hren und "
                "das <b>IG_SESSION</b> GitHub-Secret aktualisieren."
            )
            send_telegram(msg)
            print(" â€” âš  ALERT sent via Telegram")
        else:
            print(" â€” OK")
    except Exception as e:
        print(f"\n  âš  Session-age check failed: {e}")

# â”€â”€â”€ FONT HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def fnt(size, bold=False):
    weight = "Bold" if bold else "Regular"
    candidates = [
        # Montserrat (downloaded by workflow)
        f"/usr/share/fonts/truetype/Montserrat-{weight}.ttf",
        f"/usr/local/share/fonts/Montserrat-{weight}.ttf",
        # DejaVu fallback
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/local/share/fonts/DejaVuSans{'-Bold' if bold else ''}.ttf",
        # Windows — Montserrat if installed, Arial fallback
        f"C:/Windows/Fonts/Montserrat-{weight}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
        # Local assets fallback
        os.path.join(os.path.dirname(__file__), "assets",
                     f"Montserrat-{weight}.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# â”€â”€â”€ LOGO WATERMARK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_logo_cache = None

def get_logo_asset(size=90):
    global _logo_cache
    if _logo_cache and _logo_cache[0] == size:
        return _logo_cache[1]

    if os.path.exists(LOGO_FILE):
        try:
            logo = Image.open(LOGO_FILE).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    if _LOGO_B64:
        try:
            logo = Image.open(io.BytesIO(base64.b64decode(_LOGO_B64))).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    if LOGO_URL:
        try:
            r = requests.get(LOGO_URL, timeout=10)
            logo = Image.open(io.BytesIO(r.content)).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    # Fallback: draw primitive M symbol
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

# â”€â”€â”€ DESIGN HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

def draw_base_frame(img_rgba, w=W, h=H, is_bw=False, slide_num=None, badge=None):
    d    = ImageDraw.Draw(img_rgba)
    ACC  = COLORS["white"] if is_bw else COLORS["silver"]
    BODY = (180, 180, 180) if is_bw else COLORS["dark"]

    d.rectangle([(0, 0), (w, 5)], fill=ACC)
    d.rectangle([(0, h-5), (w, h)], fill=ACC)

    d.text((60, 28), "MENTVIRO", font=fnt(28, True), fill=ACC)
    d.text((60, 62), "BUSINESS MINDSET", font=fnt(17), fill=BODY)
    d.rectangle([(60, 96), (w-60, 98)], fill=(70, 70, 70))

    if badge:
        d.text((60, 120), badge, font=fnt(30, True), fill=ACC)

    if slide_num:
        bb = fnt(26).getbbox(slide_num)
        d.text((w - 60 - (bb[2]-bb[0]), 124), slide_num, font=fnt(26), fill=BODY)

    d.rectangle([(60, h-120), (w-60, h-116)], fill=(60, 60, 60))
    d.text((60, h-100), "@mentviro", font=fnt(30, True), fill=COLORS["white"])
    paste_logo(img_rgba, w - 80, h - 78, size=80)

def dark_overlay(base_rgb, w=W, h=H, strength=195):
    ov = Image.new("RGBA", (w, h))
    od = ImageDraw.Draw(ov)
    for y in range(h):
        a = int(strength - 30 + (y / h) * 30)
        od.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(base_rgb.convert("RGBA"), ov)

# â”€â”€â”€ PEXELS HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def pexels_portrait(query, target_w=W, target_h=H):
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "orientation": "portrait", "per_page": 5, "size": "large"},
            timeout=30,
        )
        if r.status_code != 200:
            return None
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos[:min(3, len(photos))])
        url   = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
        resp  = requests.get(url, timeout=30)
        img   = Image.open(io.BytesIO(resp.content)).convert("RGB")
        src_w, src_h = img.size
        target_ratio = target_w / target_h
        src_ratio    = src_w / src_h
        if src_ratio > target_ratio:
            new_w  = int(src_h * target_ratio)
            offset = (src_w - new_w) // 2
            img    = img.crop((offset, 0, offset + new_w, src_h))
        elif src_ratio < target_ratio:
            new_h = int(src_w / target_ratio)
            img   = img.crop((0, 0, src_w, new_h))
        return img.resize((target_w, target_h), Image.LANCZOS)
    except Exception as e:
        print(f"  âš  Pexels portrait error: {e}")
        return None

def pexels_video(query):
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "per_page": 5, "orientation": "portrait"},
            timeout=30,
        )
        for v in r.json().get("videos", []):
            for vf in v.get("video_files", []):
                if "mp4" in vf.get("file_type", ""):
                    return vf["link"]
    except Exception as e:
        print(f"  âš  Pexels video error: {e}")
    return None

# â”€â”€â”€ CAROUSEL BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_carousel_slide(slide, bg_img=None, w=W, h=H):
    is_cover = slide.get("is_cover", False)
    is_bw    = is_cover

    if bg_img is not None:
        bg  = bg_img.convert("L").convert("RGB") if is_bw else bg_img
        img = dark_overlay(bg, w=w, h=h, strength=198)
    elif is_cover:
        img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    else:
        img = Image.new("RGBA", (w, h), tuple(COLORS["bg"]) + (255,))

    draw_base_frame(img, w=w, h=h, is_bw=is_bw,
                    slide_num=slide.get("num"), badge=slide.get("badge"))
    d    = ImageDraw.Draw(img)
    BODY = (175, 175, 175)

    content_top = 165 + (30 if slide.get("badge") else 0)

    if is_cover:
        paste_logo(img, w // 2, int(h * 0.23), size=200)
        content_top = int(h * 0.42)

    title_size = 74 if not is_cover else 68
    y = content_top + 30
    for line in slide.get("title", []):
        d.text((60, y), line, font=fnt(title_size, True), fill=COLORS["white"])
        bb = fnt(title_size, True).getbbox(line)
        y += (bb[3] - bb[1]) + 14

    y += 36
    for line in slide.get("body", []):
        d.text((60, y), line, font=fnt(40), fill=BODY)
        bb = fnt(40).getbbox(line)
        y += (bb[3] - bb[1]) + 12

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

# â”€â”€â”€ STORY BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_story(post):
    query = (post.get("pexels_queries") or ["dark cityscape night cinematic"])[0]
    bg    = pexels_portrait(query, target_w=SW, target_h=SH)
    if bg is None:
        bg = Image.new("RGB", (SW, SH), (0, 0, 0))

    ov = Image.new("RGBA", (SW, SH))
    od = ImageDraw.Draw(ov)
    for y in range(SH):
        a = int(155 + (y / SH) * 80)
        od.line([(0, y), (SW, y)], fill=(0, 0, 0, a))
    story_rgba = Image.alpha_composite(bg.convert("RGBA"), ov)
    d = ImageDraw.Draw(story_rgba)

    SILVER = COLORS["silver"]
    d.rectangle([(0, 0), (SW, 7)], fill=SILVER)
    d.text((60, 55), "@mentviro", font=fnt(40, True), fill=SILVER)
    d.rectangle([(60, 108), (200, 115)], fill=SILVER)

    paste_logo(story_rgba, SW // 2, SH // 2 - 260, size=200)

    texts = post.get("story_text", ["NEU", post.get("topic", ""), "â†’ Sieh dir den Post an"])
    y = SH // 2 - 60
    for j, line in enumerate(texts):
        sz   = 34 if j == 0 else (84 if j < len(texts)-1 else 46)
        bold = j > 0
        col  = SILVER if j == 0 else (COLORS["white"] if j < len(texts)-1 else SILVER)
        d.text((60, y), line, font=fnt(sz, bold), fill=col)
        bb = fnt(sz, bold).getbbox(line)
        y += (bb[3] - bb[1]) + 12

    d.rectangle([(0, SH-7), (SW, SH)], fill=SILVER)

    buf = io.BytesIO()
    story_rgba.convert("RGB").save(buf, "JPEG", quality=93)
    buf.seek(0)
    return buf.read()

# â”€â”€â”€ INSTAGRAM CLIENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_ig_client = None

def get_ig_client():
    global _ig_client
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
        print("  Instagram: session loaded from IG_SESSION")
        _ig_client = cl
        return cl

    cl = Client()
    cl.delay_range = [1, 3]
    cl.login(username, password)
    print("  Instagram: password login OK")
    _ig_client = cl
    return cl

# â”€â”€â”€ ENGAGEMENT TRACKING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def fetch_and_store_insights(plan):
    """
    Fetch like/comment counts for recently published posts that don't have
    insights yet. Stores them in plan["posts"][n]["insights"] and saves.
    Uses media_info() which works on any account type.
    """
    updated = False
    cl      = None
    cutoff  = (date.today() - timedelta(days=30)).isoformat()

    for post in plan["posts"]:
        if post.get("status") != "published":
            continue
        if post.get("insights"):
            continue
        if not post.get("post_id"):
            continue
        if post.get("date", "9999") < cutoff:
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
            print(f"  Insights Day {post['day']}: "
                  f"{post['insights']['likes']} likes, "
                  f"{post['insights']['comments']} comments  (score {score})")
            updated = True
        except Exception as e:
            print(f"  âš  Insights Day {post['day']}: {e}")

    if updated:
        save_plan(plan)

def get_engagement_context(plan):
    """
    Return a string describing which recent posts performed best.
    Injected into the Gemini prompt so new posts learn from what worked.
    """
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
        lines.append(
            f"  {'âœ…' if score > 20 else 'âž¡'} '{p['topic']}' ({p['type']}) â€” "
            f"{ins.get('likes',0)} Likes, {ins.get('comments',0)} Comments "
            f"[Score {score}]"
        )
    lines.append("\nâ†’ Baue auf Themen mit hohem Score auf. "
                 "Wiederhole erfolgreiche Formate (Hook-Stil, Struktur, Kontrast).")
    return "\n".join(lines) + "\n"

# â”€â”€â”€ TREND + HASHTAG CONTEXT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Curated high-performing German business/finance hashtags
HASHTAG_POOL = [
    "#geldanlage", "#finanztipps", "#investieren", "#etfinvestor", "#aktien",
    "#vermÃ¶gensaufbau", "#passiveseinkommen", "#finanziellefreiheit", "#reichwerden",
    "#businessmindset", "#erfolgsmentalitÃ¤t", "#unternehmertum", "#selbststÃ¤ndig",
    "#motivation", "#erfolgreich", "#mindset", "#successmindset", "#entrepreneur",
    "#finanzbildung", "#sparplan", "#depot", "#dividenden", "#bÃ¶rsenwissen",
    "#reichtum", "#wohlstand", "#businesstips", "#mentaltraining", "#zielsetzung",
    "#mentviro", "#businessmindset", "#moneyminds", "#wealthbuilding",
]

def get_trending_context():
    """
    Fetch current trending topics for DE finance/business via:
      1. Google Trends Daily RSS (top trending searches in Germany)
      2. Financial news RSS feeds (Handelsblatt, NTV Wirtschaft, Focus Money)
    Returns a formatted string injected into the Gemini prompt.
    All sources fail silently.
    """
    import xml.etree.ElementTree as ET
    lines   = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mentviro-bot/1.0)"}

    # 1. Google Trends Daily Trending Searches (DE)
    try:
        r = requests.get(
            "https://trends.google.com/trending/rss?geo=DE",
            timeout=12, headers=headers,
        )
        if r.status_code == 200:
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")[:15]
            trending = [item.findtext("title", "").strip() for item in items
                        if item.findtext("title", "").strip()]
            if trending:
                lines.append("GOOGLE TRENDS â€” Trending Searches Deutschland (heute):")
                for t in trending:
                    lines.append(f"  â€¢ {t}")
    except Exception as e:
        print(f"  âš  Google Trends RSS failed: {e}")

    # 2. Financial News RSS
    feeds = [
        ("Handelsblatt Finanzen", "https://www.handelsblatt.com/rss/finanzen"),
        ("NTV Wirtschaft",        "https://www.n-tv.de/wirtschaft/rss"),
        ("Focus Money",           "https://rss.focus.de/fol/xml/rss_folnews.xml"),
    ]
    headlines = []
    for name, url in feeds:
        try:
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code != 200:
                continue
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")[:4]
            for item in items:
                title = item.findtext("title", "").strip()
                if title:
                    headlines.append(title)
        except Exception:
            pass
    if headlines:
        lines.append("\nAKTUELLE WIRTSCHAFTS-HEADLINES (heute):")
        for h in headlines[:12]:
            lines.append(f"  â€¢ {h}")

    if not lines:
        return ""
    return "\n" + "\n".join(lines) + "\n"

# â”€â”€â”€ CONTENT AUTO-GENERATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_and_refill_content(plan):
    pending = [p for p in plan["posts"] if p["status"] == "pending"]
    if len(pending) >= 2:
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("âš  GEMINI_API_KEY not set â€” skipping auto-generation")
        return

    print(f"ðŸ“ Only {len(pending)} pending post(s) left â€” auto-generating 3 more via Gemini...")

    print("  Fetching trending context...")
    trend_context = get_trending_context()
    if trend_context:
        print(f"  Trends loaded ({len(trend_context)} chars)")
    else:
        print("  No trend data available â€” continuing without")

    engagement_context = get_engagement_context(plan)
    if engagement_context:
        print(f"  Engagement context: {len(engagement_context)} chars")

    existing_topics = [p["topic"] for p in plan["posts"]]
    last_day   = max(p["day"] for p in plan["posts"])
    last_date  = max(date.fromisoformat(p["date"]) for p in plan["posts"])
    last_type  = plan["posts"][-1]["type"] if plan["posts"] else "reel"

    start_date = last_date + timedelta(days=1)
    dates  = [(start_date + timedelta(days=i)).isoformat() for i in range(3)]
    types  = []
    t = last_type
    for _ in range(3):
        t = "reel" if t == "carousel" else "carousel"
        types.append(t)

    hashtag_sample = random.sample(HASHTAG_POOL, min(20, len(HASHTAG_POOL)))

    prompt = f"""Du bist viraler Content Creator fÃ¼r @mentviro (Business Mindset, Instagram, Deutsch).

Erstelle GENAU 3 neue Posts als JSON-Array. Nicht mehr, nicht weniger.

BEREITS BEHANDELTE THEMEN (NICHT wiederholen):
{chr(10).join(f'- {t}' for t in existing_topics)}
{trend_context}
WICHTIG ZU DEN TREND-DATEN: Greife aktuelle Trends und Headlines auf, wo sie passen.
VerknÃ¼pfe sie mit Business-Mindset-Perspektive. Nutze Ereignisse als Hook, nicht als Nachricht.
{engagement_context}
VIRALER CONTENT â€” PFLICHT:
- Hooks: "Niemand redet darÃ¼ber", "Das sagt dir kein Banker", "HÃ¶r sofort damit auf", "Die bittere Wahrheit Ã¼ber..."
- Kontroverse Aussagen die zum Kommentieren anregen
- Curiosity-Gap: Leser muss wissen wie es weitergeht
- Zahlen-Listicles: "5 Dinge die...", "3 Fehler warum..."
- Zielgruppe: 20â€“40 Jahre, VermÃ¶gensaufbau, Deutschland

VORGABEN:
- Types (Reihenfolge): {types}
- Tage: {last_day+1} bis {last_day+3}
- Daten: {dates[0]} bis {dates[2]}
- Sprache: Deutsch | Themen: Mindset, Finanzen, Investieren, Entrepreneurship
- PEXELS QUERIES: cinematic, dunkel, Ã¤sthetisch. NIEMALS: businessman, office, suit, handshake
  Gut: "dark foggy forest path moody", "aerial city night cinematic", "chess king macro shadow"
- Slide title[]: max 3 kurze Zeilen | body[]: max 2 Zeilen
- Caption: emotional, provokant, exakt 15 Hashtags aus dieser Liste (mix):
  {' '.join(hashtag_sample)}
  Plus immer: #mentviro
- story_poll: Kurze Ja/Nein oder Entweder/Oder Frage zum Post-Thema (max 40 Zeichen)
  Beispiele: "Schon mal Geld verloren?", "ETF oder Einzelaktien?", "Mindset oder Skills?"

Gib NUR das JSON-Array aus, kein Text davor/danach.

Carousel-Schema:
{{"day":N,"date":"YYYY-MM-DD","type":"carousel","topic":"...","status":"pending","hook":"...",
"slides":[
  {{"badge":null,"num":null,"title":["..."],"body":["..."],"is_cover":true}},
  {{"badge":"PUNKT #1","num":"1 / N","title":["..."],"body":["..."]}},
  ...,
  {{"badge":"FOLGE UNS","num":null,"title":["Mehr Mindset","& Money Moves"],"body":["Folge @mentviro","fÃ¼r tÃ¤glich mehr."]}}
],
"caption":"...","pexels_queries":["q1","q2","q3","q4","q5","q6"],
"story_text":["NEU AUF MENTVIRO","Zeile 1","Zeile 2","â†’ Sieh dir den Post an"],
"story_poll":"Kurze Frage?"}}

Reel-Schema:
{{"day":N,"date":"YYYY-MM-DD","type":"reel","topic":"...","status":"pending","hook":"...",
"script":["Satz 1","Satz 2","Satz 3","Satz 4","Satz 5","Folge @mentviro."],
"caption":"...","pexels_video_query":"dark cinematic query",
"story_text":["NEUES REEL","Zeile 1","Zeile 2","â†’ Schau jetzt"],
"story_poll":"Kurze Frage?"}}"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"content-type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": 8000, "temperature": 0.9}},
            timeout=120,
        )
        if r.status_code != 200:
            print(f"âš  Gemini API error {r.status_code}: {r.text[:300]}")
            return
        text  = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start == -1 or end == 0:
            print("âš  No JSON array in Gemini response")
            return
        new_posts = json.loads(text[start:end])
        plan["posts"].extend(new_posts)
        save_plan(plan)
        print(f"âœ… Auto-generated {len(new_posts)} new posts (Day {last_day+1}â€“{last_day+len(new_posts)})")
    except Exception as e:
        print(f"âš  Auto-generation failed: {e}")

# â”€â”€â”€ CAROUSEL WORKFLOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_carousel(post, plan):
    print(f"Building carousel: {post['topic']}")
    slides          = post["slides"]
    pexels_queries  = post.get("pexels_queries", [])
    tmp_paths       = []

    try:
        for i, slide in enumerate(slides):
            print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
            bg_img = None
            if not slide.get("is_cover") and pexels_queries:
                query  = pexels_queries[min(i, len(pexels_queries)-1)]
                bg_img = pexels_portrait(query)
            img_bytes = build_carousel_slide(slide, bg_img)
            path = f"{TMPDIR}/mentviro_d{post['day']}_s{i+1}.jpg"
            with open(path, "wb") as f:
                f.write(img_bytes)
            tmp_paths.append(path)
            print("ok")
            time.sleep(0.5)

        print("Uploading carousel to Instagram...")
        cl    = get_ig_client()
        media = cl.album_upload(tmp_paths, caption=post["caption"])
        print(f"  Carousel live! ID: {media.pk}")
        return str(media.pk)

    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass

# â”€â”€â”€ REEL WORKFLOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _wrap_title(text, max_len=26):
    if len(text) <= max_len:
        return [text]
    words  = text.split()
    lines, cur = [], []
    for w in words:
        if sum(len(x) + 1 for x in cur) + len(w) > max_len and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines[:3]

def _reel_as_carousel(post, plan):
    """
    Fallback: convert reel script into a vertical 9:16 carousel (1080Ã—1920).
    Matches reel aesthetic better than landscape slides.
    """
    print("  Building 9:16 carousel from reel script as fallback...")
    script = post.get("script", [post.get("hook", post["topic"])])
    n      = len(script)
    slides = []

    slides.append({
        "badge": None, "num": None, "is_cover": True,
        "title": _wrap_title(post.get("hook", post["topic"])),
        "body":  ["Lies weiter. â†’"],
    })
    for i, line in enumerate(script):
        slides.append({
            "badge": None,
            "num":   f"{i+1} / {n}",
            "title": _wrap_title(line),
            "body":  [],
        })
    slides.append({
        "badge": "FOLGE UNS", "num": None,
        "title": ["TÃ¤gliches Mindset", "& Money Moves"],
        "body":  ["Folge @mentviro", "fÃ¼r tÃ¤glich mehr."],
    })

    pq = post.get("pexels_video_query", "dark city cinematic night")
    tmp_paths = []
    try:
        for i, slide in enumerate(slides):
            print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
            bg_img = None
            if not slide.get("is_cover"):
                bg_img = pexels_portrait(pq, target_w=SW, target_h=SH)
            # Build in 9:16 format
            img_bytes = build_carousel_slide(slide, bg_img, w=SW, h=SH)
            path = f"{TMPDIR}/mentviro_reel_fb_d{post['day']}_s{i+1}.jpg"
            with open(path, "wb") as f:
                f.write(img_bytes)
            tmp_paths.append(path)
            print("ok")
            time.sleep(0.5)

        print("  Uploading 9:16 carousel to Instagram...")
        cl    = get_ig_client()
        media = cl.album_upload(tmp_paths, caption=post["caption"])
        print(f"  Reel-Carousel live! ID: {media.pk}")
        return str(media.pk)
    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass

def run_reel(post, plan):
    import subprocess

    print(f"Building reel: {post['topic']}")

    script_text = " ".join(post.get("script", [post.get("hook", "")]))

    print("  Generating voiceover (ElevenLabs)...")
    try:
        el_key = os.environ.get(
            "ELEVENLABS_API_KEY",
            "1071b6e53cb6e950c63d8e11a05dfa7b07764275cab9fda0ce63104a421c2d37",
        )
        el_r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
            headers={"xi-api-key": el_key, "Content-Type": "application/json"},
            json={"text": script_text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            timeout=60,
        )
        if el_r.status_code == 200 and len(el_r.content) > 1000:
            print("  Audio generated")
        else:
            print(f"  âš  ElevenLabs {el_r.status_code}: {el_r.text[:200]}")
    except Exception as e:
        print(f"  âš  ElevenLabs error: {e}")

    print("  Searching Pexels video...")
    video_url = pexels_video(post.get("pexels_video_query", "cinematic dark city night"))
    if not video_url:
        print("  âš  No Pexels video found â€” falling back to 9:16 carousel")
        return _reel_as_carousel(post, plan)

    print("  Downloading video...")
    raw_path   = f"{TMPDIR}/mentviro_reel_d{post['day']}_raw.mp4"
    conv_path  = f"{TMPDIR}/mentviro_reel_d{post['day']}.mp4"
    thumb_path = conv_path + ".jpg"

    r = requests.get(video_url, timeout=120, stream=True)
    with open(raw_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)
    size_mb = os.path.getsize(raw_path) / 1024 / 1024
    print(f"  Raw video: {size_mb:.1f} MB")

    try:
        probe    = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", raw_path],
            capture_output=True, text=True, timeout=30,
        )
        duration = float((probe.stdout.strip().split("\n")[0]) or "0")
        print(f"  Duration: {duration:.1f}s")
        loop_args = []
        if duration < 5:
            loops     = max(1, int(20 / max(duration, 0.1)))
            loop_args = ["-stream_loop", str(loops)]
            print(f"  Short clip â€” looping Ã—{loops}")
        subprocess.run(
            ["ffmpeg", "-y"] + loop_args + [
                "-i", raw_path,
                "-vf", ("scale=1080:1920:force_original_aspect_ratio=decrease,"
                         "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1"),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-t", "30",
                conv_path,
            ],
            check=True, capture_output=True, timeout=240,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", conv_path,
             "-ss", "0", "-vframes", "1", "-q:v", "2", thumb_path],
            check=True, capture_output=True, timeout=30,
        )
        print(f"  Re-encoded: {os.path.getsize(conv_path)/1024/1024:.1f} MB, thumbnail OK")
        final_video = conv_path
    except Exception as e:
        print(f"  âš  ffmpeg failed: {e} â€” using raw video")
        final_video = raw_path
        thumb_path  = None

    try:
        print("  Uploading reel to Instagram...")
        cl    = get_ig_client()
        media = cl.clip_upload(
            final_video,
            caption=post["caption"],
            thumbnail=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
        )
        print(f"  Reel live! ID: {media.pk}")
        return str(media.pk)
    except Exception as e:
        print(f"  âš  clip_upload failed ({type(e).__name__}: {e})")
        print("  â†’ Falling back to 9:16 carousel")
        return _reel_as_carousel(post, plan)
    finally:
        for p in [raw_path, conv_path, thumb_path]:
            try:
                if p and os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

# â”€â”€â”€ STORY WORKFLOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_story(post, plan):
    print("Building story...")
    story_bytes = build_story(post)
    story_path  = f"{TMPDIR}/mentviro_story_d{post['day']}.jpg"

    with open(story_path, "wb") as f:
        f.write(story_bytes)

    try:
        print("  Uploading story to Instagram...")
        cl = get_ig_client()

        # Story poll sticker
        stickers = []
        poll_q   = post.get("story_poll", "")
        if poll_q:
            try:
                from instagrapi.types import StoryPoll
                poll = StoryPoll(
                    x=0.5, y=0.72, width=0.9, height=0.14,
                    question=poll_q,
                    tallies=[{"text": "Ja âœ…"}, {"text": "Nein âŒ"}],
                )
                stickers = [poll]
                print(f"  Adding poll: '{poll_q}'")
            except Exception as e:
                print(f"  âš  Poll sticker skipped: {e}")

        if stickers:
            media = cl.photo_upload_to_story(story_path, stickers=stickers)
        else:
            media = cl.photo_upload_to_story(story_path)

        print(f"  Story live! ID: {media.pk}")
        return str(media.pk)
    finally:
        try:
            os.unlink(story_path)
        except Exception:
            pass

# â”€â”€â”€ HTML DASHBOARD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_dashboard(plan):
    """
    Generate docs/index.html â€” a simple overview of upcoming + recent posts.
    Committed to repo; visible via GitHub Pages if enabled.
    """
    today      = date.today().isoformat()
    upcoming   = [p for p in plan["posts"] if p["status"] == "pending"][:7]
    recent     = sorted(
        [p for p in plan["posts"] if p["status"] == "published"],
        key=lambda p: p.get("date", ""), reverse=True
    )[:10]

    def badge(t):
        return (f'<span style="background:#1a73e8;color:#fff;padding:2px 8px;'
                f'border-radius:4px;font-size:12px">{t.upper()}</span>')

    def ins_html(p):
        ins = p.get("insights", {})
        if not ins:
            return ""
        return (f'<span style="color:#888;font-size:13px"> &nbsp;'
                f'â¤ {ins.get("likes",0)}  ðŸ’¬ {ins.get("comments",0)}</span>')

    rows_upcoming = ""
    for p in upcoming:
        rows_upcoming += (
            f'<tr><td>{p["date"]}</td><td>Day {p["day"]}</td>'
            f'<td>{badge(p["type"])}</td>'
            f'<td style="max-width:400px">{p["topic"]}</td></tr>\n'
        )

    rows_recent = ""
    for p in recent:
        rows_recent += (
            f'<tr><td>{p["date"]}</td><td>Day {p["day"]}</td>'
            f'<td>{badge(p["type"])}</td>'
            f'<td style="max-width:400px">{p["topic"]}{ins_html(p)}</td></tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>mentviro Content Dashboard</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0d0d0d; color: #e0e0e0;
           margin: 0; padding: 24px; }}
    h1   {{ color: #fff; margin-bottom: 4px; }}
    .sub {{ color: #888; margin-bottom: 32px; font-size: 14px; }}
    h2   {{ color: #c0c0c0; border-bottom: 1px solid #333; padding-bottom: 6px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 40px; }}
    th    {{ text-align: left; color: #888; font-weight: 600; font-size: 13px;
             padding: 8px 12px; border-bottom: 1px solid #333; }}
    td    {{ padding: 10px 12px; border-bottom: 1px solid #222; font-size: 14px; }}
    tr:hover td {{ background: #1a1a1a; }}
  </style>
</head>
<body>
  <h1>mentviro Content Dashboard</h1>
  <p class="sub">Generiert am {today} &nbsp;Â·&nbsp; {len(upcoming)} ausstehend &nbsp;Â·&nbsp; {len(recent)} kÃ¼rzlich verÃ¶ffentlicht</p>

  <h2>ðŸ“… Kommende Posts</h2>
  <table>
    <tr><th>Datum</th><th>Tag</th><th>Typ</th><th>Thema</th></tr>
    {rows_upcoming if rows_upcoming else '<tr><td colspan="4" style="color:#666">Keine ausstehenden Posts</td></tr>'}
  </table>

  <h2>âœ… Zuletzt verÃ¶ffentlicht</h2>
  <table>
    <tr><th>Datum</th><th>Tag</th><th>Typ</th><th>Thema + Performance</th></tr>
    {rows_recent if rows_recent else '<tr><td colspan="4" style="color:#666">Noch keine verÃ¶ffentlichten Posts</td></tr>'}
  </table>
</body>
</html>"""

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_path = os.path.join(docs_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Dashboard written â†’ docs/index.html ({len(upcoming)} upcoming, {len(recent)} recent)")

# â”€â”€â”€ OPTIMAL POSTING TIME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def update_posting_time_stats(plan):
    """
    Track which hour posts are published and their engagement score.
    Writes a recommendation to plan['settings']['posting_stats'].
    If the recommended hour differs from the current schedule, prints a hint.
    """
    hour_scores: dict = {}
    for p in plan["posts"]:
        if p.get("status") != "published" or not p.get("insights"):
            continue
        published_at = p.get("published_at", "")
        if not published_at:
            continue
        try:
            hour  = int(published_at[11:13])
            ins   = p["insights"]
            score = ins.get("likes", 0) * 2 + ins.get("comments", 0) * 5
            if hour not in hour_scores:
                hour_scores[hour] = []
            hour_scores[hour].append(score)
        except Exception:
            pass

    if not hour_scores:
        return

    avg_by_hour = {h: sum(v)/len(v) for h, v in hour_scores.items()}
    best_hour   = max(avg_by_hour, key=avg_by_hour.get)

    settings = plan.setdefault("settings", {})
    settings["posting_stats"] = {
        "avg_score_by_hour": avg_by_hour,
        "recommended_hour_utc": best_hour,
    }
    save_plan(plan)

    current_cron_hour = 16  # 0 16 * * * â†’ 18:00 CET
    if best_hour != current_cron_hour and len(hour_scores) >= 5:
        print(f"  ðŸ“Š Posting-time tip: best avg engagement at {best_hour}:00 UTC "
              f"(currently {current_cron_hour}:00 UTC). "
              f"Consider updating cron to '0 {best_hour} * * *'.")

# â”€â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print(f"\n{'='*55}")
    print(f"  mentviro Auto-Post --- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    plan = load_plan()
    init_colors(plan)

    # 1. Session age check
    print("Checking IG session age...")
    check_session_age()

    # 5. Fetch engagement insights for recent posts
    print("\nFetching engagement insights for recent posts...")
    try:
        fetch_and_store_insights(plan)
        plan = load_plan()
    except Exception as e:
        print(f"  âš  Insights fetch failed: {e}")

    # 7. Update posting-time statistics
    update_posting_time_stats(plan)

    # Auto-generate new content if running low
    check_and_refill_content(plan)
    plan = load_plan()

    post = get_todays_post(plan)
    if not post:
        print("No pending post for today. All done!")
        generate_dashboard(plan)
        return

    print(f"\nDay {post['day']} --- {post['date']} --- {post['type'].upper()}")
    print(f"Topic: {post['topic']}\n")

    try:
        if post["type"] == "carousel":
            media_id = run_carousel(post, plan)
        elif post["type"] == "reel":
            media_id = run_reel(post, plan)
        else:
            raise ValueError(f"Unknown post type: {post['type']}")

        story_id = run_story(post, plan)

        post["status"]       = "published"
        post["post_id"]      = media_id
        post["story_id"]     = story_id
        post["published_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        save_plan(plan)

        # 9. Regenerate dashboard
        plan = load_plan()
        generate_dashboard(plan)

        summary = (
            f"âœ… <b>mentviro</b> Day {post['day']} gepostet!\n"
            f"ðŸ“Œ {post['type'].upper()}: {post['topic']}\n"
            f"ðŸ†” Post: <code>{media_id}</code> | Story: <code>{story_id}</code>"
        )
        send_telegram(summary)

        print(f"\n{'='*55}")
        print(f"  Done! Post: {media_id} | Story: {story_id}")
        print(f"{'='*55}\n")

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"\nERROR: {e}\n{tb}")
        send_telegram(
            f"âŒ <b>mentviro-bot FEHLER</b> (Day {post.get('day','?')})\n"
            f"<code>{type(e).__name__}: {str(e)[:300]}</code>"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()


