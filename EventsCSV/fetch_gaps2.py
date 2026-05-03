import urllib.request, urllib.parse, json, time, csv, os, re

ENDPOINT = 'https://query.wikidata.org/sparql'
BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'
QID_RE = re.compile(r'^Q\d+$')

HEADERS = {
    'Accept': 'application/sparql-results+json',
    'User-Agent': 'EpochGame/1.0 (history quiz; contact srivats66@gmail.com)'
}

def run_query(sparql):
    params = urllib.parse.urlencode({'query': sparql, 'format': 'json'})
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"ERROR: {e}")
        return None

BANDS = [
    (1000, 1200), (1200, 1350), (1350, 1500),
    (1500, 1650), (1650, 1800), (1800, 1900),
    (1900, 1970), (1970, 2027),
]

# ── 1. EXPLORATION — use P571 (inception) for expeditions ───────────────────
EXPLORATION_TYPES = 'wd:Q83821 wd:Q2281788 wd:Q1172478 wd:Q1172478 wd:Q35509'

# ── 2. SCIENCE — broader types, use P571 ────────────────────────────────────
SCIENCE_TYPES = 'wd:Q12772819 wd:Q166620 wd:Q2725376 wd:Q2996394 wd:Q7187 wd:Q35120'

JOBS = [
    ('exploration', EXPLORATION_TYPES, 'wdt:P571', 'exploration_gap2'),
    ('science',     SCIENCE_TYPES,     'wdt:P571', 'science_gap2'),
]

all_rows = []
seen_ids = set()

# Load existing IDs from gap_fills to avoid dupes
with open(os.path.join(BASE, 'gap_fills.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        seen_ids.add(r['id'])

for (tag, types, date_prop, source) in JOBS:
    print(f"\n{'='*40}\nCategory: {tag.upper()}")
    cat_rows = []
    for (y_min, y_max) in BANDS:
        sparql = f"""
SELECT DISTINCT ?event ?eventLabel (YEAR(?date) AS ?year) ?countryLabel WHERE {{
  VALUES ?type {{ {types} }}
  ?event wdt:P31 ?type ;
         {date_prop} ?date .
  FILTER(YEAR(?date) >= {y_min} && YEAR(?date) < {y_max})
  OPTIONAL {{ ?event wdt:P17 ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY RAND()
LIMIT 60
""".strip()
        print(f"  {y_min}–{y_max} ... ", end='', flush=True)
        data = run_query(sparql)
        if not data:
            print("FAILED — skip")
            time.sleep(3)
            continue
        kept = 0
        for r in data.get('results', {}).get('bindings', []):
            label = r.get('eventLabel', {}).get('value', '')
            if QID_RE.match(label): continue
            eid = r.get('event', {}).get('value', '').split('/')[-1]
            if eid in seen_ids: continue
            yr = r.get('year', {}).get('value', '')
            if not yr: continue
            country = r.get('countryLabel', {}).get('value', '')
            seen_ids.add(eid)
            cat_rows.append({'id': eid, 'label': label, 'year': int(yr),
                             'country': country, 'tag': tag, 'source_file': source})
            kept += 1
        print(f"{kept} kept")
        time.sleep(1.5)
    print(f"  Subtotal: {len(cat_rows)}")
    all_rows.extend(cat_rows)

out = os.path.join(BASE, 'gap_fills2.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['id','label','year','country','tag','source_file'])
    w.writeheader()
    w.writerows(sorted(all_rows, key=lambda r: r['year']))
print(f"\n✓ {len(all_rows)} new events → gap_fills2.csv")
