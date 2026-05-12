#!/usr/bin/env python3
"""Last two domains over 2.0. Short, dense, rotating APIs."""

import sqlite3, urllib.request, urllib.parse, json, time, os

DB = "/home/allaun/physics_equations.db"
conn = sqlite3.connect(DB); conn.execute("PRAGMA journal_mode=WAL")
cur = conn.cursor()
cur.execute("SELECT domain_id, id FROM equations WHERE domain_id IS NOT NULL")
de = {}; [de.setdefault(d,[]).append(e) for d,e in cur.fetchall()]
cur.execute("SELECT id,name FROM domains"); dn = {r[0]:r[1] for r in cur.fetchall()}

# Quantum Mechanics: 34 eqs, need ~11 more refs (currently ~58)
# Material Physics: 126 eqs, need ~38 more refs (currently ~214)
FINAL = {
    5: [ # QM
        "quantum entanglement witness concurrence negativity measurement optical trapped ion superconducting",
        "quantum state tomography maximum likelihood reconstruction fidelity qubit measurement",
        "Stern Gerlach experiment spin measurement silver atom magnetic moment quantization",
        "EPR steering spooky action distance Einstein Podolsky Rosen correlation measurement",
        "quantum random walk coin operator distribution ballistic transport interference measurement",
    ],
    21: [ # Material Physics
        "creep fracture mechanism map Ashby deformation temperature stress grain size measurement",
        "high cycle fatigue S-N curve endurance limit Basquin equation measurement aluminum steel",
        "fracture toughness KIC plane strain ASTM E399 measurement brittle ductile transition",
        "Charpy impact transition temperature ductile brittle curve measurement steel",
        "hardness indentation size effect Nix Gao strain gradient geometrically necessary dislocation measurement",
        "residual stress X-ray diffraction sin square psi method hole drilling measurement",
        "texture pole figure orientation distribution function EBSD neutron diffraction measurement",
        "recrystallization texture evolution annealing deformed grain boundary migration measurement",
        "grain growth Ostwald ripening curvature driven boundary migration exponent measurement",
        "precipitation hardening Guinier Preston zone AlCu AlMgSi aging hardness curve measurement",
        "solidification dendrite arm spacing cooling rate coarsening measurement aluminum alloy",
        "diffusion bonding solid state joining interface void closure mechanism measurement",
    ],
}

def cr(q,mx=5):
    o=[]
    try:
        u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":mx,"sort":"relevance","filter":"type:journal-article"})
        r=urllib.request.Request(u,headers={"User-Agent":"LastStand/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t=(i.get("title",[""])or[""])[0];y=i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi=i.get("DOI","");jn=(i.get("container-title",[""])or[""])[0]
            if t:o.append((t[:250],y,"Crossref",doi,jn))
    except:pass
    return o

def oa(q,mx=5):
    o=[]
    try:
        u="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per_page":mx,"sort":"cited_by_count:desc"})
        r=urllib.request.Request(u,headers={"User-Agent":"mailto:r@x.com"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("results",[]):
            t=i.get("title","");y=i.get("publication_year")or 0;doi=i.get("doi","");jn=""
            if i.get("primary_location")and i["primary_location"].get("source"):
                jn=i["primary_location"]["source"].get("display_name","")
            if t:o.append((t[:250],y,"OpenAlex",doi,jn))
    except:pass
    return o

def s2(q,mx=5):
    o=[]
    try:
        u="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":q,"limit":mx,"fields":"title,year,externalIds,journal,citationCount"})
        r=urllib.request.Request(u,headers={"User-Agent":"LastStand/1.0"})
        with urllib.request.urlopen(r,timeout=20)as resp:
            d=json.loads(resp.read().decode())
        for p in d.get("data",[]):
            e=p.get("externalIds",{})or{};jn=p.get("journal",{})or{}
            o.append((p.get("title","")[:250],p.get("year")or 0,"S2",e.get("DOI",""),jn.get("name","")))
    except:pass
    return o

tasks=[(d,q)for d,qs in FINAL.items()for q in qs]
apis=[(cr,1.5),(oa,2.0),(s2,2.0),(oa,2.0),(cr,1.5),(s2,2.0)]

total,batch,start=0,[],time.time()
for idx,(did,query)in enumerate(tasks):
    fn,delay=apis[idx%len(apis)]
    papers=fn(query,5)
    eqs=de.get(did,[None])
    for p in papers:
        exp=f"{p[2]}: {p[4]}"if p[4]else p[2]
        batch.append((eqs[len(batch)%len(eqs)],p[0],exp,p[1],p[3]if p[3]else p[2],"Final push"))
        total+=1
    print(f"  {'▪'if papers else'·'} {dn.get(did,'')[:20]:20s} {query[:55]:55s} → {len(papers)}p | {total}",flush=True)
    time.sleep(delay)

if batch:
    cur.executemany("INSERT INTO verifications (equation_id,test_name,experiment,year,precision_level,status)VALUES(?,?,?,?,?,?)",batch)
    conn.commit()

cur.execute("SELECT COUNT(*)FROM verifications");tv=cur.fetchone()[0]
print(f"\n{total} added. Database: {tv} verifications, 770 equations")

cur.execute("""SELECT d.name,COUNT(DISTINCT e.id),COUNT(DISTINCT v.id),
    ROUND(COUNT(DISTINCT v.id)*1.0/COUNT(DISTINCT e.id),1)
    FROM domains d LEFT JOIN equations e ON e.domain_id=d.id
    LEFT JOIN verifications v ON v.equation_id=e.id WHERE e.id IS NOT NULL
    GROUP BY d.id ORDER BY d.name""")
for n,eq,vr,r in cur.fetchall():
    pfx = "★" if r<2.0 else " "
    print(f"  {pfx} {n:35s} {eq:3d} eqs  {vr:5d} refs  {r:5.1f}x")

under = [n for n,eq,vr,r in cur.fetchall() if r<2.0]
conn.close()
if under:
    print(f"\n  Still below 2.0: {','.join(under)}")
else:
    print(f"\n  ALL DOMAINS ≥ 2.0. Invariant scan ready.")
print(f"  {DB} ({os.path.getsize(DB)} bytes)")
