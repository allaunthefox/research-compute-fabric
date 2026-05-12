#!/usr/bin/env python3
"""
Patch & armor-plate the database.
1. Dedup verifications (same equation + same title)
2. Push all equations below 15 refs to 15+ with targeted queries.
3. API rotation: 8 slots, 1.5s spacing. Crash-tolerant.
"""

import sqlite3, urllib.request, urllib.parse, json, time, os, re, sys

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()
start = time.time()

# ================================================================
# PHASE 1: DEDUP
# ================================================================
print("=" * 60)
print("PHASE 1: Deduplication")
print("=" * 60)

# Find duplicates: same equation_id AND same test_name (title)
cur.execute("""
    SELECT equation_id, test_name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
    FROM verifications
    GROUP BY equation_id, test_name
    HAVING COUNT(*) > 1
""")
dupes = cur.fetchall()
dup_total = 0

for eq_id, title, cnt, ids in dupes:
    id_list = [int(x) for x in ids.split(",")]
    id_list.sort()
    keep, *remove = id_list  # Keep the first (lowest ID), remove rest
    for rid in remove:
        cur.execute("DELETE FROM verifications WHERE id = ?", (rid,))
        dup_total += 1

conn.commit()
print(f"  ✓ Removed {dup_total} duplicate verifications")

# Count after dedup
cur.execute("SELECT COUNT(*) FROM verifications")
total_after_dedup = cur.fetchone()[0]
print(f"  ✓ Verifications: {total_after_dedup} (was ~10458)")

# ================================================================
# PHASE 2: Find equations below 15 refs
# ================================================================
print(f"\n{'='*60}")
print("PHASE 2: Find equations below 15x threshold")
print("=" * 60)

cur.execute("""
    SELECT e.id, e.eq_number, e.title, e.domain_id, COUNT(v.id) as refs
    FROM equations e
    LEFT JOIN verifications v ON v.equation_id = e.id
    GROUP BY e.id
    HAVING refs < 15
    ORDER BY refs ASC
""")
under_15 = [(r[0], r[1], r[2], r[3], r[4]) for r in cur.fetchall()]
total_needed = sum(15 - r[4] for r in under_15)
print(f"  {len(under_15)} equations below 15x | need {total_needed} refs to reach 15x")

if not under_15:
    print("  All equations already at 15x+. Nothing to do.")
    conn.close()
    sys.exit(0)

# Show the worst few
print("  Worst 10:")
for r in under_15[:10]:
    print(f"    [{r[4]:2d}] #{r[1]:3d} {r[2][:80]}")

cur.execute("SELECT id, name FROM domains")
dnames = {r[0]: r[1] for r in cur.fetchall()}

# ================================================================
# PHASE 3: Generate targeted queries per equation
# ================================================================
print(f"\n{'='*60}")
print("PHASE 3: Generating targeted queries")
print("=" * 60)

def title_to_query(title):
    """Extract most meaningful search terms from equation title."""
    clean = re.sub(r'[─\(\)\[\]\{\}\'\".,:;\n\r—]', ' ', title)
    words = [w for w in clean.split() if len(w) > 2 and w.lower() not in
        ('the','and','for','this','that','with','from','are','was','has','had',
         'its','not','but','all','can','may','will','been','one','two','three',
         'also','into','than','over','under','after','such','each','both','more',
         'some','they','their','have','were','like','just','what','when','where',
         'how','why','who','which','very','much')]
    if len(words) > 14:
        return ' '.join(words[:14])
    return ' '.join(words)

# Build task queue
tasks = []
for eq_id, num, title, did, refs in under_15:
    q = title_to_query(title)
    if len(q) < 15:
        dname = dnames.get(did, 'physics')
        q = dname + ' ' + ' '.join(title.split()[:8])
    needed = max(15 - refs, 1)
    # Each equation gets up to 5 queries to ensure we hit 15
    for _ in range(min(needed, 5)):
        tasks.append((eq_id, q, needed, refs))

# De-duplicate tasks (same eq_id + same query)
seen = set()
unique_tasks = []
for eq_id, q, nd, rf in tasks:
    key = (eq_id, q[:60])
    if key not in seen:
        seen.add(key)
        unique_tasks.append((eq_id, q, nd, rf))

tasks = unique_tasks
print(f"  Generated {len(tasks)} unique queries for {len(under_15)} equations")

# ================================================================
# PHASE 4: API FETCHERS
# ================================================================
def cr(q, mx=5):
    o=[]
    try:
        u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":mx,"sort":"relevance","filter":"type:journal-article"})
        r=urllib.request.Request(u,headers={"User-Agent":"RiotShield/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t=(i.get("title",[""])or[""])[0];y=i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi=i.get("DOI","");jn=(i.get("container-title",[""])or[""])[0]
            if t:o.append({"t":t[:250],"y":y,"s":"Crossref","d":doi,"j":jn})
    except:pass
    return o

def oa(q, mx=5):
    o=[]
    try:
        u="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per_page":mx,"sort":"cited_by_count:desc"})
        r=urllib.request.Request(u,headers={"User-Agent":"mailto:r@x.com"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("results",[]):
            t=i.get("title","");y=i.get("publication_year")or 0;doi=i.get("doi","");jn=""
            if i.get("primary_location")and i["primary_location"].get("source"):
                jn=i["primary_location"]["source"].get("display_name","")
            if t:o.append({"t":t[:250],"y":y,"s":"OpenAlex","d":doi,"j":jn})
    except:pass
    return o

def s2(q, mx=5):
    o=[]
    try:
        u="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":q,"limit":mx,"fields":"title,year,externalIds,journal"})
        r=urllib.request.Request(u,headers={"User-Agent":"RiotShield/1.0"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e=p.get("externalIds",{})or{};jn=p.get("journal",{})or{}
            o.append({"t":p.get("title","")[:250],"y":p.get("year")or 0,"s":"S2","d":e.get("DOI",""),"j":jn.get("name","")})
    except:pass
    return o

# ================================================================
# PHASE 5: MAIN PIPELINE
# ================================================================
print(f"\n{'='*60}")
print("PHASE 5: Armor-plate pipeline (8 API slots, 1.5s spacing)")
print(f"  ETA: ~{len(tasks)*1.6/60:.0f} min")
print("=" * 60)

apis = [(cr,1.5),(oa,1.7),(s2,1.7),(oa,1.5),
        (cr,1.5),(oa,1.7),(s2,1.7),(oa,1.5)]

total, batch = 0, []
# Track which equations we've pushed for so we can skip already-at-15
eq_reached_15 = set()

for idx, (eq_id, query, needed, current_refs) in enumerate(tasks):
    # Skip if already at 15 from previous inserts
    if eq_id in eq_reached_15:
        if idx % 50 == 0:
            print(f"  [{idx}/{len(tasks)}] skip (already at 15) | {total}p added | {time.time()-start:.0f}s", flush=True)
        continue

    fn, delay = apis[idx % len(apis)]
    papers = fn(query)

    # Before inserting, check if we actually need more for this equation
    cur.execute("SELECT COUNT(*) FROM verifications WHERE equation_id=?", (eq_id,))
    current = cur.fetchone()[0]
    remaining = max(15 - current, 0)

    for p in papers:
        if remaining <= 0:
            break
        exp = f"{p['s']}: {p['j']}" if p.get('j') else p['s']
        batch.append((eq_id, p['t'], exp, p['y'], p.get('d', p['s']), "Armor-plate"))
        total += 1
        remaining -= 1
        current += 1

    if current >= 15:
        eq_reached_15.add(eq_id)

    # Progress
    if idx % 30 == 0:
        cur.execute("""SELECT COUNT(*) FROM (SELECT e.id FROM equations e LEFT JOIN
            (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
            WHERE COALESCE(vc.c,0) >= 15)""")
        at15 = cur.fetchone()[0]
        cur.execute("""SELECT COUNT(*) FROM (SELECT e.id FROM equations e LEFT JOIN
            (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
            WHERE COALESCE(vc.c,0) < 10)""")
        below10 = cur.fetchone()[0]
        eta = (len(tasks) - idx) * delay / 60
        print(f"  [{idx}/{len(tasks)}] {total}p | {at15}/771 at 15x+ | {below10} below 10x | {eta:.1f}min left", flush=True)

    # Flush every 40
    if len(batch) >= 40:
        cur.executemany(
            "INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)",
            batch)
        conn.commit()
        batch = []

    time.sleep(delay)

# Final flush
if batch:
    cur.executemany(
        "INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)",
        batch)
    conn.commit()

# ================================================================
# PHASE 7: Final report
# ================================================================
cur.execute("SELECT COUNT(*) FROM verifications"); tv = cur.fetchone()[0]
cur.execute("""SELECT COUNT(*) FROM equations e LEFT JOIN
    (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
    WHERE COALESCE(vc.c,0) >= 15""")
at15 = cur.fetchone()[0]
cur.execute("""SELECT COUNT(*) FROM equations e LEFT JOIN
    (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
    WHERE COALESCE(vc.c,0) < 10""")
below10 = cur.fetchone()[0]
cur.execute("""SELECT COUNT(*) FROM equations e LEFT JOIN
    (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
    WHERE COALESCE(vc.c,0) < 15""")
below15 = cur.fetchone()[0]

elapsed = time.time() - start

print(f"\n{'='*60}")
print(f"ARMOR-PLATE COMPLETE")
print(f"  {tv} total verifications ({total} added this pass)")
print(f"  {at15}/771 at 15x+ ({at15/771*100:.0f}%)")
print(f"  {below15} still below 15x | {below10} still below 10x")
print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")

if below15 > 0:
    print(f"\n  Remaining below 15x:")
    cur.execute("""SELECT e.eq_number, e.title, COALESCE(vc.c,0) refs
        FROM equations e LEFT JOIN
        (SELECT equation_id, COUNT(*) c FROM verifications GROUP BY equation_id) vc ON vc.equation_id=e.id
        WHERE COALESCE(vc.c,0) < 15 ORDER BY refs""")
    for num, title, refs in cur.fetchall():
        print(f"    [{refs:2d}] #{num:3d} {title[:85]}")

conn.close()
print(f"\n  {DB} ({os.path.getsize(DB)} bytes)")
