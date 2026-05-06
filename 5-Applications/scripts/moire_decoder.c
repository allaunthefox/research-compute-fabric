/*
 * Moiré Multilayer Decoder
 *
 * Architecture: 4-layer van der Waals stack with twist-angle mixing.
 * Each layer has its own periodicity (basis) and twist relative to the layer below.
 * The gap between layers is where basis fusion (prediction blending) occurs.
 * Torsional force tracks prediction error and feeds back into gap width adaptation.
 *
 * Based on:
 *   - PIST composite addressing (tree, surface, torus, shell)
 *   - van der Waals moiré physics (twist bilayer graphene)
 *   - Torsional force microscopy (PNAS 2024)
 *   - Genetic parallelism / evolutionary cheat sheet (PLoS Biology 2026)
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

#define NUM_LAYERS      4
#define BASIS_SIZE      16
#define HISTORY_SIZE    256
#define MAX_CONTEXT     256
#define TWIST_BITS      4   /* twist encoded in 4 bits per layer */
#define MAX_DOMAINS     8   /* cross-domain basis library size */

/*
 * Each layer is a periodic structure at a different scale.
 * Layer 0: character-level   (1-byte period, twist = 0)
 * Layer 1: word-level       (4-6 byte period, small twist)
 * Layer 2: phrase-level     (20-50 byte period, larger twist)
 * Layer 3: sentence/struct  (100+ byte period, largest twist)
 */
typedef struct {
    uint8_t  basis[BASIS_SIZE];     /* periodic prediction pattern */
    float    twist;                  /* phase shift from layer below, radians */
    float    gap;                    /* coupling strength to layer below [0,1] */
    float    torsion_force;          /* accumulated prediction error */
    uint32_t period;                 /* natural period in bytes */
} Layer;

/*
 * The decoder state is the multilayer stack plus a history tape
 * (Bennett reversibility: no information discarded, only appended).
 */
typedef struct {
    Layer    layers[NUM_LAYERS];
    uint8_t  history[HISTORY_SIZE];  /* FAMM scar tape */
    uint32_t h_pos;                  /* write position in history */
    uint32_t position;               /* global byte position */

    /* Empirical frequency tables per layer, per context */
    float    freq[NUM_LAYERS][MAX_CONTEXT][256];
    float    total[NUM_LAYERS][MAX_CONTEXT];
} MoireDecoder;

/* ─── Helpers ─── */

static inline float sigmoid(float x) {
    return 1.0f / (1.0f + expf(-x));
}

static inline uint8_t hash_mix(uint32_t a, uint32_t b) {
    /* Knuth multiplicative hash mix */
    return (uint8_t)((a * 2654435761u + b * 0x9e3779b9u) >> 24);
}

/* ─── Layer prediction ─── */

static uint8_t predict_layer(MoireDecoder *dec, int layer_idx, uint32_t pos) {
    Layer *L = &dec->layers[layer_idx];

    /* Periodic prediction from basis */
    uint32_t idx = (pos / L->period) % BASIS_SIZE;
    uint8_t base = L->basis[idx];

    /* Twist correction: phase shift from layer below */
    if (layer_idx > 0) {
        float phase = L->twist * (float)(pos % L->period) / (float)L->period;
        uint8_t twist_corr = (uint8_t)(sinf(phase) * 127.0f);
        base ^= twist_corr;
    }

    /* Torsional force shear: recent errors modify prediction */
    if (dec->h_pos > 0) {
        uint8_t last_err = dec->history[(dec->h_pos - 1) % HISTORY_SIZE];
        float shear = L->torsion_force * 0.01f;
        base ^= (uint8_t)(last_err * shear);
    }

    return base;
}

/* ─── Basis fusion across the gap ─── */

static float blend_weight(float gap, float torsion) {
    /* Gap narrows under high torsion (stronger coupling when stressed) */
    float effective_gap = gap * (1.0f - 0.5f * sigmoid(torsion));
    return 1.0f - effective_gap;
}

static uint8_t fuse_layers(MoireDecoder *dec, uint32_t pos) {
    float weights[NUM_LAYERS];
    uint8_t preds[NUM_LAYERS];
    float total_weight = 0.0f;

    /* Collect predictions and weights from all layers */
    for (int i = 0; i < NUM_LAYERS; i++) {
        preds[i] = predict_layer(dec, i, pos);
        weights[i] = blend_weight(dec->layers[i].gap, dec->layers[i].torsion_force);
        total_weight += weights[i];
    }

    /* Weighted majority vote (spin-1 mixing) */
    float vote[256];
    memset(vote, 0, sizeof(vote));

    for (int i = 0; i < NUM_LAYERS; i++) {
        float w = weights[i] / total_weight;
        vote[preds[i]] += w;
        /* Also vote for neighbors (smooth blending) */
        vote[(preds[i] + 1) & 0xFF] += w * 0.3f;
        vote[(preds[i] - 1) & 0xFF] += w * 0.3f;
    }

    /* Find peak vote */
    int best = 0;
    for (int i = 1; i < 256; i++) {
        if (vote[i] > vote[best]) best = i;
    }

    return (uint8_t)best;
}

/* ─── Empirical context model ─── */

static uint8_t predict_statistical(MoireDecoder *dec, uint8_t context) {
    /* Use Layer 0 (character-level) frequency table */
    float *probs = dec->freq[0][context];
    float total = dec->total[0][context];

    if (total < 1.0f) {
        return (uint8_t)(context * 7 + 13); /* fallback hash */
    }

    /* Return most probable byte */
    int best = 0;
    for (int i = 1; i < 256; i++) {
        if (probs[i] > probs[best]) best = i;
    }
    return (uint8_t)best;
}

/* ─── Adaptive mixing: moiré vs. statistical ─── */

static float moire_confidence(MoireDecoder *dec) {
    /* Confidence increases when layers agree (low variance between preds) */
    float mean_twist = 0.0f;
    for (int i = 0; i < NUM_LAYERS; i++) {
        mean_twist += dec->layers[i].torsion_force;
    }
    mean_twist /= NUM_LAYERS;

    float var = 0.0f;
    for (int i = 0; i < NUM_LAYERS; i++) {
        float d = dec->layers[i].torsion_force - mean_twist;
        var += d * d;
    }
    var /= NUM_LAYERS;

    /* Low variance = high confidence in moiré prediction */
    return sigmoid(2.0f - var);
}

static uint8_t predict(MoireDecoder *dec, uint8_t context, uint32_t pos) {
    uint8_t moire_pred = fuse_layers(dec, pos);
    uint8_t stat_pred  = predict_statistical(dec, context);

    float alpha = moire_confidence(dec);

    /* Blend: alpha * moire + (1-alpha) * statistical */
    return (uint8_t)(alpha * moire_pred + (1.0f - alpha) * stat_pred);
}

/* ─── Cross-Domain Basis Migration ─── */

typedef struct {
    char     name[32];
    uint8_t  basis[BASIS_SIZE];
    float    fitness;    /* historical prediction accuracy */
} BasisDomain;

typedef struct {
    BasisDomain domains[MAX_DOMAINS];
    int count;
} BasisLibrary;

static BasisLibrary g_library;

static void library_init(void) {
    memset(&g_library, 0, sizeof(g_library));
    /* Pre-seed with known domain basis vectors */
    const char *names[MAX_DOMAINS] = {
        "ascii_text", "xml_markup", "english_words",
        "citations", "math_symbols", "foreign_names",
        "tables_csv", "code_snippets"
    };
    for (int i = 0; i < MAX_DOMAINS; i++) {
        strncpy(g_library.domains[i].name, names[i], 31);
        for (int j = 0; j < BASIS_SIZE; j++) {
            g_library.domains[i].basis[j] = (uint8_t)(i * 31 + j * 17);
        }
        g_library.domains[i].fitness = 0.5f;
    }
    g_library.count = MAX_DOMAINS;
}

static void migrate_basis(Layer *L, int domain_idx) {
    if (domain_idx < 0 || domain_idx >= g_library.count) return;
    memcpy(L->basis, g_library.domains[domain_idx].basis, BASIS_SIZE);
    /* Twist adjusts to match the new domain's characteristic phase */
    L->twist = (float)(domain_idx + 1) * 0.4f;
}

static int select_best_domain(MoireDecoder *dec, int layer_idx) {
    /* Find the domain basis that would have minimized recent error */
    float best_score = 1e9f;
    int best_idx = -1;
    for (int d = 0; d < g_library.count; d++) {
        float score = g_library.domains[d].fitness;
        /* Prefer domains with fitness close to current layer's torsion */
        float match = fabsf(score - (1.0f - dec->layers[layer_idx].torsion_force));
        if (match < best_score) {
            best_score = match;
            best_idx = d;
        }
    }
    return best_idx;
}

/* ─── Forward declarations for cross-domain migration ─── */

static void library_init(void);
static void migrate_basis(Layer *L, int domain_idx);
static int select_best_domain(MoireDecoder *dec, int layer_idx);

/* ─── Decode loop ─── */

static void decode_byte(MoireDecoder *dec, uint8_t residual, uint8_t context) {
    uint8_t pred = predict(dec, context, dec->position);
    uint8_t actual = pred ^ residual;

    /* Update history tape (Bennett reversibility) */
    dec->history[dec->h_pos % HISTORY_SIZE] = residual;
    dec->h_pos++;

    /* Update torsional force on each layer */
    for (int i = 0; i < NUM_LAYERS; i++) {
        uint8_t layer_pred = predict_layer(dec, i, dec->position);
        float err = (float)(layer_pred ^ actual) / 255.0f;
        dec->layers[i].torsion_force = 0.9f * dec->layers[i].torsion_force + 0.1f * err;

        /* Adapt gap: high error → narrower gap (stronger coupling to next layer) */
        dec->layers[i].gap = sigmoid(2.0f - dec->layers[i].torsion_force * 5.0f);

        /* Cross-domain basis migration: if stressed, import from library */
        if (dec->layers[i].torsion_force > 0.3f && (dec->position % 64) == 0) {
            int best_domain = select_best_domain(dec, i);
            if (best_domain >= 0) {
                migrate_basis(&dec->layers[i], best_domain);
                /* Fitness feedback: reward successful migrations */
                g_library.domains[best_domain].fitness =
                    0.95f * g_library.domains[best_domain].fitness + 0.05f * (1.0f - err);
            }
        }
    }

    /* Update frequency tables */
    dec->freq[0][context][actual] += 1.0f;
    dec->total[0][context] += 1.0f;

    dec->position++;
}

/* ─── Initialization ─── */

static void init_layer(Layer *L, uint32_t period, float twist, float gap) {
    L->period = period;
    L->twist = twist;
    L->gap = gap;
    L->torsion_force = 0.0f;

    /* Initialize basis with structured pattern */
    for (int i = 0; i < BASIS_SIZE; i++) {
        L->basis[i] = (uint8_t)(i * 17 + period % 256);
    }
}

static void init_decoder(MoireDecoder *dec) {
    memset(dec, 0, sizeof(MoireDecoder));
    library_init();

    /* Layer stack: character → word → phrase → sentence */
    init_layer(&dec->layers[0], 1,   0.0f,  0.3f);  /* char level */
    init_layer(&dec->layers[1], 5,   0.3f,  0.5f);  /* word level */
    init_layer(&dec->layers[2], 25,  0.7f,  0.7f);  /* phrase level */
    init_layer(&dec->layers[3], 120, 1.2f,  0.9f);  /* sentence level */

    /* Seed frequency tables with small prior */
    for (int i = 0; i < NUM_LAYERS; i++) {
        for (int c = 0; c < MAX_CONTEXT; c++) {
            for (int b = 0; b < 256; b++) {
                dec->freq[i][c][b] = 0.5f;
            }
            dec->total[i][c] = 128.0f;
        }
    }
}

/* ─── Main decode function ─── */

int moire_decode(const uint8_t *residuals, size_t len,
                 uint8_t *output, size_t out_len) {
    MoireDecoder dec;
    init_decoder(&dec);

    uint8_t context = 0;
    size_t n = (len < out_len) ? len : out_len;

    for (size_t i = 0; i < n; i++) {
        uint8_t pred = predict(&dec, context, dec.position);
        output[i] = pred ^ residuals[i];
        decode_byte(&dec, residuals[i], context);
        context = output[i];
    }

    return (int)n;
}

/* ─── Encode function (symmetric) ─── */

int moire_encode(const uint8_t *input, size_t len,
                 uint8_t *residuals, size_t out_len) {
    MoireDecoder dec;
    init_decoder(&dec);

    uint8_t context = 0;
    size_t n = (len < out_len) ? len : out_len;

    for (size_t i = 0; i < n; i++) {
        uint8_t pred = predict(&dec, context, dec.position);
        residuals[i] = input[i] ^ pred;
        decode_byte(&dec, residuals[i], context);
        context = input[i];
    }

    return (int)n;
}

/* ─── Compression ratio estimator ─── */

double moire_estimate_entropy(const uint8_t *data, size_t len) {
    MoireDecoder dec;
    init_decoder(&dec);

    uint8_t context = 0;
    double total_bits = 0.0;

    for (size_t i = 0; i < len; i++) {
        uint8_t pred = predict(&dec, context, dec.position);
        uint8_t residual = data[i] ^ pred;

        /* Estimate bits: uniform = 8, zero residual = ~0 bits */
        double p = (residual == 0) ? 0.5 : (1.0 / 256.0);
        total_bits += -log2(p);

        decode_byte(&dec, residual, context);
        context = data[i];
    }

    return total_bits / (double)len;
}

/* ─── Test main ─── */

int main(int argc, char **argv) {
    const uint8_t *data;
    size_t len;
    int is_file = 0;

    if (argc >= 2) {
        /* Read from file */
        FILE *f = fopen(argv[1], "rb");
        if (!f) {
            perror("fopen");
            return 1;
        }
        fseek(f, 0, SEEK_END);
        len = (size_t)ftell(f);
        fseek(f, 0, SEEK_SET);
        uint8_t *buf = malloc(len);
        fread(buf, 1, len, f);
        fclose(f);
        data = buf;
        is_file = 1;
    } else {
        /* Default test string */
        static const char test[] = "The quick brown fox jumps over the lazy dog. "
                                    "The quick brown fox jumps over the lazy dog. "
                                    "The quick brown fox jumps over the lazy dog. ";
        data = (const uint8_t *)test;
        len = strlen(test);
    }

    uint8_t *residuals = malloc(len);
    uint8_t *decoded   = malloc(len);

    printf("Moire Multilayer Decoder — Test\n");
    printf("Input length: %zu bytes\n", len);

    /* Encode */
    int n_enc = moire_encode(data, len, residuals, len);
    printf("Encoded: %d bytes\n", n_enc);

    /* Estimate entropy */
    double ent = moire_estimate_entropy(data, len);
    printf("Estimated entropy: %.4f bits/byte\n", ent);

    /* Decode */
    int n_dec = moire_decode(residuals, len, decoded, len);
    printf("Decoded: %d bytes\n", n_dec);

    /* Verify round-trip */
    int ok = (memcmp(data, decoded, len) == 0);
    printf("Round-trip: %s\n", ok ? "PASS" : "FAIL");

    free(residuals);
    free(decoded);
    if (is_file) free((void *)data);
    return ok ? 0 : 1;
}
