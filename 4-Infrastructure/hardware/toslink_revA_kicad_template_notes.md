# TOSLINK Rev A KiCad template notes

Use `TOSLINK_EDGE_CARRIER_TEMPLATE.kicad_mod` as a *mechanical helper* footprint.

What it is for:
- board-edge reference
- connector body reference
- keepout for fiber + carrier
- support-hole placeholders
- carrier anchor-hole placeholders

What it is **not** for:
- actual electrical pin geometry of your TX/RX module

Recommended usage:
1. Import the official TOSLINK electrical footprint from the exact module datasheet.
2. Put the optical mouth flush to the board edge.
3. Add this helper footprint on top of or adjacent to the connector footprint.
4. Replace the placeholder dimensions:
   - A = support hole pitch
   - B = left/right carrier anchor pitch
   - C = edge-to-anchor center distance
   - signal pin row positions
   - body width/depth
5. Add matching features to the printed carrier:
   - hard stops for X/Y alignment
   - light flex arm for retention
   - clearance for fiber insertion
6. Keep tall parts out of the carrier zone.

Mechanical rule of thumb:
- PCB handles signals.
- Carrier handles insertion force.
- Solder joints should not be the only retention feature.
