# Locally Adaptive Contact Materials

Status: candidate research target

Safety posture: control/materials model, not a fabrication recipe

## Plain Version

Locally adaptive materials are materials whose surface, stiffness, adhesion,
shape, or damping can change in small regions fast enough to affect motion,
grip, impact survival, or routing.

The stronger target is a cooperative anisotropic material held near a controlled
critical phase boundary. "Anisotropic" means the material responds differently
along different directions. "Cooperative" means neighboring patches do not flip
independently; they bias each other into a useful local shape or grip state.

The Research Stack use is not "liquid robot magic." The grounded version is:

```text
local sensor field
  -> contact-risk estimate
  -> criticality margin check
  -> cached morphology/contact pattern
  -> charged local material-state change
  -> verified contact authority
```

For robots, especially AMEE-like or multi-limbed platforms, the speed limit is
not just maximum actuator speed. It is whether the body can keep enough
controllable contact with the environment while gravity, terrain, and impact
forces change.

## Contact Authority

Define contact authority as the controllable impulse a body can apply through a
surface patch before slipping, detaching, tipping, overheating, or damaging
itself.

```text
ContactAuthority(patch) =
  traction
  + adhesion
  + normal_force_control
  + damping_capacity
  - slip_risk
  - detachment_risk
  - heat_load
  - damage_risk
```

For variable gravity or station emergency maneuvers:

```text
g_eff = sqrt(g_local^2 + a_thrust^2 + a_rotation^2)
theta = atan2(a_lateral, g_local)
```

The material controller should care about `g_eff` and `theta`, because the
"floor" may become a wall, a slope, or a nearly useless traction surface.

## Real-World Anchor: Gecko Dry Adhesion

The closest real-world model is gecko adhesion: a hierarchical surface made of
lamellae, setae, and nanoscale spatulae that creates dry, reversible contact by
bringing many tiny tips close enough to a surface for van der Waals interaction.

What transfers into this concept:

| Gecko mechanism | Flip-tile material analogue |
|---|---|
| Many small setae/spatulae | Many small surface tiles or fibril-like microfeatures. |
| Directional attachment/detachment | Tile orientation and exposed-face control. |
| Dry reversible adhesion | Adhesive mode without wet glue or permanent bonding. |
| Hierarchical structure | Layered surface, compliance, routing, memory, and load layers. |
| Surface-area amplification | Contact authority comes from many local contacts, not one huge clamp. |

The stack should treat gecko-like adhesion as a contact primitive:

```text
GeckoContact =
  contact_area
  * tip_density
  * orientation_alignment
  * surface_conformity
  * detachability
  - contamination_penalty
  - roughness_penalty
  - wear_penalty
```

This is a strong precedent for the layered flip-tile skin because the useful
property is not simply "sticky." It is controllable adhesion: attach strongly
under the right shear/orientation and release without tearing the surface apart.

Known limits remain part of the receipt:

| Limit | Why it matters |
|---|---|
| roughness | Poor surface conformity reduces real contact area. |
| dust/contamination | Local tips can foul or lose effective contact. |
| wet chemistry | Humidity and surface chemistry can change adhesion behavior. |
| peel direction | Detachment is directional; the controller must command release paths. |
| wear/fatigue | Repeated cycling can damage microfeatures. |

Sources to preserve in future prior-art search:

- Autumn et al., 2002, direct evidence for dry gecko setae adhesion by van der
  Waals forces.
- Reviews on gecko-inspired dry adhesive materials for robotics and climbing
  robots.
- Work on substrate modulus, surface chemistry, and directional adhesion in
  gecko-inspired surfaces.

## Recovered Material Family: Structural eFuse Surfaces

The recovered session also points at a second materials family: not adaptive
skin, but self-attesting structure. The useful primitive is a load-bearing body
whose internal geometry and material state produce a measurable signal when the
body leaves its safe regime.

```text
healthy structure
  -> balanced flux / baseline RF signature / high resistance
  -> no alert
```

```text
overload, buckling, or misalignment
  -> tubule resonance shift / flux imbalance / percolation jump
  -> piezo or magnetoelectric pulse
  -> alert receipt
```

Recovered candidate pieces:

| Piece | Role |
|---|---|
| SLS resonant tubule lattice | Load-bearing void geometry that can also act as RF cavity or waveguide. |
| Conductive valence matrix | Carbon or ferrite doped print material with a strain-sensitive percolation threshold. |
| Magnetic labyrinth | Internal flux route that changes when geometry deforms. |
| Magnetoelectric laminate capsule | Converts magnetic/mechanical change into electrical signal. |
| Piezo alert layer | Audible/electrical failure receipt. |
| SDR resonant void readout | Non-contact signature for healthy vs damaged internal geometry. |

This belongs next to the adaptive contact material work because both use local
material state as a finite, receipt-bearing control surface. The difference is
that the structural eFuse is mostly passive and safety-oriented, while the
flip-tile/hair-field surface is active and locomotion-oriented.

## Fractal Extendable Hair Field

The material surface can be modeled as fractally nested extendable hairs:

```text
skin tile
  -> primary hair
  -> secondary branch
  -> tertiary microhook / spatula
```

Each hair is not a passive bristle. It is an active contact element that can
extend, bend, orient, stiffen, and retract under local field/charge control.

```text
HairState =
  {
    extension_length,
    branch_depth,
    orientation,
    stiffness,
    tip_mode,
    charge_state,
    preload,
    fatigue,
    contamination
  }
```

The point is to hook into a tensioned surface, not pierce or damage it. The
surface skin supplies preload and shear; the hairs multiply contact points and
turn local tension into controllable grip.

```text
HairContact =
  branch_depth_gain
  * extension_length
  * orientation_alignment
  * surface_tension_coupling
  * van_der_waals_contact
  * microhook_engagement
  - entanglement_risk
  - fouling_risk
  - retract_failure_risk
```

Where:

| Term | Meaning |
|---|---|
| `branch_depth_gain` | Contact multiplication from fractal branching. |
| `surface_tension_coupling` | How well the tensioned skin transfers load into the hairs. |
| `van_der_waals_contact` | Gecko-like dry adhesion at tiny tips. |
| `microhook_engagement` | Mechanical catch on roughness, fibers, pores, or engineered texture. |
| `entanglement_risk` | Hairs catch too well and fail to release. |
| `retract_failure_risk` | Hairs cannot retract cleanly under load or contamination. |

This adds a second adhesion mode:

```text
total_contact =
  gecko_like_surface_contact
  + fractal_hair_microhook_contact
```

The controller should select hair depth by environment:

| Surface | Hair policy |
|---|---|
| smooth glass / metal | shallow spatula mode; maximize van der Waals contact. |
| rough rock / fabric / regolith | deeper branch mode; allow microhook engagement. |
| dirty or dusty surface | low-depth probe first; avoid fouling the whole field. |
| emergency anchor | deep extension with high preload and explicit release plan. |
| high-speed gait | shallow directional mode; release speed matters more than max grip. |

The receipt has to include detachability. A hair field that grips but cannot
release is a trap, not a locomotion primitive.

## Scale Discipline

The practical design target should be micron-scale extension first. That keeps
the mechanism inside ordinary microstructure, surface roughness, fiber contact,
MEMS-like actuation, and dry adhesion physics instead of depending on exotic
nanoscale effects.

```text
working_scale =
  tile_mm
  -> hair_10_to_500_microns
  -> tip_0.1_to_10_microns
```

Use nanoscale only as a terminal contact refinement, not as the load-bearing
story:

| Scale | Role |
|---|---|
| millimeter tile | Addressable control patch and load routing cell. |
| 10-500 micron hair | Extendable contact element; main mechanical engagement scale. |
| 1-10 micron branch/tip | Texture matching, dry adhesion, and controlled release. |
| submicron/nano tip | Optional van der Waals boost when fabrication and wear receipts exist. |

The important claim is modest and useful:

```text
micron hairs can reach into real surface texture
without requiring weird physics
```

That gives the material a credible path for rough surfaces, fabrics, regolith,
machined metal, polymer skins, and engineered docking pads.

## Critical Phase Boundary

The material is most useful when it sits close to, but not across, a controlled
phase transition:

```text
CriticalMargin =
  abs(control_energy - transition_energy)
  / (1 + thermal_noise + damage_noise + model_uncertainty)
```

Small `CriticalMargin` means the material is easy to switch. Too small means it
may chatter, avalanche, or flip from noise. Too large means it takes too much
energy to reshape on demand.

The desired regime is a bounded near-critical window:

```text
critical_floor <= CriticalMargin <= critical_ceiling
```

The control input can be treated as a local charge/field packet:

```text
ShapeDelta =
  response_tensor
  * charge_input
  * neighbor_alignment
  * hysteresis_gate
```

Where:

| Term | Meaning |
|---|---|
| `response_tensor` | Direction-dependent material response; this is the anisotropic part. |
| `charge_input` | Electrical, magnetic, thermal, optical, pressure, or chemical control input. |
| `neighbor_alignment` | Cooperative bias from adjacent patches. |
| `hysteresis_gate` | Prevents rapid flip-flop around the phase boundary. |

This makes the material "charged to change shape" without implying free energy.
The charge reduces the switching cost because the material is already near a
permitted transition.

## Cooperative Patch Field

Each patch carries a local state:

```text
PatchState =
  {
    phase,
    orientation,
    stiffness,
    adhesion,
    damping,
    charge,
    heat,
    fatigue,
    neighbors
  }
```

Cooperation is a local alignment rule:

```text
neighbor_alignment(p) =
  weighted_sum(
    orientation_similarity,
    phase_similarity,
    shared_load_direction,
    scar_avoidance
  )
```

The useful behavior is not a global body morphing all at once. It is a wave of
small local transitions that forms a temporary foot, anchor, skid, spring,
shield, or tendon-like path.

## Layered Flip-Tile Skin

A concrete mental model is a layered flip-tile skin: many small material tiles
stacked in layers, where each tile can flip, rotate, swell, stiffen, adhere, or
change texture under local charge/field control.

This is closer to a programmable material surface than a continuous liquid
body:

```text
LayeredSkin =
  layers of tiles
  + local flip states
  + anisotropic response axes
  + neighbor coupling
  + critical-margin gates
```

Each tile has a finite state set:

```text
TileState =
  {
    orientation,
    exposed_face,
    stiffness_mode,
    adhesion_mode,
    friction_mode,
    damping_mode,
    charge_state,
    thermal_state,
    fatigue_state
  }
```

Layering matters because one tile face can optimize contact while another layer
handles load, heat spreading, or shape memory:

| Layer | Duty |
|---|---|
| surface layer | friction, adhesion, texture, local contact. |
| hair field layer | fractal extendable hairs for van der Waals contact and microhook engagement. |
| compliance layer | stiffness, damping, impact absorption. |
| routing layer | charge/field delivery and local control. |
| memory layer | hysteresis, scars, fatigue, and restored default shape. |
| structure layer | load-bearing geometry and tear limits. |

The flip-tile update is finite and auditable:

```text
next_tile_state =
  gate(
    current_state,
    local_force,
    charge_input,
    neighbor_alignment,
    critical_margin,
    heat_limit,
    fatigue_limit
  )
```

This gives the idea a buildable shape: start with a finite layered tile lattice,
not a whole-body shapeshifter. A robot foot, gripper, tire, drone landing pad,
or wall-crawling patch could use the same local state machine.

## Morphology Meme

A morphology meme is a cached local material/contact program:

```text
Meme =
  {
    shape,
    stiffness_profile,
    adhesion_profile,
    damping_profile,
    gait/contact_policy,
    trigger_conditions,
    failure_mode
  }
```

Examples:

| Meme | Use |
|---|---|
| `wide_skate` | Low-gravity traversal where friction is weak and longer contact patches matter. |
| `anchor_mesh` | Space-station thrust emergency or rotating frame where the gravity vector swings. |
| `pancake_root_lock` | High-g or impact survival; lower center of mass and maximize surface area. |
| `needle_sprint` | Low-drag ballistic phase; high damage risk, low maneuver authority. |
| `distributed_soft_foot` | Rough terrain where many small compliant contacts beat one rigid footfall. |

The "memetic" part means the controller recalls a successful shape/contact
program instead of solving the whole body from scratch every frame.

## Speed Gate

A rigid legged robot has a familiar Froude-style speed scale:

```text
v_rigid ~= k * sqrt(g_eff * leg_length)
```

A locally adaptive material changes the effective length and contact surface:

```text
leg_length -> L_shape(t, terrain, g_eff, theta)
```

The safe speed is the minimum of all active limits:

```text
V_safe =
  min(
    V_froude(g_eff, L_shape),
    V_contact(mu, adhesion, duty_factor),
    V_critical(CriticalMargin, hysteresis, avalanche_risk),
    V_morph(strain_rate, viscosity, heat),
    V_control(sensor_latency, prediction_error),
    V_damage(impact_tolerance)
  )
```

This equation prevents overclaiming. If the material can morph fast but cannot
dissipate heat, the heat term wins. If it can grip but cannot predict impact,
the control term wins.

## Adaptation Objective

Choose the morphology meme that buys the most contact authority per cost:

```text
select_meme =
  argmax_meme(
    contact_authority
    + speed_gain
    + stability_margin
    + critical_switchability
    - morph_heat
    - avalanche_risk
    - prediction_error
    - damage_risk
  )
```

This is FAMM-like behavior for bodies:

```text
successful contact pattern -> basin
failed contact pattern     -> scar
unknown contact pattern    -> quarantine / slow probe
```

## Local Adaptive Material Packet

A minimal receipt-bearing packet:

```json
{
  "patch_id": "foot:front_left:pad_03",
  "meme": "anchor_mesh",
  "phase": "near_critical_anchor",
  "hair_mode": "deep_microhook",
  "hair_branch_depth": 3,
  "critical_margin_q0_16": 18000,
  "neighbor_alignment_q0_16": 51000,
  "g_eff_q0_16": 32768,
  "theta_q0_16": 49152,
  "contact_authority_q0_16": 45500,
  "heat_load_q0_16": 9000,
  "slip_risk_q0_16": 7200,
  "damage_risk_q0_16": 3000,
  "action": "stiffen_and_adhere",
  "receipt": "sensor-window-hash + model-version + bounds"
}
```

## Promotion Rule

Promote a material-control pattern only when:

```text
ContactAuthority >= authority_floor
critical_floor <= CriticalMargin <= critical_ceiling
avalanche_risk <= avalanche_ceiling
heat_load <= heat_ceiling
damage_risk <= damage_ceiling
prediction_error <= prediction_ceiling
receipt_ok = true
```

Otherwise keep it as:

| Outcome | Meaning |
|---|---|
| `PROMOTE` | Safe enough to use as an active morphology/control prior. |
| `HOLD` | Interesting but needs more terrain or gravity cases. |
| `SCAR` | Failed under known conditions; downrank similar future attempts. |
| `QUARANTINE` | Missing receipts or unsafe extrapolation. |

## Stack Integration

| Stack surface | Role |
|---|---|
| FAMM | Store contact basins, scars, and risky terrain patterns. |
| Gecko dry adhesion | Real-world anchor for reversible van der Waals-style contact authority. |
| Fractal extendable hair field | Contact multiplier that can switch between shallow dry adhesion and deeper microhook engagement. |
| Micron-scale discipline | Keeps the main mechanism in ordinary microstructured contact instead of exotic nanoscale load-bearing claims. |
| Semantic Eigenvector Bundle | Cluster shape/material/contact memes by shared utility. |
| Mass Number | Promote only material adaptations with admissible benefit and bounded residual risk. |
| GPU + FPGA verification | GPU predicts contact fields; FPGA verifies bounds, hashes, and gate decisions. |
| Variable-gravity locomotion | Use `g_eff` and `theta` to select anchor, skate, sprint, or root-lock modes. |
| Critical-phase control | Keep patch transitions easy enough to command but far enough from noise-driven avalanche. |
| Layered flip-tile skin | Finite local tile states make the material programmable and auditable instead of vague morphing matter. |
| Application map | `AdaptiveMaterialMathApplicationMap.md` identifies DynamicCanal, COUCH, Braid Sieve, Waveprobe, MorphicDSP, PIST, Hutter, cotranslational folding, and branch-cut surfaces where the concept can pay rent. |

## Research Target

The near-term target is not a universal morphing body. It is a local adaptive
patch that can choose between a small finite set of states:

```text
soft / stiff / adhesive / damping / low-friction / high-friction / anchor
```

That is enough to make the idea pay rent. If local patches can keep contact
authority high under changing gravity and terrain, the robot gets better
locomotion without needing full liquid-metal fantasy hardware.

The longer-term target is a cooperative near-critical sheet where local patches
can be charged into shape changes on demand, but every transition still carries
a receipt for phase margin, heat, fatigue, and avalanche risk.
