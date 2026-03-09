#!/usr/bin/env python3
"""
generate-school-content.py
For every UK school in Notion that is missing Thai Angle EN/TH, Hero Tagline EN/TH,
and Parent Quote EN/TH — generate them with Gemini and save back to Notion.

Usage: python3 generate-school-content.py
       python3 generate-school-content.py --school "Abbey DLD College"  # single school
       python3 generate-school-content.py --dry-run                     # preview only
"""

import urllib.request, urllib.error, json, os, sys, re, time

# ── Config ────────────────────────────────────────────────────────────────────
env_lines = open(os.path.expanduser("~/.openclaw/.env")).read().splitlines()
NOTION_KEY  = next(l.split("=",1)[1].strip() for l in env_lines if l.startswith("NOTION_API_KEY"))
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY") or next((l.split("=",1)[1].strip() for l in env_lines if l.startswith("GEMINI_API_KEY")), "AIzaSyCkKCvbALjH72FpzFjZGDZ8lsoz7dGTxMI")
DB_ID       = "30e9d89c-abdc-8002-a053-f16764e9d51d"
DRY_RUN     = "--dry-run" in sys.argv
FILTER_NAME = next((sys.argv[i+1] for i,a in enumerate(sys.argv) if a == "--school"), None)
FILTER_NAME = FILTER_NAME.lower() if FILTER_NAME else None

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def notion_request(url, body=None, method=None):
    if method is None:
        method = "POST" if body else "GET"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers=NOTION_HEADERS,
        method=method
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def txt(prop):
    if not prop: return ""
    t = prop.get("type","")
    if t == "rich_text": return "".join(b.get("plain_text","") for b in prop.get("rich_text",[]))
    if t == "title":     return "".join(b.get("plain_text","") for b in prop.get("title",[]))
    if t == "number":    v = prop.get("number"); return str(v) if v is not None else ""
    if t == "select":    s = prop.get("select"); return s["name"] if s else ""
    return ""

def rich_text_prop(value):
    """Convert a string to Notion rich_text property format."""
    chunks = []
    # Notion max per block is 2000 chars
    while len(value) > 2000:
        chunks.append(value[:2000])
        value = value[2000:]
    chunks.append(value)
    return {"rich_text": [{"text": {"content": c}} for c in chunks if c]}

def call_gemini(prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return data["candidates"][0]["content"]["parts"][0]["text"]

def extract_json(text):
    """Extract JSON from Gemini response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    # Find first { to last }
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError(f"No JSON found in: {text[:200]}")

# ── Fetch all UK schools from Notion ─────────────────────────────────────────
def fetch_schools():
    pages, cursor = [], None
    while True:
        body = {
            "filter": {"property": "Country", "select": {"equals": "United Kingdom"}},
            "page_size": 100
        }
        if cursor: body["start_cursor"] = cursor
        data = notion_request(f"https://api.notion.com/v1/databases/{DB_ID}/query", body)
        pages.extend(data["results"])
        if not data.get("has_more"): break
        cursor = data["next_cursor"]
    return pages

# ── Generate content for one school ──────────────────────────────────────────
def generate_content(school_data):
    name     = school_data["name"]
    location = school_data["location"]
    fees     = school_data["fees"]
    sports   = school_data["sports"]
    pastoral = school_data["pastoral"]
    isi      = school_data["isi"]
    alevel   = school_data["alevel"]
    gcse     = school_data["gcse"]
    alumni   = school_data["alumni"]
    char     = school_data["school_char"]
    boarding = school_data["boarding_ratio"]
    school_type = school_data["school_type"]
    entry    = school_data["entry_year"]
    total_stu = school_data["total_students"]
    scholarships = school_data["scholarships"]

    prompt = f"""You are a content writer for LINKEDU, a UK boarding school consultancy for Thai families in Thailand.

Write compelling, parent-focused content for this UK boarding school. The audience is Thai parents considering sending their child to the UK. Tone: warm, informative, confident. No fluff.

SCHOOL DATA:
- Name: {name}
- Location: {location}
- School Type: {school_type}
- Annual Fee: {fees}
- Entry From: {entry}
- Total Students: {total_stu}
- Boarding Ratio: {boarding}
- A-Level Results: {alevel}
- GCSE Results: {gcse}
- Sports Offered: {sports}
- Scholarships: {scholarships}
- Pastoral Care: {pastoral}
- School Character: {char}
- Notable Alumni: {alumni}
- ISI Key Strengths: {isi}

Generate the following. Return ONLY valid JSON, no markdown, no explanation:

{{
  "hero_tagline_en": "One punchy sentence (max 12 words) that captures this school's strongest selling point for Thai families. Make it specific to THIS school.",
  "hero_tagline_th": "Thai translation of hero_tagline_en",
  "thai_angle_en": "3-4 sentences written specifically for Thai families. Cover: what makes this school special, pastoral/international support, one standout fact (academic or sport). Natural, confident tone. Do NOT mention Notion, databases, or that this is AI-generated.",
  "thai_angle_th": "Thai translation of thai_angle_en — natural Thai, not robotic translation",
  "parent_quote_en": "A realistic 1-2 sentence testimonial from a Thai parent. Specific detail about the school. In quotes.",
  "parent_quote_th": "Thai translation of parent_quote_en",
  "parent_attribution_en": "e.g. Thai Mother · Year 11 Student or Thai Father · Year 9 Student",
  "parent_attribution_th": "e.g. คุณแม่ชาวไทย · นักเรียน Year 11"
}}"""

    raw = call_gemini(prompt)
    return extract_json(raw)

# ── Save generated content back to Notion ────────────────────────────────────
def save_to_notion(page_id, content):
    props = {
        "Hero Tagline EN":         rich_text_prop(content.get("hero_tagline_en","")),
        "Hero Tagline TH":         rich_text_prop(content.get("hero_tagline_th","")),
        "Thai Angle EN":           rich_text_prop(content.get("thai_angle_en","")),
        "Thai Angle TH":           rich_text_prop(content.get("thai_angle_th","")),
        "Parent Quote EN":         rich_text_prop(content.get("parent_quote_en","")),
        "Parent Quote TH":         rich_text_prop(content.get("parent_quote_th","")),
        "Parent Attribution EN":   rich_text_prop(content.get("parent_attribution_en","")),
        "Parent Attribution TH":   rich_text_prop(content.get("parent_attribution_th","")),
    }
    notion_request(
        f"https://api.notion.com/v1/pages/{page_id}",
        body={"properties": props},
        method="PATCH"
    )

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("Fetching UK schools from Notion...")
    pages = fetch_schools()
    print(f"Found {len(pages)} UK schools\n")

    to_process = []
    for page in pages:
        p    = page["properties"]
        name = txt(p.get("School Name",{})).strip()
        if not name:
            continue
        if FILTER_NAME and FILTER_NAME not in name.lower():
            continue

        # Skip if already has content
        existing = txt(p.get("Thai Angle EN",{})).strip()
        if existing and not FILTER_NAME:
            continue

        to_process.append({
            "page_id":      page["id"],
            "name":         name,
            "location":     txt(p.get("Location",{})),
            "school_type":  txt(p.get("School Type",{})) or "Full Boarding",
            "fees":         txt(p.get("Boarding Fee\n Year 7 - Year 13\n Per Year",{})) or "Contact school",
            "alevel":       txt(p.get("A-Level\n(A* - A)",{})) or "Not provided",
            "gcse":         txt(p.get("GCSE\n(9 - 7)",{})) or "Not provided",
            "sports":       txt(p.get("Core Sports",{})) or txt(p.get("Sports",{})) or "Various",
            "pastoral":     txt(p.get("Pastoral Care",{})),
            "isi":          txt(p.get("ISI Key Strengths",{})),
            "alumni":       txt(p.get("Notable Alumni",{})),
            "school_char":  txt(p.get("School Character",{})),
            "boarding_ratio": txt(p.get("Boarding Ratio",{})),
            "entry_year":   txt(p.get("Lowest Boarding Entry Year",{})) or "Year 9",
            "total_students": txt(p.get("Total Number of Student",{})) or "—",
            "scholarships": txt(p.get("Update Scholarships",{})) or "Contact school",
        })

    print(f"Schools needing content: {len(to_process)}\n")
    if DRY_RUN:
        for s in to_process:
            print(f"  Would generate: {s['name']}")
        return

    success, failed = 0, []

    for i, school in enumerate(to_process, 1):
        name = school["name"]
        print(f"[{i}/{len(to_process)}] {name}...", end=" ", flush=True)
        try:
            content = generate_content(school)
            save_to_notion(school["page_id"], content)
            print(f"✅")
            success += 1
            time.sleep(0.4)  # gentle rate limit
        except Exception as e:
            print(f"❌ {e}")
            failed.append(name)
            time.sleep(1)

    print(f"\n✅ Done: {success}/{len(to_process)} schools updated in Notion")
    if failed:
        print(f"❌ Failed ({len(failed)}): {', '.join(failed)}")

if __name__ == "__main__":
    main()
