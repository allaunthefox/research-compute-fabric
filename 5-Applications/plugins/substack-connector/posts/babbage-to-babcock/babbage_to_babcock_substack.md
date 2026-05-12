# From Babbage to Babcock
## Or: I like pipes. And cooling. And oh no.

Standard disclaimer: if you are here for the juicy math and not the rambling frog, it is at the bottom.

I do not open posts by flinging equations at your face like some kind of unhinged math flasher. The formal objects are there. They will wait. Mostly.

[IMAGE: babbage_to_babcock_header_1778019835666.png]

Quick roadmap, so you know what is ahead: I start by following a single pipe until it drags us from datacenters to boiler rooms, through a bit of Soviet hydraulic computation, and finally back to the city itself as a computational reservoir. Along the way, I argue for reading physical infrastructure as a matrix of state and failure, introduce a thing I call the **Babcock Matrix**, poke holes in surveillance tech, and suggest that the future of computation might need both **Babbage** and **Babcock** on the blueprint.

And yes, the math will finally arrive at the bottom, for the patient or insatiably curious.

But something practical is sneaking around in all this abstraction: reimagining pipes and boilers as active computational witnesses, not just background noise, could change how we detect failures, optimize resources, or even fund cities and hospitals. If we start treating infrastructure as a readable system rather than a passive utility, maintenance could shift from frantic reaction to early intervention. Waste could become opportunity. Cities might even find new ways to support the very people their networks serve.

Semantic weight.

Yes, the thesis of this work is so heavy that it requires its own cooling system.

Fortunately, this post comes equipped with a Babcock-certified semantic pipe, rated to carry the full pressure of my argument with only occasional leaks of meaning.

Please wear protective eyewear in case of a conceptual blowout.

They didn’t pay me.

Probably.

---

## **The Pipe**

One day, the coolant line decided it was done with its job description.

This is what my brain does. It sees a pipe, a valve, a pressure gauge — objects that just want to live quiet, respectable lives — and immediately starts interrogating them for hidden meaning.

Normal people see a coolant line and think:

> Excellent, the server is not on fire. Time to update my LinkedIn endorsements.

I see a coolant line and think:

> Hang on. Is this thing trying to communicate in complete sentences?

A coolant line is simple. Hot thing gets hot. Liquid carries heat away. Pump keeps things moving. Machine does not metl.

Yes, that is misspelled. No, I will not fix it. This is a pro-mistake zone.

I get a Pepsi from the fridge, and that is empirical evidence, baby. Also, this is the only post referencing taste with half the calories and twice the existential dread.

That should have been the whole story.

Unfortunately, I kept looking at it.

And then the pipe became a sentence.

Not metaphorically.

A computational sentence.

Quick aside: did you know computers use terms like **WORD**? I didn’t until recently. Now I’m out here muttering, “Subdivide the rational fraction via WORD addresses,” like I’m auditioning for a role in a very niche cyberpunk musical.

But structurally, a pipe has direction. It has resistance, pressure, state, and failure modes. It participates in a graph. It knows, in the brutal language of physics, whether the system it belongs to is still balancing.

And taxes.

Always taxes.

The IRS is the only true invariant.

Then the annoying thought arrived, as they do, at exactly the wrong moment:

> What if the cooling system is not just removing the consequences of computation? What if it is already doing a second kind of computation underneath it?

By that, I mean: what if the physical processes inside the cooling system — the flows, pressures, temperatures, delays, and dynamics — are themselves a form of computation, distinct from the abstract symbolic calculations happening in the server?

What if the infrastructure does math with physics, not just silicon?

Fantastic.

Thank you, brain, for this unsolicited TED Talk.

That is where this post begins.

Not with an answer.

With a pipe that would not stay quiet.

No, not the pipe you see your very angry bookie carrying.

Stay in your lane. Come on.

---

## **The Babbage Part**

Babbage is the comfortable origin story.

But only if you were not born in the late 1890s and forced to read the schematics. Those poor, poor engineers.

Computation as machinery.

Gears. Tables. Mechanical logic.

Numbers go in. Operations happen. Numbers come out.

REALLY loud.

Seriously, think NASCAR if the car were made of hammers and nobody had invented OSHA yet.

This is the lineage we know how to talk about.

It eventually leads to silicon, chips, GPUs, datacenters, and all the glowing machinery we now treat as weightless, mostly because the hard parts are tucked behind dashboards nobody actually looks at until something is on fire.

Or, you know, Pornhub.

But computation is not weightless.

Every bit flip has a cost. Every accelerator cluster is basically a Ferrari engine for Nvidia boxes. This is also a very expensive way of converting electricity into heat and then pretending that was not the point.

That heat does not disappear because the model got smarter.

It has to go somewhere.

Air. Water. Refrigerant. Coolant. Pumps. Valves. Heat exchangers. All the unglamorous plumbing that keeps the symbolic machine from becoming an accidental furnace.

We built a multibillion-dollar industry and bolted a boiler room underneath it.

Babbage gives us the symbolic engine.

But the datacenter also needs Babcock.

---

## **The Babcock Part**

I am using **Babcock** less as a single historical figure and more as an industrial ghost haunting the boiler room of modernity.

Babcock means boilers.

Pressure vessels. Tubes. Heat. Containment. Failure modes with consequences.

A boiler is not a symbol machine.

A boiler is a pressure argument with consequences, and the consequences are usually loud, wet, and involve someone yelling about insurance.

Babbage calculates.

Babcock remembers the calculation must be paid for in heat.

And beneath both of them are the plumbers.

The quiet priesthood of pressure, drainage, valves, traps, vents, seals, slopes, gauges, and emergency shutoffs.

The people who already knew what this entire essay is just now rediscovering:

> No system is real until it can move heat, move water, survive failure, and be repaired by someone who owns at least three wrenches and a deep, existential grudge against leaks.

So yes, this is a post about computation.

But it is also a thank-you note to every plumber, pipefitter, steamfitter, maintenance tech, facilities engineer, and night-shift person who kept the substrate alive while the rest of us argued about the symbols on top of it and pretended the pipes would just fix themselves if we used enough Greek letters.

Once I saw that split, liquid cooling started looking different.

A coolant loop is not decorative infrastructure. It is a mandatory thermodynamic coupling layer. If it gets ignored, blocked, misread, or decoupled, the machine enters a throttling, shutdown, or damage state.

The computer cannot opt out of its cooling system.

So why are we treating the cooling system like passive plumbing, as if it is just there for the vibes?

I will be honest: this question annoyed me more than it should have. It felt like watching someone run a very expensive calculation and then throw away half the output because it came out as heat instead of numbers.

---

## **The Bad Idea, Which Is Not Actually the Bad Idea**

Here is the version that sounds bad:

> With mild changes, coolant lines can become data lines.

That framing is wrong.

It makes people imagine Ethernet in a pipe. Tiny packets with headers paddling through a rack like very determined boats.

That is not it.

Please do not build that.

The better idea is somehow both stranger and more boring, which is my favorite genre:

> The coolant loop is already a physically coupled state system. You can read it as one.

For example: sensors track temperature and pressure at different points in the loop. If the temperature spikes at the server intake but drops at the coolant return, and at the same time flow from the pump shows a subtle decline, you can infer that a blockage has started forming.

Even before an alarm goes off, the combined state of temperature, flow, and pressure across the topology creates a signature you can read.

This is not just monitoring for emergencies. It is recognizing that the ever-changing state of the coolant loop already encodes meaningful information about the whole system, if you watch it like a language instead of just plumbing.

Pressure, flow, temperature, valve position, pump speed, branch impedance, vibration, thermal delay, failure signatures — all of that is already part of the loop’s state.

The coolant system is already doing work.

The question is whether some of that unavoidable thermodynamic work can also carry useful structure.

Not:

> Can a pipe send data?

Rather:

> If a pipe must already carry the consequences of computation, can we use that mandatory coupling as a computational witness?

That is the moment it stopped being a gimmick and started being the kind of idea that ruins your ability to enjoy normal plumbing ever again.

---

## **The Old Water Computer Is Hiding in the Wall**

This is not completely without ancestors, which I find reassuring. It is nice to know someone was already doing a version of the thing before I had the annoying thought.

Vladimir Lukyanov built a hydraulic analog computer in the 1930s: the Soviet water integrator. It solved differential equations using water level, flow, and resistance.

Not metaphorically.

The water did the math because the system was arranged so that its behavior matched the equation.

A water computer.

In the Soviet Union.

In the 1930s.

And we, as a species, sort of just left it in the historical lost-and-found.

That matters. It reminds me that computation has never belonged only to electronics.

Sometimes computation is a gear.

Sometimes it is voltage.

Sometimes light gets trapped in a cavity and starts a new religion.

Sometimes water is just looking for a level.

And sometimes, apparently, a Soviet plumbing installation should have had a much better museum tour.

I am not proposing we rebuild Lukyanov’s machine.

I am saying we already built enormous fluid systems around the machines and cities we depend on.

We just have not been reading them correctly.

---

## **The Reservoir Trick**

The idea I actually care about comes from **reservoir computing**.

In reservoir computing, you do not train the whole physical system. You drive the system, let its internal dynamics transform the input, and train only a readout layer.

You are not programming the reservoir.

You are listening to it.

Photonic reservoir computing is the version that breaks my brain.

Not because photons are magic.

Because the posture is different.

It says:

> Let physics do part of the transformation.

That sentence is dangerous to me specifically. I want to put it on a wall.

Because once you accept it, you start seeing reservoirs everywhere, which makes normal conversations very difficult and plumbing supply stores extremely philosophical.

Or great, if you find the right crowd.

I do not go out much.

A coolant manifold is a reservoir.

A pressure zone is a reservoir.

A city water network is a reservoir.

A road network under load is a reservoir.

A bridge vibrating in weather and traffic is a reservoir.

Not all of them are useful.

Not all are readable.

Not all should be touched.

But the category opens, and once it opens, it stays open.

The question becomes:

> Which physical systems are already being forced, measured, constrained, and stabilized?

Those are candidate substrates.

I have started seeing them on the way to the grocery store.

This is fine.

Everything is fine.

The produce section is now a topology problem.

---

## **The View from the Moon**

Before we zoom back in, let me zoom all the way out.

Because there is one more reservoir, and it is the biggest one.

The largest computational device on Earth is the weather system.

Nobody built it. Nobody programmed it. It has been running for four billion years without a budget meeting, a steering committee, a single line of code, a Zoom call, or a directive from middle management insisting we recompile the physics paradigm before the Q3 deadline.

The input signal is solar radiation.

The input translators are Earth’s rotation, ocean heat capacity, atmospheric composition, terrain, ice albedo, and about forty other things we are still arguing about.

The reservoir dynamics are everything meteorology has ever tried to describe.

The readout layer is what we call a weather forecast.

We did not design this substrate. We just eventually got good enough instruments to start reading it.

Now, here is the thing that made me sit down, stare into the existential void, and reconsider my relationship with weather apps:

> The weather system is not separate from the city substrate argument. It is the top layer.

The city sits inside the weather system.

The water network is fed by it.

The steam tunnels are responding to it.

The roads deform under it.

The demand waves in a city’s water grid are partially weather-driven.

The hospital steam load spikes with it.

The whole stack looks like this:

```
weather system
  ← largest physical reservoir, solar-forced
        ↓
city water / steam network
  ← civilization-scale reservoir, demand-forced
        ↓
hospital steam loop
  ← campus-scale reservoir, load-forced
        ↓
datacenter coolant loop
  ← machine-scale reservoir, compute-forced
```

Same architecture at every level.

Different scale.

No CPU anywhere in the stack, unless you count the one running the PowerPoint explaining why the pipes are over budget. And Anne from accounting is now a pie chart showing that they stole your pie from the fridge.

This is what I mean when I say:

> All is computation if you have the correct input translator.

Physics does not need to be told to compute.

It already is.

The question is only whether we have built the readout layer yet.

The weather system has one, imperfect and still improving.

The city does not yet.

That is the gap.

That is the whole post.

You can stop reading now, but I know you won’t.

---

## **SCADA Was Already There**

This is where it becomes less science fiction, which is a relief, because at this point I was starting to wonder if I needed to submit myself for peer review or just a wellness check.

Modern infrastructure already has control systems.

Pumps report status. Valves expose position. Tanks expose levels. Pressure zones have readings. Alarms fire. Operators intervene. Setpoints change.

The flow is already controlled.

The data already exists.

Which means the first step is not to install a surveillance mesh over a city, build anything new, write a grant proposal, or convince anyone that water computers are cool again.

The first step is to place the existing inputs and outputs in the topologies to which they belong.

That is the object I am calling the **Babcock Matrix**.

In plain English:

> The Babcock Matrix is a map of all the moving parts, measurements, and flow states in a physical infrastructure system, organized so you can see how everything is connected and how the system changes over time.

More formally, a Babcock Matrix is the graph-aligned state of a mandatory flow or thermodynamic system.

Nodes are pumps, valves, tanks, reservoirs, cold plates, junctions, and pressure zones.

Edges are pipes, mains, tunnels, coolant lines, bypasses, and returns.

The state is pressure, flow, temperature, level, actuator position, and alarm condition.

The matrix is not just numbers.

The matrix is a set of numbers placed back onto the body from which they came.

I do not know yet if this is a useful object.

I think it is.

I am writing it down because that is how I find out.

If you have seen this object before under a different name, please tell me immediately so I can cite you and feel less like I invented something weird in my bathroom at 2 a.m. with a wrench and a spreadsheet.

---

## **The Substrate Inversion**

People will say:

> But that is not really computation.

What they usually mean is:

> That is not the kind of computation I already recognize, and recognizing things is how I know they are real.

I do not think substrate has to mean silicon.

A substrate is any lawful physical medium whose state transitions can be constrained, observed, and made useful.

Silicon is a substrate because charge can be disciplined into logic.

Optics is a substrate because photons can be guided, delayed, interfered with, and read.

Hydraulics is a substrate because pressure, flow, resistance, storage, and delay evolve under constraints.

A road can be a substrate.

A bridge.

A pipe.

Not because they are secretly laptops — they are not, do not email me — but because they are physical systems with state, topology, forcing, memory, residuals, and possible readouts.

The city does not fail to compute because it lacks GPUs.

It computes differently, because its substrate is water, gravity, pressure, demand, delay, friction, strain, and weather constraint becoming legible.

---

## **Failure as a Math Error**

This is the piece that made the whole thing click for me.

I was so pleased about it that I told someone at dinner.

They were not as pleased.

But I think they were wrong, and also possibly regretting their RSVP.

A pipe rupture does not need to be recognized as a rupture first.

In a topological flow matrix, it shows up first as a conservation failure.

Water enters a subgraph.

Water exits a subgraph.

Some is stored.

If those quantities stop balancing beyond tolerance, the graph is telling you something has changed.

The pipe does not need to announce that it broke.

The graph fails to close.

A hidden outlet appears.

Flow disappears into an unmodeled sink.

The alarm is secondary.

The first event is a math error.

That is the kind of infrastructure I want.

Not infrastructure that waits to be visibly broken and then sends someone a ticket.

Infrastructure whose equations fail so loudly that even the coffee machine knows it is time to call maintenance.

---

## **A Road That Screams**

Once you see this, it jumps to another domain.

And then it just keeps jumping, which is a problem I apparently cannot stop having.

A road is a material graph under load, weather, vibration, moisture, drainage, traffic, thermal cycling, and time.

If you have a topological equation for the road, maintenance changes category.

You are not just patching holes after they appear.

You are building a road that screams for repair.

The scream is not mystical.

It is mathematical.

A road segment has an expected vibration signature. It drains a certain way. It deforms within a certain envelope. It responds to temperature and load within bounds.

When that stops being true, the road has already reported its wound.

[IMAGE: screaming_infrastructure_topology_1778019886128.png]

The pothole is only the late-stage user interface.

I love that sentence.

I think about it more than is reasonable, which is probably why I am not invited to more parties.

> The pothole is the late-stage user interface of a failed topology.

---

## **Not the Surveillance City**

This is also why I am not describing the usual IoT answer.

The IoT answer and I have a complicated relationship.

A lot of smart-city thinking is surveillance with better branding.

More cameras. More phone tracking. More license plate readers. More household inference. More private behavior turned into someone else’s data exhaust. More dashboards that imply that if you just knew more things about more people, the city would somehow fix itself.

It would not.

And that is not what I am describing.

The city does not need to watch its citizens to know where it is breaking.

A pipe does not need to identify a household to know conservation no longer closes.

A bridge does not need to identify pedestrians to know its vibration modes are drifting.

A road does not need to identify a driver to know its surface is failing.

The point is **asset-state minimalism**:

> Read the physical variables required to determine whether the asset remains inside its lawful envelope.

Ignore identity.

Avoid behavioral inference.

Keep the readout local where possible.

Let the infrastructure diagnose itself.

Not the people inside it.

I think this is a more useful thing to build.

It is also less fun for the camera companies, which is probably why it is not the default.

And why I am not on their holiday card list.

---

## **The Hospitals Are Already Doing It. They Just Do Not Know Yet.**

Here is the one that keeps me up at night.

Across America, hospitals run steam distribution systems.

They have for over a century.

Steam for sterilization, heating, humidification, pressure systems, and surgical suites.

Big installations.

Heavily instrumented.

Already monitored.

Already controlled.

Already producing a thermodynamic state continuously, around the clock, whether anyone is paying attention to it as a substrate or not.

These are not edge cases.

These are major urban hospitals. Academic medical centers. Regional health systems.

The steam channels are there.

The pressure differentials are there.

The flow state is there.

The thermodynamic potential is just sitting in the pipes, doing its job, going unread as anything except:

> The steam is fine.

Now here is the part that got me, and also made me question whether I should be allowed near hospital basements unsupervised:

> You would not need to modify the hardware. Not a single valve. Not a single sensor.

The instrumentation already exists.

You would need a software update and a readout layer.

That is it.

You would be reading something that is already happening, not building something new.

Which means the barrier to entry is not steel and civil engineering.

It is attention.

And possibly a willingness to annoy your facilities manager with philosophical questions about steam.

Here is where it becomes less abstract and more uncomfortable:

Many people in America use the emergency room for basic care because they cannot afford anything else. They go in. They get treated. They skip the bill. Not because they are irresponsible, but because the math does not work, and the bill would break them anyway.

The system is also broken.

The ER absorbs the loss.

The hospital absorbs the loss.

Everyone pretends this is not a structural problem, then argues about it every few years without fixing anything.

But if a hospital could rent out thermodynamic reservoir capacity from its existing steam infrastructure to a startup that needs cheap reservoir compute, to a research group, or to whoever else could use lawful physical dynamics as a substrate, that revenue would not have to go to shareholders.

It could go to a gap fund.

A sliding scale.

A no-bill threshold for people who cannot pay.

This is not entirely unprecedented. Utilities sometimes lease excess capacity on power or fiber lines. District heating networks have experimented with selling spare thermal energy to nearby buildings or datacenters. In the financial world, capacity markets let power generators profit from reliability assets they are already maintaining. Even excess hospital parking lots are occasionally rented out to outside organizations.

These models show that infrastructure resource-sharing exists as a practical path, even if thermodynamic reservoir leasing would come with its own regulatory and operational headaches.

No new infrastructure.

No surveillance.

No identifying anyone.

Just:

> The steam is already doing thermodynamic work. We can read that work. Someone may pay to use it. That payment can help keep the person who came in with a broken arm at 2 a.m. from leaving with a $4,000 bill they will spend three years ignoring.

I am not saying this is easy.

I am not saying the regulatory path is obvious.

I am not saying hospitals would just do this voluntarily, unless someone invents a TikTok challenge for it.

I am saying the physical argument closes.

The substrate is there.

The instrumentation is there.

The need is there.

The only thing missing is treating the pipe as something more than a pipe.

---

## **City as Substrate**

The hospital is the intimate version of the argument.

One campus.

One steam loop.

One institution whose thermodynamic waste could become its own operating margin.

Now scale it up.

Imagine New York.

Not as a skyline.

As a hydraulic organism.

The world’s most caffeinated amoeba.

Reservoirs. Aqueducts. Tunnels. Mains. Valves. Towers. Pumps. Pressure zones. Demand waves. Stormwater. Wastewater. Heat. Weather. Gravity.

Millions of people are participating in aggregate flows without needing to be individually identified, surveilled, tagged, or logged into a dashboard.

That system is already in motion.

Already forced.

Already controlled.

Already producing state.

A datacenter spends electricity to create artificial state transitions in silicon.

A city water network undergoes enormous state transitions because civilization requires it, and civilization does not care whether you have the budget for it.

I am not saying New York’s plumbing is a GPU cluster.

That framing smuggles in the wrong definition of substrate and would also be a very strange pitch to the city council.

I am saying New York’s plumbing is a civilization-scale physical reservoir whose dynamics can be made legible.

The city is already running the simulation in matter.

SCADA is the passive sensorium.

The Babcock Matrix is the state representation.

The readout is where computation becomes visible.

The city is doing the work.

We are just not watching the right output, probably because we are too busy arguing about zoning or inventing new ways to spell infrastructure.

---

## **Homeostatic Homology**

Once you lift the system into topology, you can ask a different kind of question.

Not just:

> Where are the pipes?

But:

> Which parts of the system perform the same stability function?

A tank, a reservoir, a pressure-regulated district, and a coolant buffer look physically different.

But under perturbation, they may play related roles.

They buffer shock.

They restore gradients.

They preserve pressure.

They maintain thermal viability.

They keep the larger system from leaving its safe envelope.

That is what I mean by **homeostatic homology**:

> A recurring equivalence between parts of a controlled physical network that perform the same stability-preserving role.

A city is full of these.

A datacenter is full of these.

A body is full of these.

Here is where I have to physically stop myself, because my brain immediately tries to jump from pipes to biology to compression to formal verification to governance to whether frogs have homeostatic homology and how many ponds that would require, and whether n is large enough, and whether the frogs have unionized.

So I will keep the claim small:

> If infrastructure can be represented as a topological state matrix, we can classify its substructures by how they preserve homeostasis under stress.

That is enough.

That is already a lot.

I will go lie down and try not to think about pipes for at least five minutes.

---

## **The Map**

This all started as a weird sentence:

> Coolant lines can become data lines.

But that sentence was only the door.

Behind it:

```
flow control already exists
        ↓
SCADA provides passive state
        ↓
state belongs on topology
        ↓
topology becomes matrix
        ↓
matrix exposes residuals
        ↓
residuals expose failure
        ↓
failure becomes legible before collapse
```

That is the thing I am trying to name, mostly so I can stop yelling about it at dinner.

Not surveillance.

Not magical pipes.

Not replacing GPUs with plumbing.

Not tiny packets on boats.

A substrate inversion.

A way to treat mandatory physical infrastructure as a lawful computational witness.

Babbage gave us the symbolic engine.

Babcock gives us the pressure vessel.

The future city may need both:

> logic above, thermodynamic witness below.

And somewhere between them:

> a pipe that would not stay quiet.

I do not know if the Babcock Matrix is the right object.

I think it is.

If you see a hole in it, or you have seen this exact idea somewhere else and I just did not find it yet, tell me.

That is literally why I am writing this.

I would rather be corrected than comfortable, even if it means admitting I fell in love with a matrix at dinner.

If you have related work, critiques, other examples, or practical implementation stories — especially ones that either strengthen or undermine what I am proposing — please send them my way.

Collaboration, sharp skepticism, and cross-pollination are more than welcome.

If you know a better framework, I want to know.

If you want to build something or test an idea in the wild, reach out.

The best part of working in public is seeing what happens when thoughts collide.

---

# **Appendix: The Math, for People Who Want It**

## **1. Infrastructure Graph**
Let the physical infrastructure be represented as a graph: $G = (V, E)$.

## **2. Local State Vector**
Each node or edge carries a state vector: $s_i(t) = [P_i(t), Q_i(t), T_i(t), L_i(t), A_i(t), \Delta P_i(t), R_i(t), \alpha_i(t)]$.

## **3. The Babcock Matrix**
The Babcock Matrix is the graph-aligned state matrix: $\mathfrak{B}_t = (G, A_G, W_G, \mathcal{B}_t)$.

## **4. Flow-Control Dynamics**
Infrastructure evolution: $\mathcal{B}_{t+1} = F(\mathcal{B}_t, u_t, d_t, W_G) + \eta_t$.

## **5. Reservoir Readout**
Readout layer: $y_t = R_\theta(\mathcal{B}_t, G, W_G)$.

## **6. Conservation Residual**
$r_S(t) = \sum Q_{in} - \sum Q_{out} - \Delta S(t)$. Failure occurs when $|r_S(t)| > \epsilon_S$.

## **7. Rupture as Hidden Boundary**
The graph fails to balance before the alarm fires.

## **8. Homeostatic Objective**
The cost function $H(\mathfrak{B}_t)$ representing the deviation from the viable envelope.

## **9. Homeostatic Homology**
Equivalence between stability-preserving structures.

## **10. Screaming Infrastructure Residual**
$\rho_t = \|\mathcal{L}(X_t, G)\|$. The pothole is the late-stage UI of a failed topology.

## **11. Privacy-Preserving Readout Constraint**
$\frac{\partial Y_t}{\partial P_t^{\text{personal}}} = 0$.

## **12. Hospital Steam Loop**
Ethical value chain: thermodynamic residual value $\rightarrow$ hospital operating relief $\rightarrow$ care capacity.
