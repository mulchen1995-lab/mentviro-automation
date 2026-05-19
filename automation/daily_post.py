#!/usr/bin/env python3
"""
mentviro Daily Instagram Automation
Runs daily via GitHub Actions cron at 18:00 CET
Posts carousels, reels and stories to @mentviro via instagrapi.
"""

import os, sys, json, io, time, random, requests, base64, tempfile
from datetime import date, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PLAN_FILE  = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_FILE  = os.path.join(os.path.dirname(__file__), "assets", "mentviro_logo.png")
LOGO_URL   = os.getenv("MENTVIRO_LOGO_URL", "")

# Logo is loaded from LOGO_FILE path or LOGO_URL env var; symbol drawn as fallback
_LOGO_B64 = ""

W, H   = 1080, 1350
SW, SH = 1080, 1920

# ─── LOAD PLAN ───────────────────────────────────────────────────────────────

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

def check_and_refill_content(plan):
    pending = [p for p in plan["posts"] if p["status"] == "pending"]
    if len(pending) >= 2:
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠ GEMINI_API_KEY not set — skipping auto-generation")
        return

    print(f"📝 Only {len(pending)} pending post(s) left — auto-generating 3 more via Gemini...")

    existing_topics = [p["topic"] for p in plan["posts"]]
    last_day = max(p["day"] for p in plan["posts"])
    from datetime import timedelta
    last_date = max(date.fromisoformat(p["date"]) for p in plan["posts"])
    last_type = plan["posts"][-1]["type"] if plan["posts"] else "reel"

    start_date = last_date + timedelta(days=1)
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(3)]
    types = []
    t = last_type
    for _ in range(3):
        t = "reel" if t == "carousel" else "carousel"
        types.append(t)

    prompt = f"""Du bist viraler Content Creator für @mentviro (Business Mindset, Instagram, Deutsch).

Erstelle GENAU 3 neue Posts als JSON-Array. Nicht mehr, nicht weniger.

BEREITS BEHANDELTE THEMEN (NICHT wiederholen):
{chr(10).join(f'- {t}' for t in existing_topics)}

VIRALER CONTENT — PFLICHT:
Orientiere dich an aktuellen Viral-Formaten auf Instagram/TikTok:
- Hooks wie: "Niemand redet darüber", "Das sagt dir kein Banker", "Ich wünschte, ich hätte das mit 20 gewusst", "Hör sofort damit auf", "Das ist die bittere Wahrheit über..."
- Kontroverse oder überraschende Aussagen die zum Kommentieren anregen
- Zahlen-Listicles: "5 Dinge die...", "3 Fehler warum..."
- Curiosity-Gap: Leser muss wissen wie es weitergeht
- Maximale Relevanz für Menschen 20–40 die Vermögen aufbauen wollen

VORGABEN:
- Types (in dieser Reihenfolge): {types}
- Tage: {last_day+1} bis {last_day+3}
- Daten: {dates[0]} bis {dates[2]}
- Sprache: Deutsch, Themen: Mindset, Finanzen, Investieren, Entrepreneurship, Erfolg
- PEXELS QUERIES: cinematic, dunkel, ästhetisch. NIEMALS: businessman, office, suit, handshake
  Gute Beispiele: "dark foggy forest path moody", "aerial city night lights cinematic", "chess king macro shadow dramatic", "dark ocean waves drone aerial", "dark marble texture minimal", "lone silhouette fog dark dramatic"
- Slide title[]: max 3 kurze Zeilen, body[]: max 2 Zeilen
- Caption: emotional, provokant, mit 15 deutschen/englischen Hashtags

Gib NUR das JSON-Array aus, kein Text davor/danach.

Carousel-Schema:
{{"day":N,"date":"YYYY-MM-DD","type":"carousel","topic":"...","status":"pending","hook":"...",
"slides":[
  {{"badge":null,"num":null,"title":["..."],"body":["..."],"is_cover":true}},
  {{"badge":"PUNKT #1","num":"1 / N","title":["..."],"body":["..."]}},
  ...,
  {{"badge":"FOLGE UNS","num":null,"title":["Mehr Mindset","& Money Moves"],"body":["Folge @mentviro","für täglich mehr."]}}
],
"caption":"...","pexels_queries":["q1","q2","q3","q4","q5","q6"],
"story_text":["NEU AUF MENTVIRO","Zeile 1","Zeile 2","→ Sieh dir den Post an"]}}

Reel-Schema:
{{"day":N,"date":"YYYY-MM-DD","type":"reel","topic":"...","status":"pending","hook":"...",
"script":["Satz 1","Satz 2","Satz 3","Satz 4","Satz 5","Folge @mentviro."],
"caption":"...","pexels_video_query":"dark cinematic query",
"story_text":["NEUES REEL","Zeile 1","Zeile 2","→ Schau jetzt"]}}"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"content-type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 8000, "temperature": 0.9}},
            timeout=120,
        )
        if r.status_code != 200:
            print(f"⚠ Gemini API error {r.status_code}: {r.text[:300]}")
            return
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            print("⚠ No JSON array in Gemini response")
            return
        new_posts = json.loads(text[start:end])
        plan["posts"].extend(new_posts)
        save_plan(plan)
        print(f"✅ Auto-generated {len(new_posts)} new posts (Day {last_day+1}–{last_day+len(new_posts)})")
    except Exception as e:
        print(f"⚠ Auto-generation failed: {e}")

# ─── FONT HELPERS ────────────────────────────────────────────────────────────

def fnt(size, bold=False):
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/local/share/fonts/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# ─── LOGO WATERMARK ──────────────────────────────────────────────────────────

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

    sym = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(sym)
    s, col = size, (192, 192, 192, 140)
    lw = max(2, s // 22)
    for off in range(lw):
        d.ellipse([s*.04+off, s*.40+off, s*.96-off, s*.62-off], outline=col)
    pts = [(s*.18,s*.80),(s*.18,s*.20),(s*.50,s*.55),(s*.82,s*.20),(s*.82,s*.80)]
    d.line([(int(x),int(y)) for x,y in pts], fill=col, width=lw+1)
    ax2, ay2 = int(s*.90), int(s*.02)
    d.line([(int(s*.68),int(s*.22)),(ax2,ay2)], fill=col, width=lw)
    d.polygon([(ax2,ay2),(ax2-int(s*.12),ay2+int(s*.05)),(ax2-int(s*.04),ay2+int(s*.13))], fill=col)
    _logo_cache = (size, sym)
    return sym

def paste_logo(img_rgba, x, y, size=90):
    logo = get_logo_asset(size)
    img_rgba.alpha_composite(logo, (x - size // 2, y - size // 2))

# ─── DESIGN HELPERS ──────────────────────────────────────────────────────────

COLORS = None

def init_colors(plan):
    global COLORS
    c = plan["settings"]["colors"]
    COLORS = {
        "bg":    tuple(c["background"]),
        "white": tuple(c["white"]),
        "silver": tuple(c["silver"]),
        "light": tuple(c["light_silver"]),
        "dark":  tuple(c["dark_silver"]),
    }

def draw_base_frame(img_rgba, is_bw=False, slide_num=None, badge=None):
    d = ImageDraw.Draw(img_rgba)
    ACC  = COLORS["white"] if is_bw else COLORS["silver"]
    BODY = (180, 180, 180) if is_bw else COLORS["dark"]

    d.rectangle([(0, 0), (W, 5)], fill=ACC)
    d.rectangle([(0, H-5), (W, H)], fill=ACC)

    d.text((60, 28), "MENTVIRO", font=fnt(28, True), fill=ACC)
    d.text((60, 62), "BUSINESS MINDSET", font=fnt(17), fill=BODY)
    d.rectangle([(60, 96), (W-60, 98)], fill=(70, 70, 70))

    if badge:
        d.text((60, 120), badge, font=fnt(30, True), fill=ACC)

    if slide_num:
        bb = fnt(26).getbbox(slide_num)
        d.text((W - 60 - (bb[2]-bb[0]), 124), slide_num, font=fnt(26), fill=BODY)

    d.rectangle([(60, H-120), (W-60, H-116)], fill=(60, 60, 60))
    d.text((60, H-100), "@mentviro", font=fnt(30, True), fill=COLORS["white"])
    paste_logo(img_rgba, W - 80, H - 78, size=80)

def dark_overlay(base_rgb, strength=195):
    ov = Image.new("RGBA", (W, H))
    od = ImageDraw.Draw(ov)
    for y in range(H):
        a = int(strength - 30 + (y / H) * 30)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(base_rgb.convert("RGBA"), ov)

# ─── PEXELS HELPERS ──────────────────────────────────────────────────────────

def pexels_portrait(query, target_w=W, target_h=H):
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        print(f"  ⚠ PEXELS_API_KEY not set")
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "orientation": "portrait", "per_page": 5, "size": "large"},
            timeout=30,
        )
        if r.status_code != 200:
            print(f"  ⚠ Pexels API {r.status_code}: {r.text[:200]}")
            return None
        photos = r.json().get("photos", [])
        if not photos:
            print(f"  ⚠ No Pexels photos for: {query}")
            return None
        photo = random.choice(photos[:min(3, len(photos))])
        url = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
        resp = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        src_w, src_h = img.size
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h
        if src_ratio > target_ratio:
            new_w = int(src_h * target_ratio)
            offset = (src_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, src_h))
        elif src_ratio < target_ratio:
            new_h = int(src_w / target_ratio)
            img = img.crop((0, 0, src_w, new_h))
        return img.resize((target_w, target_h), Image.LANCZOS)
    except Exception as e:
        print(f"  ⚠ Pexels portrait error: {e}")
        return None

def pexels_video(query):
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        print("  ⚠ PEXELS_API_KEY not set")
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
        print(f"  ⚠ Pexels video error: {e}")
    return None

# ─── CAROUSEL BUILDER ────────────────────────────────────────────────────────

def build_carousel_slide(slide, bg_img=None):
    is_cover = slide.get("is_cover", False)
    is_bw    = is_cover

    if bg_img is not None:
        bg = bg_img.convert("L").convert("RGB") if is_bw else bg_img
        img = dark_overlay(bg, 198)
    elif is_cover:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    else:
        img = Image.new("RGBA", (W, H), tuple(COLORS["bg"]) + (255,))

    draw_base_frame(img, is_bw=is_bw, slide_num=slide.get("num"), badge=slide.get("badge"))
    d = ImageDraw.Draw(img)
    BODY = (175, 175, 175)

    content_top = 165 + (30 if slide.get("badge") else 0)

    if is_cover:
        paste_logo(img, W // 2, 310, size=200)
        content_top = 560

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

# ─── STORY BUILDER ───────────────────────────────────────────────────────────

def build_story(post):
    query = (post.get("pexels_queries") or ["dark cityscape night cinematic"])[0]
    bg = pexels_portrait(query, target_w=SW, target_h=SH)
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

    texts = post.get("story_text", ["NEU", post.get("topic", ""), "→ Sieh dir den Post an"])
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

# ─── INSTAGRAM CLIENT ────────────────────────────────────────────────────────

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

    cl = Client()
    cl.delay_range = [1, 3]

    # Try session-based login first (avoids challenge on repeated runs)
    session_json = os.environ.get("IG_SESSION", "")
    if session_json:
        try:
            import json as _json
            settings = _json.loads(session_json)
            cl.load_settings(settings)
            cl.login(username, password)
            print("  Instagram: session login OK")
            _ig_client = cl
            return cl
        except Exception as e:
            print(f"  Session login failed ({e}), trying password login...")
            cl = Client()
            cl.delay_range = [1, 3]

    cl.login(username, password)
    print("  Instagram: password login OK")
    _ig_client = cl
    return cl

# ─── CAROUSEL WORKFLOW ───────────────────────────────────────────────────────

def run_carousel(post, plan):
    print(f"Building carousel: {post['topic']}")
    slides = post["slides"]
    pexels_queries = post.get("pexels_queries", [])

    tmp_paths = []
    try:
        for i, slide in enumerate(slides):
            print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
            bg_img = None
            if not slide.get("is_cover") and pexels_queries:
                query = pexels_queries[min(i, len(pexels_queries)-1)]
                bg_img = pexels_portrait(query)
            img_bytes = build_carousel_slide(slide, bg_img)
            path = f"/tmp/mentviro_d{post['day']}_s{i+1}.jpg"
            with open(path, "wb") as f:
                f.write(img_bytes)
            tmp_paths.append(path)
            print("ok")
            time.sleep(0.5)

        print("Uploading carousel to Instagram...")
        cl = get_ig_client()
        media = cl.album_upload(tmp_paths, caption=post["caption"])
        print(f"  Carousel live! ID: {media.pk}")
        return str(media.pk)

    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass

# ─── REEL WORKFLOW ───────────────────────────────────────────────────────────

def run_reel(post, plan):
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
            print("  Audio generated (not mixed into video)")
        else:
            print(f"  ⚠ ElevenLabs {el_r.status_code}: {el_r.text[:200]}")
    except Exception as e:
        print(f"  ⚠ ElevenLabs error: {e}")

    print("  Searching Pexels video...")
    video_url = pexels_video(post.get("pexels_video_query", "cinematic dark city night"))
    if not video_url:
        raise RuntimeError("No Pexels video found for reel")

    print(f"  Downloading video...")
    video_path = f"/tmp/mentviro_reel_d{post['day']}.mp4"
    r = requests.get(video_url, timeout=120, stream=True)
    with open(video_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)
    size_mb = os.path.getsize(video_path) / 1024 / 1024
    print(f"  Video: {size_mb:.1f} MB")

    try:
        print("  Uploading reel to Instagram...")
        cl = get_ig_client()
        media = cl.clip_upload(video_path, caption=post["caption"])
        print(f"  Reel live! ID: {media.pk}")
        return str(media.pk)
    finally:
        try:
            os.unlink(video_path)
        except Exception:
            pass

# ─── STORY WORKFLOW ──────────────────────────────────────────────────────────

def run_story(post, plan):
    print("Building story...")
    story_bytes = build_story(post)

    story_path = f"/tmp/mentviro_story_d{post['day']}.jpg"
    with open(story_path, "wb") as f:
        f.write(story_bytes)

    try:
        print("  Uploading story to Instagram...")
        cl = get_ig_client()
        media = cl.photo_upload_to_story(story_path)
        print(f"  Story live! ID: {media.pk}")
        return str(media.pk)
    finally:
        try:
            os.unlink(story_path)
        except Exception:
            pass

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  mentviro Auto-Post --- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    plan = load_plan()
    init_colors(plan)

    check_and_refill_content(plan)
    plan = load_plan()

    post = get_todays_post(plan)
    if not post:
        print("No pending post for today. All done!")
        return

    print(f"Day {post['day']} --- {post['date']} --- {post['type'].upper()}")
    print(f"Topic: {post['topic']}\n")

    try:
        if post["type"] == "carousel":
            media_id = run_carousel(post, plan)
        elif post["type"] == "reel":
            media_id = run_reel(post, plan)
        else:
            raise ValueError(f"Unknown post type: {post['type']}")

        story_id = run_story(post, plan)

        post["status"]   = "published"
        post["post_id"]  = media_id
        post["story_id"] = story_id
        save_plan(plan)

        print(f"\n{'='*55}")
        print(f"  Done! Post: {media_id} | Story: {story_id}")
        print(f"{'='*55}\n")

    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
