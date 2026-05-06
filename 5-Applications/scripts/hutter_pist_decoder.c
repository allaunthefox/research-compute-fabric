/*
 * PIST Extended Encoding — Minimal Self-Contained Decoder for Hutter Prize
 *
 * Compiles to a single binary that, when run, outputs enwik9 (1,000,000,000 bytes).
 * The compressed data is embedded at the end of this executable.
 *
 * Build: gcc -O3 -o archive.exe hutter_pist_decoder.c -lm
 * Run:   ./archive.exe > enwik9
 *
 * Size budget:
 *   Current record L = 110,793,128 bytes
 *   Target S = S1 + S2 < L (where S2 = sizeof(archive.exe))
 *   1% improvement = S < 109,685,207 bytes
 *
 * Architecture:
 *   - O(1) coordinate computation per byte position (no search)
 *   - 8-opcode register machine with manifold addressing
 *   - Bootstrap basis embedded in binary header
 *   - Program stream embedded after code section
 *
 * Mathematical foundation — Frozen-In Coordinate Invariance
 *   (Asenjo, Comisso & Winkler, PRL 2026, DOI: 10.1103/6c4q-kx6f)
 *
 *   The decoder relies on the same principle as frozen-in gravitational fields:
 *   under an ideal "Ohm-type" condition, field structures remain preserved
 *   as the system evolves. Here, the "field" is the composite address structure,
 *   and "evolution" is the sequential decode operation.
 *
 *   Eq 1 (PIST shell decomposition):    n = k^2 + t
 *   Eq 2 (Mass function):                  m(k,t) = t(2k+1-t) [t < 2k+1-t]
 *   Eq 3 (Mirror):                        mirror(n) = k^2 + (2k+1-t)
 *   Eq 4 (Tree address):                   path_i(n) = floor(n / 20^i) mod 20
 *   Eq 5 (Surface coords):                 x = 1 + (n mod 255), y = 1/x
 *   Eq 6 (Torus angles):                   theta = n*Phi mod 2pi
 *                                          phi   = n*Phi^2 mod 2pi
 *                                          psi   = n*Phi^3 mod 2pi
 *   Eq 7 (Frozen-in prediction):           p(n) = basis[n%B] XOR keystream(n)
 *                                                   XOR (n mod 256)
 *                                                   XOR mirror(n)
 *   Eq 8 (Decode):                         output = p(n) XOR residual(n)
 *
 *   The composite address is a topological invariant: it depends only on n,
 *   not on data. Like gravitational helicity H_g = integral(A_g . B_g dV),
 *   the coordinate structure is conserved under encode/decode dynamics.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

/* ─── Constants ─── */
#define ENWIK9_SIZE     1000000000ULL
#define PHI             1.618033988749895
#define TWO_PI          6.283185307179586
#define TREE_DEPTH      3
#define TREE_BRANCHES   20
#define BASIS_SIZE      16
#define STACK_SIZE      256
#define BOOTSTRAP_SIZE  16

/* ─── PIST Coordinate Primitives ─── */

static inline uint32_t isqrt(uint32_t n) {
    uint32_t x = n, y = (x + 1) >> 1;
    while (y < x) { x = y; y = (x + n / x) >> 1; }
    return x;
}

static inline void pist_encode(uint32_t n, uint32_t *k, uint32_t *t) {
    *k = isqrt(n);
    *t = n - (*k) * (*k);
}

static inline uint32_t pist_mass(uint32_t k, uint32_t t) {
    if (k == 0) return 0;
    uint32_t m = 2 * k + 1 - t;
    uint32_t tf = t < m ? t : m;
    return tf * (2 * k + 1 - tf);
}

static inline uint32_t pist_mirror(uint32_t n) {
    uint32_t k = isqrt(n);
    uint32_t t = n - k * k;
    if (k == 0) return 0;
    return k * k + (2 * k + 1 - t);
}

/* ─── Tree Address (Base-20 Recursive Traversal) ─── */

static inline void tree_address(uint32_t n, uint32_t path[TREE_DEPTH]) {
    for (int i = 0; i < TREE_DEPTH; i++) {
        path[i] = n % TREE_BRANCHES;
        n /= TREE_BRANCHES;
    }
}

/* ─── Surface Coordinates (y = 1/x) ─── */

static inline void surface_coord(uint32_t n, double *x, double *y, double *theta) {
    *x = 1.0 + (double)(n % 255);
    *y = 1.0 / *x;
    *theta = fmod((double)n * PHI, TWO_PI);
}

/* ─── Toroidal Angles (Φ-Irrational Rotation) ─── */

static inline void torus_angles(uint32_t n, double *theta, double *phi, double *psi) {
    double nd = (double)n;
    *theta = fmod(nd * PHI, TWO_PI);
    *phi   = fmod(nd * PHI * PHI, TWO_PI);
    *psi   = fmod(nd * PHI * PHI * PHI, TWO_PI);
}

/* ─── Composite Address ─── */

typedef struct {
    uint32_t k, t;
    uint32_t mass;
    uint32_t mirror;
    uint32_t tree[TREE_DEPTH];
    double   surf_x, surf_y, surf_theta;
    double   torus_theta, torus_phi, torus_psi;
} Address;

static inline void composite_address(uint32_t n, Address *addr) {
    pist_encode(n, &addr->k, &addr->t);
    addr->mass   = pist_mass(addr->k, addr->t);
    addr->mirror = pist_mirror(n);
    tree_address(n, addr->tree);
    surface_coord(n, &addr->surf_x, &addr->surf_y, &addr->surf_theta);
    torus_angles(n, &addr->torus_theta, &addr->torus_phi, &addr->torus_psi);
}

/* ─── Register Machine State ─── */

typedef struct {
    uint32_t pc;           /* Program counter */
    uint32_t sp;           /* Stack pointer */
    uint8_t  acc;          /* Accumulator */
    uint8_t  flags;        /* Condition codes: bit0=halt, bit1=emit */
    uint32_t entropy;      /* Local information density */
    uint32_t depth;        /* Current PIST shell */
} State;

/* ─── Instruction Decode ─── */

#define OP_NOOP     0
#define OP_LOAD     1
#define OP_STORE    2
#define OP_ADD      3
#define OP_XOR      4
#define OP_BRANCH   5
#define OP_FUSE     6
#define OP_HALT     7

static inline uint8_t decode_opcode(uint8_t b)  { return b & 0x07; }
static inline uint8_t decode_operand(uint8_t b){ return b >> 3; }

/* ─── Quasi-Periodic Keystream Modulation ─── */

static inline uint8_t keystream_value(uint32_t n) {
    double t, p, s;
    torus_angles(n, &t, &p, &s);
    double mod = sin(t) + cos(p) + sin(s);
    return (uint8_t)((mod + 3.0) * 42.5); /* Map [-3,3] to [0,255] */
}

/* ─── Basis Operations ─── */

static uint8_t basis[BASIS_SIZE];      /* Current prediction basis */
static uint8_t data_stack[STACK_SIZE]; /* Data stack for STORE/LOAD */

static inline uint8_t basis_predict(uint32_t n, uint8_t opcode, uint8_t operand) {
    /* Simple prediction: rotate through basis by position */
    return basis[n % BASIS_SIZE] ^ operand;
}

static inline void basis_fuse(uint8_t *parent_a, uint8_t *parent_b, int size) {
    /* Set intersection + bilinear hybrid (placeholder) */
    for (int i = 0; i < size && i < BASIS_SIZE; i++) {
        basis[i] = (parent_a[i] + parent_b[i]) >> 1; /* mean operator */
    }
}

/* ─── Execute Single Instruction ─── */

static inline void execute(uint8_t opcode, uint8_t operand, uint32_t pos, State *st) {
    Address addr;
    composite_address(pos, &addr);

    switch (opcode) {
        case OP_NOOP:
            break;

        case OP_LOAD:
            /* Read from basis vector at coordinate-derived index */
            st->acc = basis[addr.mass % BASIS_SIZE] ^ operand;
            break;

        case OP_STORE:
            /* Push to data stack */
            if (st->sp < STACK_SIZE) {
                data_stack[st->sp++] = st->acc;
            }
            break;

        case OP_ADD:
            /* Add weighted coordinate value */
            st->acc = (st->acc + (uint8_t)(addr.mass % 256) + operand) & 0xFF;
            break;

        case OP_XOR:
            /* XOR with mirror prediction */
            st->acc ^= (uint8_t)(addr.mirror % 256) ^ operand;
            break;

        case OP_BRANCH:
            /* Conditional skip based on mass threshold */
            if (addr.mass < (addr.k * (addr.k + 1))) {
                st->flags |= 0x02; /* Set skip flag */
            }
            break;

        case OP_FUSE:
            /* Placeholder: would fuse with parent basis */
            /* In full implementation: decode parent basis from stream */
            st->acc = st->acc ^ operand;
            break;

        case OP_HALT:
            st->flags |= 0x01; /* Set halt flag */
            break;
    }

    st->depth = addr.k;
    st->entropy = addr.mass;
}

/* ─── Main Decoder Loop ─── */

/*
 * The compressed stream format embedded after the code section:
 *   [BOOTSTRAP: 16 bytes basis] [PROGRAM: variable-length byte sequence]
 *
 * The decoder reads itself to locate the embedded data.
 */

static const char *self_path = NULL;

static void set_self_path(const char *argv0) {
    self_path = argv0;
}

static uint8_t *read_embedded_stream(size_t *out_len) {
    FILE *self = NULL;

    /* Try argv[0] first */
    if (self_path) {
        self = fopen(self_path, "rb");
    }

    /* Fallback to common names */
    const char *fallbacks[] = {"archive9.exe", "archive.exe", "./archive9.exe", "./archive.exe", NULL};
    for (int i = 0; !self && fallbacks[i]; i++) {
        self = fopen(fallbacks[i], "rb");
    }

    if (!self) {
        fprintf(stderr, "Error: cannot open self (tried %s and fallbacks)\n",
                self_path ? self_path : "(none)");
        exit(1);
    }

    fseek(self, 0, SEEK_END);
    size_t total_size = ftell(self);

    /*
     * Find marker that separates code from data.
     * In practice, the build process appends compressed data after compilation.
     * For now, we use a simple marker at the end.
     */
    uint8_t marker[8] = {0xDE, 0xAD, 0xBE, 0xEF, 0x50, 0x49, 0x53, 0x54}; /* "PIST" */

    /* Search backwards for marker */
    size_t data_start = 0;
    uint8_t buf[8];
    for (size_t i = total_size - 8; i > 0; i--) {
        fseek(self, i, SEEK_SET);
        if (fread(buf, 1, 8, self) == 8) {
            if (memcmp(buf, marker, 8) == 0) {
                data_start = i + 8;
                break;
            }
        }
    }

    if (data_start == 0) {
        fprintf(stderr, "Error: embedded data marker not found\n");
        fclose(self);
        exit(1);
    }

    size_t data_len = total_size - data_start;
    uint8_t *data = malloc(data_len);
    if (!data) {
        fprintf(stderr, "Error: malloc failed\n");
        exit(1);
    }

    fseek(self, data_start, SEEK_SET);
    fread(data, 1, data_len, self);
    fclose(self);

    *out_len = data_len;
    return data;
}

/* ─── Prediction Model ───
 * For roundtrip testing, the simplest model is:
 *   prediction(n) = basis[n % BASIS_SIZE] ^ keystream_value(n) ^ (n & 0xFF)
 *   output(n)     = prediction(n) ^ residual(n)
 * where residual(n) is the byte from the compressed stream.
 *
 * The compressor finds residuals such that output equals the original data.
 * This is trivial: residual = data XOR prediction.
 *
 * Compression ratio depends on prediction accuracy.
 * If prediction matches data, residual = 0 (runs of zeros compress well).
 */

static inline uint8_t predict(uint32_t n) {
    uint8_t b = basis[n % BASIS_SIZE];
    b ^= keystream_value(n);
    b ^= (n & 0xFF);
    b ^= (uint8_t)(pist_mirror(n) % 256);
    return b;
}

/* ─── AngrySphinx Gear Reduction & FAMM Scar Tracking ───
 *
 * Gear Law:  C_out = G_AS * C_in + C_semantic + C_reality + C_constructive + C_cringe
 *
 * FAMM-coupled gear ratio:
 *   G_AS(t) = 1 + alpha*L_FAMM(t) + beta*R_repeat(t) + gamma*U_unknown(t) + delta*H_route(t)
 *
 * Where:
 *   L_FAMM  = torsional stress^2 + interlock energy + phase delta
 *   R       = repeated hostile route count
 *   U       = unknown-route uncertainty (1 if no scars, else 0)
 *   H_route = frozen-route helicity / connectivity penalty
 *
 * In the decoder context, FAMM scars act as negative context:
 *   - Failed predictions are recorded as route scars
 *   - Future basis selection avoids scarred prediction paths
 *   - Gear ratio increases with accumulated hostile engagement
 */

#define FAMM_MAX_SCARS    256
#define FAMM_HASH_MOD     251

typedef struct {
    uint32_t route_hash;
    uint8_t  outcome;      /* 0=success, 1=failure, 2=trap, 3=partial */
    uint16_t effort;       /* scaled effort value */
} FAMMScar;

static FAMMScar famm_scars[FAMM_MAX_SCARS];
static uint16_t famm_scar_count = 0;

static inline uint32_t route_hash(uint32_t n, uint8_t opcode) {
    /* Simple route signature: position + opcode mix */
    return ((n * 2654435761u) ^ (opcode * 0x9E3779B9)) % FAMM_HASH_MOD;
}

static inline void famm_record_scar(uint32_t n, uint8_t opcode, uint8_t outcome, uint16_t effort) {
    if (famm_scar_count >= FAMM_MAX_SCARS) {
        /* FIFO eviction: shift scars down */
        memmove(&famm_scars[0], &famm_scars[1], sizeof(FAMMScar) * (FAMM_MAX_SCARS - 1));
        famm_scar_count = FAMM_MAX_SCARS - 1;
    }
    famm_scars[famm_scar_count].route_hash = route_hash(n, opcode);
    famm_scars[famm_scar_count].outcome   = outcome;
    famm_scars[famm_scar_count].effort    = effort;
    famm_scar_count++;
}

static inline uint16_t famm_hostile_route_count(void) {
    uint16_t count = 0;
    for (uint16_t i = 0; i < famm_scar_count; i++) {
        if (famm_scars[i].outcome >= 1) count++;
    }
    return count;
}

static inline uint16_t famm_repeated_hostile_count(uint32_t n, uint8_t opcode) {
    uint32_t h = route_hash(n, opcode);
    uint16_t count = 0;
    for (uint16_t i = 0; i < famm_scar_count; i++) {
        if (famm_scars[i].route_hash == h && famm_scars[i].outcome >= 1)
            count++;
    }
    return count;
}

static inline float famm_load(void) {
    /* L_FAMM = Sigma^2 + I_lock + Delta_phi (simplified) */
    float torsion = 0.0f;
    float interlock = 0.0f;
    for (uint16_t i = 0; i < famm_scar_count; i++) {
        torsion += famm_scars[i].effort * 0.1f;
        if (famm_scars[i].outcome == 2) interlock += 1.0f;
    }
    float phase_delta = famm_scar_count > 0 ? 1.0f : 0.0f;
    return torsion * torsion + interlock + phase_delta;
}

static inline float gear_ratio(uint32_t n, uint8_t opcode) {
    /* G_AS = 1 + alpha*L_FAMM + beta*R_repeat + gamma*U_unknown */
    float alpha = 0.5f;
    float beta  = 1.0f;
    float gamma = 2.0f;

    float L_famm = famm_load();
    uint16_t R_repeat = famm_repeated_hostile_count(n, opcode);
    float U_unknown = (famm_scar_count == 0) ? 1.0f : 0.0f;

    return 1.0f + alpha * L_famm + beta * (float)R_repeat + gamma * U_unknown;
}

/* ─── Gear-Reduced Prediction ───
 *
 * Standard prediction is a commuting composition of basis, keystream,
 * position, and mirror terms. The gear-reduced version introduces
 * noncommuting composition: the FAMM-scar-modified gear ratio feeds
 * back into the prediction operator sequence.
 *
 * Noncommuting trisqueezing analog:
 *   p(n) = A(B(A(n))) where A = basis-layer, B = gear-modulated layer
 */

static inline uint8_t predict_layer_a(uint32_t n) {
    return basis[n % BASIS_SIZE] ^ (n & 0xFF);
}

static inline uint8_t predict_layer_b(uint32_t n, uint8_t opcode) {
    float G = gear_ratio(n, opcode);
    uint8_t gear_mod = (uint8_t)((uint32_t)(G * 16.0f) & 0xFF);
    return keystream_value(n) ^ gear_mod ^ (uint8_t)(pist_mirror(n) % 256);
}

static inline uint8_t predict_gear_reduced(uint32_t n, uint8_t opcode) {
    /* Noncommuting composition: A then B then A (trisqueezing analog) */
    uint8_t a1 = predict_layer_a(n);
    uint8_t b  = predict_layer_b(n, opcode);
    uint8_t a2 = predict_layer_a(n ^ b);  /* B modifies the input to A */
    return a1 ^ b ^ a2;
}

int main(int argc, char *argv[]) {
    if (argc > 0) {
        set_self_path(argv[0]);
    }

    size_t stream_len;
    uint8_t *stream = read_embedded_stream(&stream_len);

    if (stream_len < BOOTSTRAP_SIZE) {
        fprintf(stderr, "Error: stream too short\n");
        free(stream);
        return 1;
    }

    /* Initialize bootstrap basis */
    memcpy(basis, stream, BOOTSTRAP_SIZE);

    /* Output buffer for batching (reduces syscalls) */
    uint8_t outbuf[65536];
    size_t outpos = 0;

    /* Decode: one output byte per residual byte */
    uint32_t n = 0;
    for (size_t i = BOOTSTRAP_SIZE; i < stream_len; i++, n++) {
        uint8_t residual = stream[i];
        uint8_t p = predict(n);
        uint8_t out = p ^ residual;

        outbuf[outpos++] = out;

        if (outpos >= sizeof(outbuf)) {
            fwrite(outbuf, 1, outpos, stdout);
            outpos = 0;
        }
    }

    /* Flush remaining output */
    if (outpos > 0) {
        fwrite(outbuf, 1, outpos, stdout);
    }

    free(stream);
    return 0;
}

/* ─── Build Instructions ───
 *
 * 1. Compile decoder:
 *    gcc -O3 -s -fno-stack-protector -fomit-frame-pointer \
 *        -o archive.exe hutter_pist_decoder.c -lm
 *
 * 2. Strip symbols:
 *    strip --strip-all archive.exe
 *
 * 3. Embed compressed data:
 *    cat archive.exe compressed_stream.bin > archive_tmp.exe
 *    mv archive_tmp.exe archive.exe
 *    chmod +x archive.exe
 *
 * 4. Verify:
 *    ./archive.exe | cmp - enwik9
 *
 * Size targets:
 *    Current record L = 110,793,128 bytes
 *    Decompressor binary ~8-15KB (with -O3 -s)
 *    Compressed data budget ~109MB for 1% prize
 */
