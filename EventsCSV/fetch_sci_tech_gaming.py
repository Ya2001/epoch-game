import urllib.request, urllib.parse, json, time, csv, os, re

ENDPOINT = 'https://query.wikidata.org/sparql'
BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'
QID_RE = re.compile(r'^Q\d+$')
HEADERS = {
    'Accept': 'application/sparql-results+json',
    'User-Agent': 'EpochGame/1.0 (history quiz; contact srivats66@gmail.com)'
}

def run_query(sparql, timeout=35):
    params = urllib.parse.urlencode({'query': sparql, 'format': 'json'})
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Load all existing IDs to avoid dupes
seen_ids = set()
for fname in ['master_clean.csv','gap_fills.csv','gap_fills2.csv']:
    p = os.path.join(BASE, fname)
    if os.path.exists(p):
        with open(p, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f): seen_ids.add(r['id'])

all_rows = []

# ── 1. SCIENCE: single type Q12772819, use P571, split by band ──────────────
print("=== SCIENCE (Q12772819, P571) ===")
for y_min, y_max in [(1000,1500),(1500,1700),(1700,1800),(1800,1900),(1900,1960),(1960,2027)]:
    sparql = f"""
SELECT DISTINCT ?event ?eventLabel (YEAR(?date) AS ?year) ?countryLabel WHERE {{
  ?event wdt:P31 wd:Q12772819 ; wdt:P571 ?date .
  FILTER(YEAR(?date) >= {y_min} && YEAR(?date) < {y_max})
  OPTIONAL {{ ?event wdt:P17 ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}} ORDER BY RAND() LIMIT 60"""
    print(f"  {y_min}–{y_max} ... ", end='', flush=True)
    data = run_query(sparql)
    kept = 0
    if data:
        for r in data.get('results',{}).get('bindings',[]):
            label = r.get('eventLabel',{}).get('value','')
            if QID_RE.match(label): continue
            eid = r.get('event',{}).get('value','').split('/')[-1]
            if eid in seen_ids: continue
            yr = r.get('year',{}).get('value','')
            if not yr: continue
            country = r.get('countryLabel',{}).get('value','')
            seen_ids.add(eid)
            all_rows.append({'id':eid,'label':label,'year':int(yr),'country':country,'tag':'science','source_file':'science_q3'})
            kept += 1
    print(f"{kept} kept")
    time.sleep(2)

# ── 2. TECHNOLOGY: inventions Q483247, P571 ──────────────────────────────────
print("\n=== TECHNOLOGY (Q483247 invention, P571) ===")
for y_min, y_max in [(1000,1600),(1600,1800),(1800,1900),(1900,1960),(1960,2027)]:
    sparql = f"""
SELECT DISTINCT ?event ?eventLabel (YEAR(?date) AS ?year) ?countryLabel WHERE {{
  ?event wdt:P31 wd:Q483247 ; wdt:P571 ?date .
  FILTER(YEAR(?date) >= {y_min} && YEAR(?date) < {y_max})
  OPTIONAL {{ ?event wdt:P17 ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}} ORDER BY RAND() LIMIT 60"""
    print(f"  {y_min}–{y_max} ... ", end='', flush=True)
    data = run_query(sparql)
    kept = 0
    if data:
        for r in data.get('results',{}).get('bindings',[]):
            label = r.get('eventLabel',{}).get('value','')
            if QID_RE.match(label): continue
            eid = r.get('event',{}).get('value','').split('/')[-1]
            if eid in seen_ids: continue
            yr = r.get('year',{}).get('value','')
            if not yr: continue
            country = r.get('countryLabel',{}).get('value','')
            seen_ids.add(eid)
            all_rows.append({'id':eid,'label':label,'year':int(yr),'country':country,'tag':'technology','source_file':'tech_q3'})
            kept += 1
    print(f"{kept} kept")
    time.sleep(2)

# ── 3. GAMING: home consoles + handheld consoles, release dates ──────────────
print("\n=== GAMING (consoles, P571) ===")
sparql = """
SELECT DISTINCT ?console ?consoleLabel (YEAR(?date) AS ?year) ?countryLabel WHERE {
  VALUES ?type { wd:Q8093 wd:Q941818 wd:Q17589470 wd:Q7889 }
  ?console wdt:P31 ?type ; wdt:P571 ?date .
  FILTER(YEAR(?date) >= 1970 && YEAR(?date) <= 2026)
  OPTIONAL { ?console wdt:P495 ?country }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
} ORDER BY ?date"""
print("  1970–2026 ... ", end='', flush=True)
data = run_query(sparql, timeout=45)
kept = 0
if data:
    for r in data.get('results',{}).get('bindings',[]):
        label = r.get('consoleLabel',{}).get('value','')
        if QID_RE.match(label): continue
        eid = r.get('console',{}).get('value','').split('/')[-1]
        if eid in seen_ids: continue
        yr = r.get('year',{}).get('value','')
        if not yr: continue
        country = r.get('countryLabel',{}).get('value','')
        seen_ids.add(eid)
        all_rows.append({'id':eid,'label':label,'year':int(yr),'country':country,'tag':'gaming','source_file':'gaming_q1'})
        kept += 1
print(f"{kept} kept")

# Write output
out = os.path.join(BASE, 'gap_fills3.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['id','label','year','country','tag','source_file'])
    w.writeheader()
    w.writerows(sorted(all_rows, key=lambda r: r['year']))

from collections import Counter
print(f"\n✓ {len(all_rows)} events → gap_fills3.csv")
for t,n in Counter(r['tag'] for r in all_rows).most_common():
    print(f"  {t}: {n}")
