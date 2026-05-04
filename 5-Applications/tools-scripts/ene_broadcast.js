import Database from "better-sqlite3";
import { join } from "path";

const dbPath = join(process.cwd(), "data", "substrate_index.db");
const db = new Database(dbPath);

// Active Peer Nodes (Tailscale IPs)
const PEERS = [
  "100.127.111.7",   // architect
  "100.111.192.47",  // judge
  "100.110.117.19",  // ip-172-31-25-81
  "100.85.1.50"      // netcup-router
];

async function broadcast(pkgName) {
  let records = [];
  if (pkgName === "ALL") {
    console.log("Gathering ALL packages for mass-sync...");
    records = db.prepare("SELECT * FROM packages").all();
  } else {
    const single = db.prepare("SELECT * FROM packages WHERE pkg = ?").get(pkgName);
    if (single) records.push(single);
  }
  
  if (records.length === 0) {
    console.error(`ERROR: No packages found to broadcast.`);
    process.exit(1);
  }

  console.log(`Broadcasting ${records.length} packages to ${PEERS.length} peers...`);

  for (const peer of PEERS) {
    try {
      console.log(` -> Pushing to ${peer}...`);
      let successCount = 0;
      for (const record of records) {
        const response = await fetch(`http://${peer}:3000/sync/ene`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(record)
        });
        const data = await response.json();
        if (data.ok) successCount++;
      }
      console.log(`    ✅ SUCCESS: ${peer} accepted ${successCount}/${records.length} records.`);
    } catch (e) {
      console.log(`    ⚠️ OFFLINE: ${peer} is unreachable.`);
    }
  }
}

const targetPkg = process.argv[2];
if (!targetPkg) {
  console.log("Usage: node ene_broadcast.js <package_name>");
  process.exit(1);
}

broadcast(targetPkg);
