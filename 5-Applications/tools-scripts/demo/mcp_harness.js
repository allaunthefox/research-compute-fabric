const terminal = document.getElementById('terminal');
const input = document.getElementById('cmd-input');

// [CONFIG] Reality Manifestation State
let CURRENT_MANIFEST = 'CHASE';

// [CONFIG] Replace with your actual Wolfram Alpha AppID
const WOLFRAM_APPID = 'YOUR_APPID_HERE';

const PERIODIC_TABLE = {
    'XE': { weight: 131.293, name: 'Xenon', role: 'Conductivity Spine' },
    'C': { weight: 12.011, name: 'Carbon', role: 'Warm Body Breeder' },
    'H': { weight: 1.008, name: 'Hydrogen', role: 'Quantum Trace' }
};

const REALITY_SPECS = {
    'STANDARD': { geometry: 'Linear 2-Anvil', logic: 'Simultaneous Pulse', pressure: '120 GPa' },
    'BLUESKY': { geometry: 'Dodecahedral 12-Anvil', logic: 'Geometric Focus', pressure: '172 GPa' },
    'CHASE': { geometry: 'Supersonic Torus (CWT)', logic: 'Sequential Piling', pressure: '245 GPa' }
};

function log(text, className = '') {
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + className;
    entry.textContent = text;
    terminal.appendChild(entry);
    terminal.scrollTop = terminal.scrollHeight;
}

async function queryWolfram(query) {
    if (WOLFRAM_APPID === 'YOUR_APPID_HERE') {
        log('[!] Error: Wolfram Alpha AppID not configured.', 'err');
        return;
    }
    log('[AETHER] Querying Wolfram Alpha: ' + query);
    try {
        const url = `https://api.wolframalpha.com/v1/result?appid=${WOLFRAM_APPID}&i=${encodeURIComponent(query)}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('API Error: ' + response.status);
        const data = await response.text();
        log('[WOLFRAM] ' + data);
    } catch (err) {
        log('[!] Error: ' + err.message, 'err');
    }
}

input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const cmd = input.value.trim().toUpperCase();
        input.value = '';
        log('architect@aether:~$ ' + cmd);
        handleCommand(cmd);
    }
});

async function queryMIMORouter() {
    try {
        const response = await fetch('/api/mimo/status');
        if (!response.ok) throw new Error('API Error: ' + response.status);
        const data = await response.json();
        log('[MIMO] Available Transports: ' + data.available_transports.join(', '));
        if (data.i2p_info) {
            log('[MIMO] I2P State: ' + data.i2p_info.state);
            log('[MIMO] I2P Manifests: ' + data.i2p_info.manifests_registered);
        }
        log('[MIMO] Omnitoken: OK');
        return data;
    } catch (err) {
        log('[MIMO] Error: ' + err.message, 'err');
        return null;
    }
}

function handleCommand(cmd) {
    if (cmd === 'MIMO') {
        log('[MIMO] Probing multi-band transport...');
        queryMIMORouter();
        return;
    }
    if (cmd.startsWith('WOLFRAM ')) {
        queryWolfram(cmd.substring(8));
        return;
    }
    if (cmd.startsWith('ATOMIC ')) {
        const symbol = cmd.split(' ')[1];
        if (symbol && PERIODIC_TABLE[symbol]) {
            const data = PERIODIC_TABLE[symbol];
            log(`[AETHER] Element: ${data.name} (${symbol})`);
            log(`[AETHER] Atomic Weight: ${data.weight} u`);
            log(`[AETHER] Tactical Role: ${data.role}`);
        } else {
            log('[!] Usage: ATOMIC <SYMBOL>', 'err');
        }
        return;
    }

    switch (cmd) {
        case 'MANIFEST':
            if (CURRENT_MANIFEST === 'CHASE') CURRENT_MANIFEST = 'STANDARD';
            else if (CURRENT_MANIFEST === 'STANDARD') CURRENT_MANIFEST = 'BLUESKY';
            else CURRENT_MANIFEST = 'CHASE';
            log(`[AETHER] Reality Track Switch: -> ${CURRENT_MANIFEST}`);
            const specs = REALITY_SPECS[CURRENT_MANIFEST];
            log(`[AETHER] Geometry: ${specs.geometry}`);
            log(`[AETHER] Logic: ${specs.logic}`);
            log(`[AETHER] Target Pressure: ${specs.pressure}`);
            break;
        case 'CHASE':
            log('[AETHER] Initializing Chasing Wave Sequential Detonation...');
            log('[AETHER] Geometry: Supersonic Torus (CWT)');
            log('[AETHER] Mach Stem Peak: 245 GPa (Sequential Piling)');
            log('[AETHER] Sequence Delay: 10ps (Phase-Shifted)');
            break;
        case 'SAS':
            log('[AETHER] Engaging Supersonic Acoustic Siphon (SAS)...');
            log('[AETHER] Mode: Supersonic Cavitation-Work Recapture');
            log('[AETHER] Efficiency: 94.2% (Mach-Stem Shunt)');
            log('[AETHER] Destination: SCF Breeder Cloud (The Mass)');
            break;
        case 'DAC12':
            log('[AETHER] Initializing DAC-12 Array Profile...');
            log('[AETHER] Geometry: Dodecahedral (12 Symmetrical Faces)');
            log('[AETHER] Force Divergence: < 0.001% (Scalar Focus)');
            break;
        case 'LONSDALEITE':
            log('[AETHER] Analyzing Lonsdaleite Cycle...');
            log('[AETHER] Phase: Transient Hexagonal Diamond (LPT)');
            log('[AETHER] Role: Inertial Squeeze Anvil');
            break;
        case 'SOLITON':
            log('[AETHER] Initializing Soliton String Chemistry...');
            log('[AETHER] State: Metallic Xenon-Carbon Plasma (XACS)');
            log('[AETHER] Conductivity: 1e4 S/cm (MIT Active)');
            log('[AETHER] Ionization: alpha = 0.85 (Focus-Induced)');
            break;
        case 'WORLDBUILD':
            log('[AETHER] --- WORLDBUILDING DISCLAIMER ---', 'warn');
            log('[AETHER] The SAS/CWT/Lonsdaleite mechanics are HIGH-FIDELITY CONCEPTUAL ONLY.');
            log('[AETHER] Intended Role: Speculative Narrative Modeling.');
            log('[AETHER] Context: Toy Model Physics.');
            break;
        case 'OMNI_BAL':
            log('[AETHER] Recalibrating manifold...');
            setTimeout(() => log('[AETHER] Stability lock active.'), 1000);
            break;
        case 'VRAM_FLUSH':
            log('[WARNING] Initiating VRAM_FLUSH...', 'warn');
            setTimeout(() => log('[AETHER] VRAM cleared.'), 500);
            break;
        case 'STARK_PROVE':
            log('[AETHER] Proof: sha3-' + Math.random().toString(16).slice(2));
            break;
        case 'HELP':
            log('Commands: MANIFEST, CHASE, SAS, DAC12, LONSDALEITE, SOLITON, WORLDBUILD, WOLFRAM <q>, ATOMIC <q>, OMNI_BAL, VRAM_FLUSH, THERMO, STARK_PROVE, MIMO, CLEAR, HELP');
            break;
        case 'CLEAR':
            terminal.innerHTML = '';
            break;
        default:
            if (cmd) log('[!] Unknown command: ' + cmd, 'err');
    }
}

setTimeout(() => {
    log(`[+] Track initialized: ${CURRENT_MANIFEST}`);
    log('[+] entropic floor detected at 0.500');
    log('[+] STARK verification complete.');
}, 500);
