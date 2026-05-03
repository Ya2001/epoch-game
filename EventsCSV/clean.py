import csv, re, os

BASE = '/Users/akshay/Desktop/Phone Game/EventsCSV'

FILES = [
    ('WarsRecord.csv', 'war'),
    ('Inventions.csv', 'technology'),
    ('Coups.csv', 'revolution'),
    ('Treaties.csv', 'empire'),
    ('Disasters.csv', 'culture'),
]

# Patterns that indicate garbage rows
QID_RE = re.compile(r'^Q\d+$')
BAD_PHRASES = [
    'voting', 'election', 'society for', 'co.', '& sons', '& co',
    'robert gilmor', 'mutual relief', 'committee', 'association',
    'prime minister voting', 'suicide attack', 'strike on', 'airstrike',
]

rows = []
seen_ids = set()

for fname, tag in FILES:
    path = os.path.join(BASE, fname)
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            event_id = row['event'].split('/')[-1]  # extract QID
            label = row['eventLabel'].strip()
            year = row.get('year', '').strip()
            country = row.get('countryLabel', '').strip()

            # Skip unlabeled (QID as label)
            if QID_RE.match(label):
                continue
            # Skip already seen
            if event_id in seen_ids:
                continue
            # Skip garbage phrases
            label_lower = label.lower()
            if any(p in label_lower for p in BAD_PHRASES):
                continue
            # Skip missing year
            if not year:
                continue
            # Skip out of range
            try:
                yr = int(year)
            except ValueError:
                continue
            if yr < 1000 or yr > 2026:
                continue

            seen_ids.add(event_id)
            rows.append({
                'id': event_id,
                'label': label,
                'year': yr,
                'country': country,
                'tag': tag,
                'source_file': fname,
            })
            count += 1
        print(f"{fname}: {count} kept")

# Sort by year
rows.sort(key=lambda r: r['year'])

out_path = os.path.join(BASE, 'master_clean.csv')
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id','label','year','country','tag','source_file'])
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal: {len(rows)} events → master_clean.csv")

# Print year distribution
from collections import Counter
decades = Counter((r['year'] // 100) * 100 for r in rows)
for century in sorted(decades):
    print(f"  {century}s: {decades[century]}")
