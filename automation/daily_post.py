#!/usr/bin/env python3
"""
mentviro Daily Instagram Automation
Runs daily via GitHub Actions cron at 18:00 CET
"""

import os, sys, json, io, time, random, requests
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from composio_openai import ComposioToolSet, Action

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PLAN_FILE  = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_FILE  = os.path.join(os.path.dirname(__file__), "assets", "mentviro_logo.png")
LOGO_URL   = os.getenv("MENTVIRO_LOGO_URL", "")

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

    # 2. Try URL from env var
    if LOGO_URL:
        try:
            r = requests.get(LOGO_URL, timeout=10)
            logo = Image.open(io.BytesIO(r.content)).convert("RGBA")
            logo.thumbnail((size, size), Image.LANCZOS)
            _logo_cache = (size, logo)
            return logo
        except Exception:
            pass

    # 3. PIL-drawn fallback
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
