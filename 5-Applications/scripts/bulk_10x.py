#!/usr/bin/env python3
"""
10x scaler — generates queries from equation titles, rotates 8 API slots.
Targets under-filled equations first. Runs until 10x achieved or 6 hour timeout.
Writes incrementally so crash-tolerant.
"""

import sqlite3, urllib.request, urllib.parse, json, time, os, re, random, sys

DB = "/home/allaun/physics_equations.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=OFF")
conn.execute("PRAGMA cache_size=-4000000")
cur = conn.cursor()

# Get equations sorted by ref count (fewest first)
cur.execute("""
    SELECT e.id, e.title, e.domain_id, COUNT(v.id) as refs
    FROM equations e
    LEFT JOIN verifications v ON v.equation_id = e.id
    GROUP BY e.id
    HAVING refs < 10
    ORDER BY refs ASC
""")
targets = [(r[0], r[1], r[2], r[3]) for r in cur.fetchall()]
print(f"{len(targets)} equations below 10x | total needed: {sum(10-t[3] for t in targets)}")

cur.execute("SELECT id, name FROM domains")
dnames = {r[0]: r[1] for r in cur.fetchall()}

# ================================================================
# Equation title → search query extractor
# ================================================================
def title_to_query(title):
    """Extract the most meaningful words from an equation title for search."""
    # Remove special chars, brackets, quotes
    clean = re.sub(r'[─\(\)\[\]\{\}""''"".,:;\n\r]', ' ', title)
    # Split and filter short words
    words = [w for w in clean.split() if len(w) > 2 and w.lower() not in
        ('the', 'and', 'for', 'this', 'that', 'with', 'from', 'are', 'was',
         'has', 'had', 'its', 'not', 'but', 'all', 'can', 'may', 'will',
         'been', 'one', 'two', 'two', 'three', 'also', 'into', 'than',
         'over', 'under', 'after', 'such', 'each', 'both', 'more', 'some')]
    # Take first meaningful chunk
    if len(words) > 12:
        return ' '.join(words[:12])
    return ' '.join(words)

# ================================================================
# Build query queue: [equation_id, query_string]
# ================================================================
tasks = []
for eq_id, title, did, refs in targets:
    q = title_to_query(title)
    if len(q) < 10:
        # Fallback: use domain name + first few title words
        dname = dnames.get(did, 'physics')
        q = dname + ' ' + ' '.join(title.split()[:6])
    # Each equation gets (10 - current_refs) queries at minimum
    needed = max(10 - refs, 1)
    for _ in range(min(needed, 3)):  # Max 3 queries per eq per cycle
        tasks.append((eq_id, q))

print(f"Generated {len(tasks)} queries ({len(targets)} unique equations)")

# ================================================================
# API FETCHERS — fast
# ================================================================
def cr(q, mx=5):
    o=[]
    try:
        u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":mx,"sort":"relevance","filter":"type:journal-article"})
        r=urllib.request.Request(u,headers={"User-Agent":"10xScaler/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t=(i.get("title",[""])or[""])[0];y=i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi=i.get("DOI","");jn=(i.get("container-title",[""])or[""])[0]
            if t:o.append((t[:250],y,"Crossref",doi,jn))
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
            if t:o.append((t[:250],y,"OpenAlex",doi,jn))
    except:pass
    return o

def s2(q, mx=5):
    o=[]
    try:
        u="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":q,"limit":mx,"fields":"title,year,externalIds,journal,citationCount"})
        r=urllib.request.Request(u,headers={"User-Agent":"10xScaler/1.0"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e=p.get("externalIds",{})or{};jn=p.get("journal",{})or{}
            o.append((p.get("title","")[:250],p.get("year")or 0,"S2",e.get("DOI",""),jn.get("name","")))
    except:pass
    return o

def ep(q, mx=5):
    o=[]
    try:
        u="https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+urllib.parse.urlencode({"query":q,"resultType":"core","pageSize":mx,"format":"json"})
        r=urllib.request.Request(u,headers={"User-Agent":"10xScaler/1.0"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("resultList",{}).get("result",[]):
            t=i.get("title","");y=int(i.get("firstPublicationDate","0")[:4]) if i.get("firstPublicationDate") else 0
            doi=i.get("doi","");jn=i.get("journalTitle","")
            if t:o.append((t[:250],y,"EuropePMC",doi,jn))
    except:pass
    return o

# ================================================================
# MAIN PIPELINE — 8 API slots, 1.5s spacing
# ================================================================
apis = [(cr,1.5),(oa,1.7),(s2,1.7),(ep,1.5),
        (oa,1.7),(cr,1.5),(s2,1.7),(oa,1.7)]

total, batch, start = 0, [], time.time()
flush_count, last_stats = 0, start
eq_refs_added = {}  # eq_id → count added this run

print(f"\n{'═'*60}")
print(f"10x SCALER — {len(tasks)} queries, 8 API slots, 1.5-1.7s spacing")
print(f"ETA: ~{len(tasks)*1.6/60:.0f} min | Crash-tolerant (incremental flush)")
print(f"{'═'*60}\n")

for idx, (eq_id, query) in enumerate(tasks):
    fn, delay = apis[idx % len(apis)]
    papers = fn(query, 5)

    for p in papers:
        exp = f"{p[2]}: {p[4]}" if p[4] else p[2]
        batch.append((eq_id, p[0], exp, p[1], p[3] if p[3] else p[2], "10x scale"))
        total += 1
        eq_refs_added[eq_id] = eq_refs_added.get(eq_id, 0) + 1

    # Progress every 20 queries or 30s
    if idx % 20 == 0:
        t = time.time() - start
        rate = total/max(t,1)*60
        eta = (len(tasks) - idx) * delay / 60
        # Count how many equations hit 10x
        cur.execute("SELECT COUNT(*) FROM (SELECT equation_id, COUNT(*) as c FROM verifications GROUP BY equation_id HAVING c >= 10)")
        done = cur.fetchone()[0]
        pct = done/770*100
        print(f"  [{idx}/{len(tasks)}] {total}p added | {done}/770 at 10x ({pct:.0f}%) | {rate:.0f}p/min | {eta:.1f}min left", flush=True)

    # Flush every 40 records
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
# FINAL REPORT
# ================================================================
cur.execute("SELECT COUNT(*) FROM verifications"); tv = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM (SELECT equation_id, COUNT(*) as c FROM verifications GROUP BY equation_id HAVING c >= 10)")
at_10x = cur.fetchone()[0]

elapsed = time.time() - start
print(f"\n{'═'*60}")
print(f"DONE — {tv} total verifications | {at_10x}/770 equations at 10x+ ({at_10x/770*100:.0f}%)")
print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f} min) | {total} added this pass")
print(f"{'═'*60}\n")

# Domain summary
cur.execute("""
    SELECT d.name,
           COUNT(DISTINCT e.id) as eqs,
           COUNT(DISTINCT v.id) as refs,
           ROUND(AVG(per_eq.cnt),1) as avg_refs,
           COUNT(CASE WHEN per_eq.cnt < 10 THEN 1 END) as below_10
    FROM equations e
    JOIN domains d ON e.domain_id = d.id
    LEFT JOIN (SELECT equation_id, COUNT(*) as cnt FROM verifications GROUP BY equation_id) per_eq ON per_eq.equation_id = e.id
    GROUP BY d.id
    ORDER BY avg_refs
""")

print(f"{'Domain':35s} {'Eqs':>4s} {'Refs':>5s} {'Avg':>5s} {'<10x':>5s}")
print("-"*55)
for n, eq, vr, avg, below in cur.fetchall():
    bar = "█" * min(int(avg), 50)
    print(f"{n:35s} {eq:4d} {vr:5d} {avg:5.1f} {below:5d} {bar}")

conn.close()
print(f"\n{DB} ({os.path.getsize(DB)} bytes)")
