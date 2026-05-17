#!/usr/bin/env python3
"""
mentviro Daily Instagram Automation
Runs daily via GitHub Actions cron at 18:00 CET
"""

import os, sys, json, io, time, random, requests, base64
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from composio_openai import ComposioToolSet, Action

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PLAN_FILE  = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_FILE  = os.path.join(os.path.dirname(__file__), "assets", "mentviro_logo.png")
LOGO_URL   = os.getenv("MENTVIRO_LOGO_URL", "")

# Embedded MENTVIRO logo — transparent PNG (151×220 px), black bg removed
_LOGO_B64 = (
    "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"
)

W, H   = 1080, 1350   # carousel portrait
SW, SH = 1080, 1920   # story

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
    """Auto-generate 3 new posts via Claude API when < 2 pending remain."""
    pending = [p for p in plan["posts"] if p["status"] == "pending"]
    if len(pending) >= 2:
        return

    api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ CLAUDE_API_KEY not set — skipping auto-generation")
        return

    print(f"📝 Only {len(pending)} pending post(s) left — auto-generating 3 more via Claude...")

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
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 8000, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        if r.status_code != 200:
            print(f"⚠ Claude API error {r.status_code}: {r.text[:300]}")
            return
        text = r.json()["content"][0]["text"].strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            print("⚠ No JSON array in Claude response")
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

    # 1. Try local file (committed to repo)
    if os.path.exists(LOGO_FILE):
        try:
            logo = Image.open(LOGO_FILE).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    # 2. Embedded logo (always works, no network needed)
    try:
        logo = Image.open(io.BytesIO(base64.b64decode(_LOGO_B64))).convert("RGBA")
        logo.thumbnail((size, size), Image.LANCZOS)
        _logo_cache = (size, logo)
        return logo
    except Exception:
        pass

    # 3. Try URL from env var
    if LOGO_URL:
        try:
            r = requests.get(LOGO_URL, timeout=10)
            logo = Image.open(io.BytesIO(r.content)).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    # 4. PIL-drawn fallback
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

# ─── COMPOSIO WRAPPER ────────────────────────────────────────────────────────

_toolset = None

def get_toolset():
    global _toolset
    if _toolset is None:
        api_key = os.environ.get("COMPOSIO_API_KEY")
        if not api_key:
            raise RuntimeError("COMPOSIO_API_KEY env var not set")
        _toolset = ComposioToolSet(api_key=api_key)
    return _toolset

def run_composio_tool_safe(slug, params, account=None):
    try:
        ts = get_toolset()
        kwargs = {"action": slug, "params": params}
        if account:
            kwargs["connected_account_id"] = account
        result = ts.execute_action(**kwargs)
        if result.get("successfull") is False or result.get("error"):
            return None, result.get("error", "unknown error")
        return result, None
    except Exception as e:
        return None, str(e)

# ─── PEXELS HELPER ───────────────────────────────────────────────────────────

def pexels_portrait(query, account, target_w=W, target_h=H):
    """Fetch a cinematic Pexels image via Composio, resize to target dimensions."""
    result, err = run_composio_tool_safe(
        "PEXELS_SEARCH_PHOTOS",
        {"query": query, "orientation": "portrait", "per_page": 5, "size": "large"},
        account=account,
    )
    if err or not result:
        print(f"  ⚠ Pexels failed ({err})")
        return None
    photos = (result.get("data") or result).get("photos", [])
    if not photos:
        return None
    # Pick randomly from top results for visual variety
    photo = random.choice(photos[:min(3, len(photos))])
    url = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
    try:
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
        print(f"  ⚠ Image download failed ({e})")
        return None

# ─── CAROUSEL BUILDER ────────────────────────────────────────────────────────

def build_carousel_slide(slide, bg_img=None):
    """Render one carousel slide → JPEG bytes. bg_img is an RGB PIL Image or None."""
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
    ACC  = COLORS["white"] if is_bw else COLORS["silver"]
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

def build_story(post, pexels_account):
    """Render story slide (1080x1920)."""
    query = (post.get("pexels_queries") or ["dark cityscape night cinematic"])[0]
    bg = pexels_portrait(query, pexels_account, target_w=SW, target_h=SH)
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

# ─── UPLOAD HELPER ───────────────────────────────────────────────────────────

def upload_image(img_bytes, filename):
    """Upload to tmpfiles.org and return clean public URL."""
    for attempt in range(3):
        try:
            r = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": (filename, io.BytesIO(img_bytes), "image/jpeg")},
                timeout=60,
            )
            if r.status_code == 200:
                url = r.json().get("data", {}).get("url", "")
                if "tmpfiles.org/" in url and "/dl/" not in url:
                    url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return url
        except Exception as e:
            print(f"  Upload attempt {attempt+1} failed: {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to upload {filename}")

# ─── CAROUSEL WORKFLOW ───────────────────────────────────────────────────────

def run_carousel(post, plan):
    cfg = plan["account"]
    print(f"Building carousel: {post['topic']}")
    slides = post["slides"]
    pexels_queries = post.get("pexels_queries", [])

    slide_urls = []
    for i, slide in enumerate(slides):
        print(f"  Slide {i+1}/{len(slides)}...", end=" ", flush=True)
        bg_img = None
        if not slide.get("is_cover") and pexels_queries:
            query = pexels_queries[min(i, len(pexels_queries)-1)]
            bg_img = pexels_portrait(query, cfg["pexels_account"])
        img_bytes = build_carousel_slide(slide, bg_img)
        url = upload_image(img_bytes, f"mentviro_d{post['day']}_s{i+1}.jpg")
        slide_urls.append(url)
        print("ok")
        time.sleep(0.5)

    print("Creating carousel container...")
    result, err = run_composio_tool_safe(
        "INSTAGRAM_CREATE_CAROUSEL_CONTAINER",
        {"ig_user_id": cfg["ig_user_id"], "child_image_urls": slide_urls, "caption": post["caption"]},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Carousel container failed: {err}")
    creation_id = (result.get("data") or result).get("id")
    print(f"  Container: {creation_id}")

    time.sleep(5)
    print("Publishing carousel...")
    result, err = run_composio_tool_safe(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id": cfg["ig_user_id"], "creation_id": creation_id, "max_wait_seconds": 120},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Publish failed: {err}")
    media_id = (result.get("data") or result).get("id")
    print(f"  Carousel live! ID: {media_id}")
    return media_id

# ─── REEL WORKFLOW ───────────────────────────────────────────────────────────

def run_reel(post, plan):
    cfg = plan["account"]
    print(f"Building reel: {post['topic']}")

    script_text = " ".join(post.get("script", [post.get("hook", "")]))

    print("  Generating voiceover (ElevenLabs)...")
    result, err = run_composio_tool_safe(
        "ELEVENLABS_TEXT_TO_SPEECH",
        {"text": script_text, "voice_id": "pNInz6obpgDQGcFmaJgB", "model_id": "eleven_multilingual_v2"},
        account=cfg.get("elevenlabs_account"),
    )
    audio_url = None
    if not err and result:
        file_data = ((result.get("data") or {}).get("file") or {})
        audio_url = file_data.get("s3url") or file_data.get("url")
    print(f"  {'Audio ready' if audio_url else 'No audio - posting without voiceover'}")

    print("  Searching Pexels video...")
    result, err = run_composio_tool_safe(
        "PEXELS_SEARCH_VIDEOS",
        {"query": post.get("pexels_video_query", "cinematic dark city night"), "per_page": 3},
        account=cfg["pexels_account"],
    )
    video_url = None
    if not err and result:
        videos = (result.get("data") or result).get("videos", [])
        for v in videos:
            for vf in v.get("video_files", []):
                if vf.get("quality") in ("hd", "sd") and "mp4" in vf.get("file_type", ""):
                    video_url = vf["link"]
                    break
            if video_url:
                break

    if not video_url:
        raise RuntimeError("No Pexels video found for reel")

    print("  Posting reel...")
    result, err = run_composio_tool_safe(
        "INSTAGRAM_POST_IG_USER_MEDIA",
        {"ig_user_id": cfg["ig_user_id"], "video_url": video_url,
         "media_type": "REELS", "caption": post["caption"], "share_to_feed": True},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Reel container failed: {err}")
    container_id = (result.get("data") or result).get("id")
    time.sleep(10)

    result, err = run_composio_tool_safe(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id": cfg["ig_user_id"], "creation_id": container_id, "max_wait_seconds": 180},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Reel publish failed: {err}")
    media_id = (result.get("data") or result).get("id")
    print(f"  Reel live! ID: {media_id}")
    return media_id

# ─── STORY WORKFLOW ──────────────────────────────────────────────────────────

def run_story(post, plan):
    cfg = plan["account"]
    print("Building story...")
    story_bytes = build_story(post, cfg["pexels_account"])
    story_url = upload_image(story_bytes, f"mentviro_story_d{post['day']}.jpg")
    print(f"  Story uploaded")

    result, err = run_composio_tool_safe(
        "INSTAGRAM_POST_IG_USER_MEDIA",
        {"ig_user_id": cfg["ig_user_id"], "image_url": story_url, "media_type": "STORIES"},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Story container failed: {err}")
    container_id = (result.get("data") or result).get("id")
    time.sleep(3)

    result, err = run_composio_tool_safe(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id": cfg["ig_user_id"], "creation_id": container_id, "max_wait_seconds": 60},
        account=cfg["composio_account"],
    )
    if err:
        raise RuntimeError(f"Story publish failed: {err}")
    story_id = (result.get("data") or result).get("id")
    print(f"  Story live! ID: {story_id}")
    return story_id

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  mentviro Auto-Post --- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    plan = load_plan()
    init_colors(plan)

    check_and_refill_content(plan)
    plan = load_plan()  # reload after potential auto-generation

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
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
