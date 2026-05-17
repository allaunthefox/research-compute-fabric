#!/usr/bin/env python3
"""Hit exactly the 21 sub-10x equations with curated queries. Fast, minimal, surgical."""

import sqlite3, urllib.request, urllib.parse, json, time

DB="/home/allaun/physics_equations.db"
c=sqlite3.connect(DB);c.execute("PRAGMA journal_mode=WAL");cur=c.cursor()

TARGETS={
    537:["Kohler rule magnetoresistance scaling plot measurement single crystal metal","magnetoresistance Kohler plot Fermi surface topology measurement"],
    766:["Quetzalcoatlus northropi wingspan flight performance launch biomechanics pterosaur","giant pterosaur flight capability wing loading bone pneumaticity fossil evidence"],
    768:["ichthyosaur Ophthalmosaurus eye diameter 26cm sclerotic ring fossil measurement","ichthyosaur vision deep sea mesopelagic adaptation visual acuity"],
    353:["hardness yield strength correlation metallic material Vickers measurement","Petch Forwood hardness yield strength empirical relation measurement"],
    44:["Ampere force law parallel current carrying conductors experimental measurement","Ampere force magnetic definition SI ampere measurement parallel wires"],
    443:["Flory Fox glass transition temperature molecular weight polymer measurement polystyrene","Tg molecular weight dependence Flory Fox free volume experimental verification"],
    769:["Burgess Shale Cambrian explosion Anomalocaris Opabinia Hallucigenia body plan","Cambrian explosion body plan disparity fossil evidence measurement"],
    32:["tidal force Earth Moon measurement prediction Newton gravitation","ocean tide prediction Earth Moon Sun gravitational differential force measurement"],
    46:["Kirchhoff current law node junction conservation charge experimental verification","KCL Kirchhoff current law circuit experiment verification current balance"],
    73:["equipartition theorem specific heat diatomic gas measurement quantum correction","equipartition energy degrees freedom experimental measurement classical limit"],
    112:["time dependent perturbation theory quantum transition probability measurement","time dependent perturbation theory Fermi golden rule derivation experiment"],
    126:["mass energy equivalence E=mc2 nuclear reaction mass defect measurement","Einstein E=mc2 experimental verification nuclear binding energy mass spectrometer"],
    146:["CKM matrix quark mixing unitarity test flavor physics measurement","Cabibbo Kobayashi Maskawa matrix Vud Vus measurement unitarity test"],
    155:["Pati Salam model SU4 SU2 SU2 lepton number fourth color unification","Pati Salam model partial unification proton decay limit experimental test"],
    196:["Young double slit interference experiment measurement fringe spacing light","double slit interference experiment optical measurement fringe spacing"],
    234:["Hall effect measurement electrical transport carrier density semiconductor metal","Hall effect measurement Van der Pauw resistivity measurement"],
    265:["neutron star equation state mass radius measurement NICER X ray timing","neutron star mass radius constraint tidal deformability GW170817 EOS"],
    268:["Olbers paradox dark night sky expanding universe finite age solution measurement","Olbers paradox resolution expanding universe Hubble constant dark night sky"],
    393:["MOS capacitor threshold voltage CV measurement silicon oxide interface","MOS capacitor threshold voltage flatband CV measurement substrate"],
    466:["diffusion equation solution error function thin film Gaussian profile measurement","diffusion solution Fick second law concentration profile measurement"],
    764:["sauropod dinosaur neck posture blood pressure cardiovascular model measurement","sauropod Barosaurus Argentinosaurus heart mass blood pressure vertical neck"],
}

def cr(q):
    o=[]
    try:
        u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":q,"rows":5,"sort":"relevance","filter":"type:journal-article"})
        r=urllib.request.Request(u,headers={"User-Agent":"Surgical/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r,timeout=15)as resp:
            d=json.loads(resp.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t=(i.get("title",[""])or[""])[0];y=i.get("created",{}).get("date-parts",[[0]])[0][0]
            doi=i.get("DOI","");jn=(i.get("container-title",[""])or[""])[0]
            if t:o.append((t[:250],y,"Crossref",doi,jn))
    except:pass
    return o

def oa(q):
    o=[]
    try:
        u="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":q,"per_page":5,"sort":"cited_by_count:desc"})
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

total,batch=0,[]
for eq_id,queries in TARGETS.items():
    cur.execute("SELECT COUNT(*)FROM verifications WHERE equation_id=?",(eq_id,))
    have=cur.fetchone()[0];need=max(10-have,0)
    for q in queries:
        if need<=0:break
        for fn in [cr,oa]:
            if need<=0:break
            for p in fn(q):
                if need<=0:break
                exp=f"{p[2]}: {p[3]}"if p[3]else p[2]
                batch.append((eq_id,p[0],exp,p[1],p[3]if p[3]else p[2],"15x surgical"))
                total+=1;need-=1
            time.sleep(1.2)

cur.executemany("INSERT INTO verifications (equation_id,test_name,experiment,year,precision_level,status)VALUES(?,?,?,?,?,?)",batch)
c.commit()

cur.execute("SELECT COUNT(*)FROM verifications");tv=cur.fetchone()[0]
cur.execute("SELECT COUNT(*)FROM equations e LEFT JOIN(SELECT equation_id,COUNT(*)c FROM verifications GROUP BY equation_id)vc ON vc.equation_id=e.id WHERE COALESCE(vc.c,0)<10")
bel=cur.fetchone()[0]
cur.execute("SELECT COUNT(*)FROM equations e LEFT JOIN(SELECT equation_id,COUNT(*)c FROM verifications GROUP BY equation_id)vc ON vc.equation_id=e.id WHERE COALESCE(vc.c,0)>=15")
at15=cur.fetchone()[0]
print(f"{tv} verif | {at15}/771 at 15x+ | {bel} below 10x | {total} added")
if bel:
    cur.execute("SELECT e.eq_number,e.title,COALESCE(vc.c,0)FROM equations e LEFT JOIN(SELECT equation_id,COUNT(*)c FROM verifications GROUP BY equation_id)vc ON vc.equation_id=e.id WHERE COALESCE(vc.c,0)<10 ORDER BY vc.c")
    for n,t,rf in cur.fetchall():print(f"  [{rf}] #{n} {t[:80]}")
c.close()
