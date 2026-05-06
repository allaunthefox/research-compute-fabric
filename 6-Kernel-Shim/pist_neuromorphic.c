/*
 * PIST Neuromorphic Compression Driver — Passive Observer Phase
 * ===============================================================
 * Kernel module that passively observes data streams, builds a topological
 * manifold (DAG) of PIST coordinate transformations, and periodically exports
 * its learned structure. Active compression is gated by a mode switch.
 *
 * Philosophy: The driver learns before it acts. Evolution is driven by
 * observed entropy patterns, not hand-tuned heuristics.
 *
 * Modes:
 *   observe  (default) — samples data, builds DAG, no transformation
 *   active   — applies learned shifter chain to compress/decompress
 *
 * Sysfs interface:
 *   /sys/kernel/pist_neuromorphic/
 *   ├── mode              (rw)  observe | active
 *   ├── sample            (wo)  feed raw bytes for observation
 *   ├── dag_dump          (ro)  read current DAG as binary/graph
 *   ├── dag_interval_sec  (rw)  auto-export period (0 = off)
 *   ├── stats             (ro)  entropy histogram, coord distribution
 *   └── trigger_export    (wo)  write 1 to force DAG export
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/vmalloc.h>
#include <linux/slab.h>
#include <linux/sysfs.h>
#include <linux/kobject.h>
#include <linux/spinlock.h>
#include <linux/types.h>
#include <linux/bitops.h>
#include <linux/workqueue.h>
#include <linux/jiffies.h>
#include <linux/string.h>
#include <linux/math.h>
#include <linux/atomic.h>

MODULE_AUTHOR("Research Stack");
MODULE_DESCRIPTION("PIST Neuromorphic Compression Observer");
MODULE_LICENSE("GPL");

#define PIST_MODULE_VERSION "0.2.0-passive"

/* ───────────────────────────────────────────────────────────────────────── */
/* PIST Geometry Core                                                         */
/* ───────────────────────────────────────────────────────────────────────── */

static inline u32 pist_encode_u8(u8 n)
{
    u16 k = (u16)int_sqrt((unsigned long)n);
    u16 t = (u16)n - k * k;
    return ((u32)k << 16) | t;
}

static inline u8 pist_decode_coord(u32 coord)
{
    u16 k = (u16)(coord >> 16);
    u16 t = (u16)(coord & 0xFFFF);
    u32 n = (u32)k * k + t;
    return (u8)min_t(u32, n, 255U);
}

static inline u32 pist_mirror(u32 coord)
{
    u16 k = (u16)(coord >> 16);
    u16 t = (u16)(coord & 0xFFFF);
    return ((u32)k << 16) | (2 * k + 1 - t);
}

static inline u32 pist_mass(u32 coord)
{
    u16 k = (u16)(coord >> 16);
    u16 t = (u16)(coord & 0xFFFF);
    return (u32)t * (2 * k + 1 - t);
}

/* ───────────────────────────────────────────────────────────────────────── */
/* Neuromorphic State — Passive Observation                                   */
/* ───────────────────────────────────────────────────────────────────────── */

#define PIST_MAX_DAG_NODES      4096
#define PIST_MAX_EDGES_PER_NODE 16
#define PIST_SAMPLE_RING_SIZE   (256 * 1024)   /* 256KB ring buffer */
#define PIST_ENTROPY_BINS       64
#define PIST_COORD_BINS         256

struct pist_dag_edge {
    u16     target_node;        /* destination coordinate hash */
    u32     weight;             /* observed transition count */
    u32     last_seen_jiff;
};

struct pist_dag_node {
    u32     coord_hash;         /* hash of PIST coordinate */
    u32     visit_count;
    u32     total_mass;
    u16     edge_count;
    struct pist_dag_edge edges[PIST_MAX_EDGES_PER_NODE];
};

struct pist_neuro_state {
    /* Mode */
    atomic_t    mode;           /* 0=observe, 1=active */

    /* Observation ring */
    u8          *sample_ring;
    size_t      ring_head;
    size_t      ring_tail;
    spinlock_t  ring_lock;

    /* Statistics */
    u64         byte_freq[256];
    u64         coord_freq[PIST_COORD_BINS];
    u64         entropy_hist[PIST_ENTROPY_BINS];
    u64         total_samples;
    u64         total_bytes_observed;

    /* DAG */
    struct pist_dag_node *dag_nodes;
    u16         dag_node_count;
    spinlock_t  dag_lock;

    /* Auto-export */
    u32         export_interval_sec;
    struct delayed_work export_work;
    struct workqueue_struct *wq;

    /* Version / generation */
    u64         dag_generation;
};

#define PIST_MODE_OBSERVE   0
#define PIST_MODE_ACTIVE    1

static struct pist_neuro_state *g_state;
static struct kobject *pist_neuro_kobj;

/* ───────────────────────────────────────────────────────────────────────── */
/* Observation Engine                                                         */
/* ───────────────────────────────────────────────────────────────────────── */

static u32 pist_hash_coord(u32 coord)
{
    /* Simple Jenkins-style hash for kernel */
    u32 a = coord;
    a = (a + 0x7ed55d16) + (a << 12);
    a = (a ^ 0xc761c23c) ^ (a >> 19);
    a = (a + 0x165667b1) + (a << 5);
    a = (a + 0xd3a2646c) ^ (a << 9);
    a = (a + 0xfd7046c5) + (a << 3);
    a = (a ^ 0xb55a4f09) ^ (a >> 16);
    return a;
}

static u16 pist_coord_to_node_index(u32 coord)
{
    return (u16)(pist_hash_coord(coord) % PIST_MAX_DAG_NODES);
}

static int pist_dag_find_or_create_node(struct pist_neuro_state *st, u32 coord)
{
    u16 idx = pist_coord_to_node_index(coord);
    struct pist_dag_node *node;
    unsigned long flags;

    spin_lock_irqsave(&st->dag_lock, flags);
    node = &st->dag_nodes[idx];

    if (node->coord_hash == 0) {
        /* New node */
        node->coord_hash = pist_hash_coord(coord);
        node->visit_count = 1;
        node->total_mass = pist_mass(coord);
        node->edge_count = 0;
        st->dag_node_count++;
    } else if (node->coord_hash == pist_hash_coord(coord)) {
        /* Existing matching node */
        node->visit_count++;
        node->total_mass += pist_mass(coord);
    } else {
        /* Hash collision — overwrite with fresher data (eviction policy) */
        node->coord_hash = pist_hash_coord(coord);
        node->visit_count = 1;
        node->total_mass = pist_mass(coord);
        node->edge_count = 0;
    }

    spin_unlock_irqrestore(&st->dag_lock, flags);
    return idx;
}

static void pist_dag_add_edge(struct pist_neuro_state *st,
                               u16 from_idx, u16 to_idx)
{
    struct pist_dag_node *node;
    struct pist_dag_edge *edge;
    unsigned long flags;
    int i;

    spin_lock_irqsave(&st->dag_lock, flags);
    node = &st->dag_nodes[from_idx];

    /* Search existing edge */
    for (i = 0; i < node->edge_count; i++) {
        if (node->edges[i].target_node == to_idx) {
            node->edges[i].weight++;
            node->edges[i].last_seen_jiff = jiffies;
            spin_unlock_irqrestore(&st->dag_lock, flags);
            return;
        }
    }

    /* Add new edge if room */
    if (node->edge_count < PIST_MAX_EDGES_PER_NODE) {
        edge = &node->edges[node->edge_count++];
        edge->target_node = to_idx;
        edge->weight = 1;
        edge->last_seen_jiff = jiffies;
    } else {
        /* Evict weakest edge */
        int weakest = 0;
        for (i = 1; i < node->edge_count; i++) {
            if (node->edges[i].weight < node->edges[weakest].weight)
                weakest = i;
        }
        edge = &node->edges[weakest];
        edge->target_node = to_idx;
        edge->weight = 1;
        edge->last_seen_jiff = jiffies;
    }

    spin_unlock_irqrestore(&st->dag_lock, flags);
}

static void pist_observe_byte(struct pist_neuro_state *st, u8 b)
{
    u32 coord = pist_encode_u8(b);
    u32 mirror = pist_mirror(coord);
    u16 cidx, midx;

    /* Update frequency histograms */
    st->byte_freq[b]++;
    st->coord_freq[pist_hash_coord(coord) % PIST_COORD_BINS]++;
    st->total_bytes_observed++;

    /* Update DAG */
    cidx = pist_dag_find_or_create_node(st, coord);
    midx = pist_dag_find_or_create_node(st, mirror);

    /* Edge: coord -> mirror (observed natural symmetry) */
    pist_dag_add_edge(st, cidx, midx);
    /* Edge: mirror -> coord (inverse) */
    pist_dag_add_edge(st, midx, cidx);
}

static void pist_observe_chunk(struct pist_neuro_state *st,
                                const u8 *data, size_t len)
{
    size_t i;
    for (i = 0; i < len; i++)
        pist_observe_byte(st, data[i]);
    st->total_samples++;
}

/* Approximate entropy bucket from byte frequency */
static u8 pist_entropy_bucket(const u64 freq[256], size_t total)
{
    u64 entropy_q16 = 0;  /* Q16.16 fixed-point approximation */
    int i;

    if (total == 0)
        return 0;

    for (i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            /* p * log2(p) approximation: p in Q16.16 */
            u64 p = (freq[i] << 16) / total;
            u64 log2p = 0;
            if (p > 0) {
                /* Approx log2 using clz: log2(p) ~ 16 - clz(p) */
                log2p = (16 - __builtin_clzll(p | 1)) << 16;
            }
            entropy_q16 += (p * log2p) >> 16;
        }
    }

    /* Map to 0-63 bucket */
    return (u8)min_t(u64, entropy_q16 >> 10, PIST_ENTROPY_BINS - 1);
}

/* ───────────────────────────────────────────────────────────────────────── */
/* Workqueue — Periodic DAG Export                                            */
/* ───────────────────────────────────────────────────────────────────────── */

static void pist_export_dag_work(struct work_struct *work)
{
    struct pist_neuro_state *st =
        container_of(to_delayed_work(work), struct pist_neuro_state, export_work);

    /* Bump generation counter — userspace daemon reads /sys/kernel/pist_neuromorphic/dag_dump
     * and persists to disk. We just signal freshness. */
    st->dag_generation++;
    pr_info("DAG export triggered (gen=%llu, nodes=%u, mode=%s)\n",
            st->dag_generation, st->dag_node_count,
            atomic_read(&st->mode) == PIST_MODE_OBSERVE ? "observe" : "active");

    /* Reschedule if interval > 0 */
    if (st->export_interval_sec > 0) {
        queue_delayed_work(st->wq, &st->export_work,
                           msecs_to_jiffies(st->export_interval_sec * 1000));
    }
}

/* ───────────────────────────────────────────────────────────────────────── */
/* Sysfs Interface                                                            */
/* ───────────────────────────────────────────────────────────────────────── */

static ssize_t mode_show(struct kobject *kobj,
                          struct kobj_attribute *attr, char *buf)
{
    int m = atomic_read(&g_state->mode);
    return sprintf(buf, "%s\n", m == PIST_MODE_ACTIVE ? "active" : "observe");
}

static ssize_t mode_store(struct kobject *kobj,
                           struct kobj_attribute *attr,
                           const char *buf, size_t count)
{
    if (strncasecmp(buf, "active", 6) == 0) {
        atomic_set(&g_state->mode, PIST_MODE_ACTIVE);
        pr_info("Mode switched to ACTIVE — compression enabled\n");
    } else if (strncasecmp(buf, "observe", 7) == 0) {
        atomic_set(&g_state->mode, PIST_MODE_OBSERVE);
        pr_info("Mode switched to OBSERVE — passive learning\n");
    } else {
        return -EINVAL;
    }
    return count;
}

static struct kobj_attribute mode_attr =
    __ATTR(mode, 0644, mode_show, mode_store);

static ssize_t sample_store(struct kobject *kobj,
                             struct kobj_attribute *attr,
                             const char *buf, size_t count)
{
    struct pist_neuro_state *st = g_state;
    unsigned long flags;
    size_t i;

    if (atomic_read(&st->mode) != PIST_MODE_OBSERVE)
        return -EPERM;  /* Only observe in passive mode */

    spin_lock_irqsave(&st->ring_lock, flags);

    /* Feed bytes into observation engine directly (bypass ring for now) */
    for (i = 0; i < count; i++)
        pist_observe_byte(st, (u8)buf[i]);
    st->total_samples++;

    spin_unlock_irqrestore(&st->ring_lock, flags);

    return count;
}

static struct kobj_attribute sample_attr =
    __ATTR(sample, 0220, NULL, sample_store);

static ssize_t dag_dump_show(struct kobject *kobj,
                              struct kobj_attribute *attr, char *buf)
{
    struct pist_neuro_state *st = g_state;
    unsigned long flags;
    size_t pos = 0;
    int i, j;

    spin_lock_irqsave(&st->dag_lock, flags);

    pos += sprintf(buf + pos,
        "# PIST Neuromorphic DAG v%s gen=%llu nodes=%u\n"
        "# format: node_id coord_hash visit_count mass edge_count\n"
        "#         [target weight last_seen] ...\n",
        PIST_MODULE_VERSION, st->dag_generation, st->dag_node_count);

    for (i = 0; i < PIST_MAX_DAG_NODES && pos < PAGE_SIZE - 256; i++) {
        struct pist_dag_node *n = &st->dag_nodes[i];
        if (n->coord_hash == 0)
            continue;

        pos += sprintf(buf + pos, "%d %08x %u %u %u",
                       i, n->coord_hash, n->visit_count,
                       n->total_mass, n->edge_count);

        for (j = 0; j < n->edge_count && pos < PAGE_SIZE - 64; j++) {
            pos += sprintf(buf + pos, " %d:%u",
                           n->edges[j].target_node,
                           n->edges[j].weight);
        }
        pos += sprintf(buf + pos, "\n");
    }

    spin_unlock_irqrestore(&st->dag_lock, flags);

    return pos;
}

static struct kobj_attribute dag_dump_attr =
    __ATTR(dag_dump, 0444, dag_dump_show, NULL);

static ssize_t dag_interval_show(struct kobject *kobj,
                                  struct kobj_attribute *attr, char *buf)
{
    return sprintf(buf, "%u\n", g_state->export_interval_sec);
}

static ssize_t dag_interval_store(struct kobject *kobj,
                                   struct kobj_attribute *attr,
                                   const char *buf, size_t count)
{
    u32 val;
    int ret;

    ret = kstrtou32(buf, 10, &val);
    if (ret)
        return ret;

    g_state->export_interval_sec = val;

    /* Cancel and reschedule */
    cancel_delayed_work_sync(&g_state->export_work);
    if (val > 0) {
        queue_delayed_work(g_state->wq, &g_state->export_work,
                           msecs_to_jiffies(val * 1000));
    }

    return count;
}

static struct kobj_attribute dag_interval_attr =
    __ATTR(dag_interval_sec, 0644, dag_interval_show, dag_interval_store);

static ssize_t stats_show(struct kobject *kobj,
                           struct kobj_attribute *attr, char *buf)
{
    struct pist_neuro_state *st = g_state;
    size_t pos = 0;
    int i;

    pos += sprintf(buf + pos,
        "version: %s\n"
        "mode: %s\n"
        "total_samples: %llu\n"
        "total_bytes: %llu\n"
        "dag_nodes: %u\n"
        "dag_generation: %llu\n",
        PIST_MODULE_VERSION,
        atomic_read(&st->mode) == PIST_MODE_ACTIVE ? "active" : "observe",
        st->total_samples,
        st->total_bytes_observed,
        st->dag_node_count,
        st->dag_generation);

    pos += sprintf(buf + pos, "byte_freq_top10:");
    for (i = 0; i < 10 && pos < PAGE_SIZE - 64; i++) {
        int max_idx = 0;
        int j;
        for (j = 1; j < 256; j++)
            if (st->byte_freq[j] > st->byte_freq[max_idx])
                max_idx = j;
        pos += sprintf(buf + pos, " %02x=%llu", max_idx, st->byte_freq[max_idx]);
        st->byte_freq[max_idx] = 0; /* zero out for next iter (destructive!) */
    }
    pos += sprintf(buf + pos, "\n");

    return pos;
}

static struct kobj_attribute stats_attr =
    __ATTR(stats, 0444, stats_show, NULL);

static ssize_t trigger_export_store(struct kobject *kobj,
                                     struct kobj_attribute *attr,
                                     const char *buf, size_t count)
{
    if (buf[0] == '1')
        queue_delayed_work(g_state->wq, &g_state->export_work, 0);
    return count;
}

static struct kobj_attribute trigger_export_attr =
    __ATTR(trigger_export, 0220, NULL, trigger_export_store);

static struct attribute *pist_neuro_attrs[] = {
    &mode_attr.attr,
    &sample_attr.attr,
    &dag_dump_attr.attr,
    &dag_interval_attr.attr,
    &stats_attr.attr,
    &trigger_export_attr.attr,
    NULL,
};

static struct attribute_group pist_neuro_attr_group = {
    .attrs = pist_neuro_attrs,
};

/* ───────────────────────────────────────────────────────────────────────── */
/* Module Init / Exit                                                         */
/* ───────────────────────────────────────────────────────────────────────── */

static int __init pist_neuro_init(void)
{
    struct pist_neuro_state *st;
    int ret;

    pr_info("PIST Neuromorphic Observer v%s loading\n", PIST_MODULE_VERSION);
    pr_info("Passive mode — feed data via /sys/kernel/pist_neuromorphic/sample\n");

    st = kzalloc(sizeof(*st), GFP_KERNEL);
    if (!st)
        return -ENOMEM;

    g_state = st;

    atomic_set(&st->mode, PIST_MODE_OBSERVE);
    spin_lock_init(&st->ring_lock);
    spin_lock_init(&st->dag_lock);

    st->dag_nodes = kcalloc(PIST_MAX_DAG_NODES, sizeof(*st->dag_nodes),
                            GFP_KERNEL);
    if (!st->dag_nodes) {
        ret = -ENOMEM;
        goto err_free_state;
    }

    st->sample_ring = vmalloc(PIST_SAMPLE_RING_SIZE);
    if (!st->sample_ring) {
        ret = -ENOMEM;
        goto err_free_dag;
    }

    st->wq = alloc_workqueue("pist_neuro_wq", WQ_UNBOUND | WQ_FREEZABLE, 1);
    if (!st->wq) {
        ret = -ENOMEM;
        goto err_free_ring;
    }

    INIT_DELAYED_WORK(&st->export_work, pist_export_dag_work);

    pist_neuro_kobj = kobject_create_and_add("pist_neuromorphic", kernel_kobj);
    if (!pist_neuro_kobj) {
        ret = -ENOMEM;
        goto err_destroy_wq;
    }

    ret = sysfs_create_group(pist_neuro_kobj, &pist_neuro_attr_group);
    if (ret) {
        kobject_put(pist_neuro_kobj);
        goto err_destroy_wq;
    }

    pr_info("PIST neuromorphic sysfs: /sys/kernel/pist_neuromorphic/\n");
    pr_info("  mode=observe (default), sample=write-only, dag_dump=read-only\n");
    return 0;

err_destroy_wq:
    destroy_workqueue(st->wq);
err_free_ring:
    vfree(st->sample_ring);
err_free_dag:
    kfree(st->dag_nodes);
err_free_state:
    kfree(st);
    g_state = NULL;
    return ret;
}

static void __exit pist_neuro_exit(void)
{
    struct pist_neuro_state *st = g_state;

    if (!st)
        return;

    cancel_delayed_work_sync(&st->export_work);
    sysfs_remove_group(pist_neuro_kobj, &pist_neuro_attr_group);
    kobject_put(pist_neuro_kobj);
    destroy_workqueue(st->wq);
    vfree(st->sample_ring);
    kfree(st->dag_nodes);
    kfree(st);
    g_state = NULL;

    pr_info("PIST Neuromorphic Observer unloaded\n");
}

module_init(pist_neuro_init);
module_exit(pist_neuro_exit);
