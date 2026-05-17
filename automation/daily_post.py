#!/usr/bin/env python3
"""mentviro Daily Instagram Automation — runs via GitHub Actions cron at 18:00 CET"""

import os, sys, json, io, time, requests
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from composio_openai import ComposioToolSet

PLAN_FILE = os.path.join(os.path.dirname(__file__), "content_plan.json")
LOGO_URL  = os.getenv("MENTVIRO_LOGO_URL", "")
W, H      = 1080, 1350
SW, SH    = 1080, 1920
COLORS    = {}

# ── PLAN ─────────────────────────────────────────────────────────────────────

def load_plan():
    with open(PLAN_FILE) as f: return json.load(f)

def save_plan(plan):
    with open(PLAN_FILE, "w") as f: json.dump(plan, f, indent=2, ensure_ascii=False)

def get_todays_post(plan):
    today = date.today().isoformat()
    for p in plan["posts"]:
        if p["date"] == today and p["status"] == "pending": return p
    for p in plan["posts"]:
        if p["status"] == "pending": return p
    return None

def init_colors(plan):
    global COLORS
    c = plan["settings"]["colors"]
    COLORS = {k: tuple(v) for k, v in c.items()}
    COLORS["bg"] = COLORS.pop("background")
    COLORS["light"] = COLORS.pop("light_silver")
    COLORS["dark"]  = COLORS.pop("dark_silver")

# ── FONTS ────────────────────────────────────────────────────────────────────

def fnt(size, bold=False):
    for p in [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
    ]:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# ── LOGO ─────────────────────────────────────────────────────────────────────

_logo_cache = {}

def get_logo(size=90):
    if size in _logo_cache: return _logo_cache[size]
    if LOGO_URL:
        try:
            r = requests.get(LOGO_URL, timeout=10)
            img = Image.open(io.BytesIO(r.content)).convert("RGBA")
            img.thumbnail((size, size), Image.LANCZOS)
            _logo_cache[size] = img; return img
        except Exception: pass
    sym = Image.new("RGBA", (size, size), (0,0,0,0))
    d = ImageDraw.Draw(sym)
    s, col = size, (192,192,192,140)
    lw = max(2, s//22)
    for o in range(lw): d.ellipse([s*.04+o,s*.40+o,s*.96-o,s*.62-o], outline=col)
    pts = [(s*.18,s*.80),(s*.18,s*.20),(s*.50,s*.55),(s*.82,s*.20),(s*.82,s*.80)]
    d.line([(int(x),int(y)) for x,y in pts], fill=col, width=lw+1)
    ax1,ay1,ax2,ay2 = int(s*.68),int(s*.22),int(s*.90),int(s*.02)
    d.line([(ax1,ay1),(ax2,ay2)], fill=col, width=lw)
    d.polygon([(ax2,ay2),(ax2-int(s*.12),ay2+int(s*.05)),(ax2-int(s*.04),ay2+int(s*.13))], fill=col)
    _logo_cache[size] = sym; return sym

def paste_logo(img_rgba, cx, cy, size=90):
    logo = get_logo(size)
    img_rgba.alpha_composite(logo, (cx - size//2, cy - size//2))

# ── SLIDE BUILDER ────────────────────────────────────────────────────────────

def dark_overlay(base, strength=195):
    ov = Image.new("RGBA", (W,H))
    od = ImageDraw.Draw(ov)
    for y in range(H):
        od.line([(0,y),(W,y)], fill=(0,0,0,int(strength-30+(y/H)*30)))
    return Image.alpha_composite(base.convert("RGBA"), ov)

def draw_frame(img, badge=None, slide_num=None, bw=False):
    d = ImageDraw.Draw(img)
    ACC  = COLORS["white"] if bw else COLORS["silver"]
    BODY = (175,175,175)
    d.rectangle([(0,0),(W,5)], fill=ACC)
    d.rectangle([(0,H-5),(W,H)], fill=ACC)
    d.text((60,28), "MENTVIRO",       font=fnt(28,True), fill=ACC)
    d.text((60,62), "BUSINESS MINDSET", font=fnt(17),   fill=BODY)
    d.rectangle([(60,96),(W-60,98)], fill=(70,70,70))
    if badge:
        d.text((60,120), badge, font=fnt(30,True), fill=ACC)
    if slide_num:
        bb = fnt(26).getbbox(slide_num)
        d.text((W-60-(bb[2]-bb[0]),124), slide_num, font=fnt(26), fill=BODY)
    d.rectangle([(60,H-120),(W-60,H-116)], fill=(60,60,60))
    d.text((60,H-100), "@mentviro", font=fnt(30,True), fill=COLORS["white"])
    paste_logo(img, W-80, H-78, size=80)

def build_carousel_slide(slide):
    is_cover = slide.get("is_cover", False)
    bw = is_cover
    if slide.get("bg_url"):
        resp = requests.get(slide["bg_url"], timeout=30)
        bg = Image.open(io.BytesIO(resp.content)).convert("RGB").resize((W,H),Image.LANCZOS)
        if bw: bg = bg.convert("L").convert("RGB")
        img = dark_overlay(bg, 198)
    else:
        img = Image.new("RGBA",(W,H),(0,0,0,255))
    draw_frame(img, badge=slide.get("badge"), slide_num=slide.get("num"), bw=bw)
    d = ImageDraw.Draw(img)
    BODY = (175,175,175)
    top = 165 + (30 if slide.get("badge") else 0)
    if is_cover:
        paste_logo(img, W//2, 310, size=200)
        top = 560
    tsz = 68 if is_cover else 74
    y = top + 30
    for line in slide.get("title",[]):
        d.text((60,y), line, font=fnt(tsz,True), fill=COLORS["white"])
        bb = fnt(tsz,True).getbbox(line); y += (bb[3]-bb[1])+14
    y += 36
    for line in slide.get("body",[]):
        d.text((60,y), line, font=fnt(40), fill=BODY)
        bb = fnt(40).getbbox(line); y += (bb[3]-bb[1])+12
    buf = io.BytesIO()
    img.convert("RGB").save(buf,"JPEG",quality=93)
    return buf.getvalue()

def build_story(post):
    query = (post.get("pexels_queries") or ["businessman dark success"])[0]
    try:
        ph_key = os.environ.get("PEXELS_API_KEY","")
        r = requests.get("https://api.pexels.com/v1/search",
            headers={"Authorization": ph_key},
            params={"query":query,"orientation":"portrait","per_page":1}, timeout=15)
        photos = r.json().get("photos",[])
        if photos:
            bg = Image.open(io.BytesIO(requests.get(photos[0]["src"]["portrait"],timeout=30).content)).convert("RGB").resize((SW,SH),Image.LANCZOS)
        else: raise Exception()
    except Exception:
        bg = Image.new("RGB",(SW,SH),(0,0,0))
    ov = Image.new("RGBA",(SW,SH))
    od = ImageDraw.Draw(ov)
    for y in range(SH): od.line([(0,y),(SW,y)],fill=(0,0,0,int(155+(y/SH)*80)))
    story = Image.alpha_composite(bg.convert("RGBA"), ov)
    d = ImageDraw.Draw(story)
    SILVER = COLORS["silver"]
    d.rectangle([(0,0),(SW,7)], fill=SILVER)
    d.text((60,55),"@mentviro",font=fnt(40,True),fill=SILVER)
    d.rectangle([(60,108),(200,115)],fill=SILVER)
    paste_logo(story, SW//2, SH//2-260, size=190)
    texts = post.get("story_text",["NEU",post.get("topic",""),"→ Post ansehen"])
    y = SH//2-60
    for j,line in enumerate(texts):
        sz = 34 if j==0 else (80 if j<len(texts)-1 else 46)
        col = SILVER if j==0 else (COLORS["white"] if j<len(texts)-1 else SILVER)
        d.text((60,y), line, font=fnt(sz, j>0), fill=col)
        bb = fnt(sz,j>0).getbbox(line); y += (bb[3]-bb[1])+12
    d.rectangle([(0,SH-7),(SW,SH)],fill=SILVER)
    buf = io.BytesIO()
    story.convert("RGB").save(buf,"JPEG",quality=93)
    return buf.getvalue()

# ── UPLOAD ───────────────────────────────────────────────────────────────────

def upload(img_bytes, filename):
    for _ in range(3):
        try:
            r = requests.post("https://tmpfiles.org/api/v1/upload",
                files={"file":(filename,io.BytesIO(img_bytes),"image/jpeg")}, timeout=60)
            if r.status_code==200:
                url = r.json().get("data",{}).get("url","")
                if "tmpfiles.org/" in url and "/dl/" not in url:
                    url = url.replace("tmpfiles.org/","tmpfiles.org/dl/")
                return url
        except Exception: time.sleep(2)
    raise RuntimeError(f"Upload failed for {filename}")

# ── COMPOSIO ─────────────────────────────────────────────────────────────────

_ts = None
def toolset():
    global _ts
    if _ts is None:
        key = os.environ.get("COMPOSIO_API_KEY")
        if not key: raise RuntimeError("COMPOSIO_API_KEY not set")
        _ts = ComposioToolSet(api_key=key)
    return _ts

def run_tool(slug, params, account=None):
    try:
        kw = {"action": slug, "params": params}
        if account: kw["connected_account_id"] = account
        r = toolset().execute_action(**kw)
        if r.get("error"): return None, r["error"]
        return r, None
    except Exception as e: return None, str(e)

# ── WORKFLOWS ────────────────────────────────────────────────────────────────

def run_carousel(post, plan):
    cfg = plan["account"]
    print(f"  Building {len(post['slides'])} slides…")
    urls = []
    for i, slide in enumerate(post["slides"]):
        b = build_carousel_slide(slide)
        url = upload(b, f"mentviro_d{post['day']}_s{i+1}.jpg")
        urls.append(url)
        print(f"    Slide {i+1} ✅")
        time.sleep(0.5)
    r, err = run_tool("INSTAGRAM_CREATE_CAROUSEL_CONTAINER",
        {"ig_user_id":cfg["ig_user_id"],"child_image_urls":urls,"caption":post["caption"]},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    cid = (r.get("data") or r)["id"]
    r, err = run_tool("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id":cfg["ig_user_id"],"creation_id":cid,"max_wait_seconds":120},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    return (r.get("data") or r)["id"]

def run_reel(post, plan):
    cfg = plan["account"]
    script_text = " ".join(post.get("script",[post.get("hook","")]))
    print("  Generating voiceover…")
    r, err = run_tool("ELEVENLABS_TEXT_TO_SPEECH",
        {"text":script_text,"voice_id":"pNInz6obpgDQGcFmaJgB","model_id":"eleven_multilingual_v2"},
        account=cfg.get("elevenlabs_account"))
    audio_url = None
    if not err and r:
        f = ((r.get("data") or {}).get("file") or {})
        audio_url = f.get("s3url") or f.get("url")
    print("  Searching Pexels video…")
    r, err = run_tool("PEXELS_SEARCH_VIDEOS",
        {"query":post.get("pexels_video_query","cinematic success entrepreneur"),"per_page":3},
        account=cfg["pexels_account"])
    video_url = None
    if not err and r:
        videos = (r.get("data") or r).get("videos",[])
        if videos:
            for vf in videos[0].get("video_files",[]):
                if vf.get("quality") in ("hd","sd") and "mp4" in vf.get("file_type",""):
                    video_url = vf["link"]; break
    if not video_url:
        print("  ⚠ No video found"); return None
    r, err = run_tool("INSTAGRAM_POST_IG_USER_MEDIA",
        {"ig_user_id":cfg["ig_user_id"],"video_url":video_url,
         "media_type":"REELS","caption":post["caption"]},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    cid = (r.get("data") or r)["id"]
    time.sleep(5)
    r, err = run_tool("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id":cfg["ig_user_id"],"creation_id":cid,"max_wait_seconds":180},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    return (r.get("data") or r)["id"]

def run_story(post, plan):
    cfg = plan["account"]
    print("  Building story…")
    b = build_story(post)
    url = upload(b, f"mentviro_story_d{post['day']}.jpg")
    r, err = run_tool("INSTAGRAM_POST_IG_USER_MEDIA",
        {"ig_user_id":cfg["ig_user_id"],"image_url":url,"media_type":"STORIES"},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    cid = (r.get("data") or r)["id"]
    time.sleep(3)
    r, err = run_tool("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {"ig_user_id":cfg["ig_user_id"],"creation_id":cid,"max_wait_seconds":60},
        account=cfg["composio_account"])
    if err: raise RuntimeError(err)
    return (r.get("data") or r)["id"]

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*50}")
    print(f"  mentviro Auto-Post — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*50}\n")
    plan = load_plan()
    init_colors(plan)
    post = get_todays_post(plan)
    if not post:
        print("✅ No pending post today."); return
    print(f"📅 Day {post['day']} | {post['date']} | {post['type'].upper()}")
    print(f"📌 {post['topic']}\n")
    try:
        if   post["type"] == "carousel": mid = run_carousel(post, plan)
        elif post["type"] == "reel":     mid = run_reel(post, plan)
        else: raise ValueError(f"Unknown type: {post['type']}")
        sid = run_story(post, plan)
        post.update({"status":"published","post_id":mid,"story_id":sid})
        save_plan(plan)
        print(f"\n✅ Post: {mid}  Story: {sid}")
    except Exception as e:
        print(f"\n❌ {e}"); sys.exit(1)

if __name__ == "__main__":
    main()
