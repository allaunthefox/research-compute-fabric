/*
 * QFox Topology Manager — passive nanokernel carrier
 * ==================================================
 *
 * This module is the safe Linux-carrier phase for the GCL nanokernel concept.
 * It observes carrier events, maps them into topology slots, and exposes a
 * receipt-shaped interface for userspace. It does not enforce policy.
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/atomic.h>
#include <linux/debugfs.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/jhash.h>
#include <linux/jiffies.h>
#include <linux/kernel.h>
#include <linux/kobject.h>
#include <linux/ktime.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/netdevice.h>
#include <linux/poll.h>
#include <linux/reboot.h>
#include <linux/seq_file.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/string.h>
#include <linux/uaccess.h>
#include <linux/wait.h>

MODULE_AUTHOR("Research Stack");
MODULE_DESCRIPTION("QFox passive topology manager and GCL nanokernel carrier");
MODULE_LICENSE("GPL");
MODULE_VERSION("0.1.0");

#define QFOX_VERSION "0.1.0-observe"
#define QFOX_RING_SIZE 256
#define QFOX_PAYLOAD_LEN 80
#define QFOX_READ_LIMIT 8192

enum qfox_slot {
	QFOX_SLOT_BOOT = 0,
	QFOX_SLOT_SCHED,
	QFOX_SLOT_MM,
	QFOX_SLOT_FS,
	QFOX_SLOT_BLOCK,
	QFOX_SLOT_NET,
	QFOX_SLOT_DEVICE,
	QFOX_SLOT_POWER,
	QFOX_SLOT_SECURITY,
	QFOX_SLOT_GPU,
	QFOX_SLOT_USER,
	QFOX_SLOT_RECEIPT,
	QFOX_SLOT_MAX,
};

struct qfox_event {
	u64 seq;
	u64 boottime_ns;
	u32 slot;
	u32 code;
	u32 payload_hash;
	char payload[QFOX_PAYLOAD_LEN];
};

struct qfox_state {
	spinlock_t lock;
	wait_queue_head_t waitq;
	atomic64_t seq;
	atomic_t enabled;
	u64 loaded_boottime_ns;
	u64 counters[QFOX_SLOT_MAX];
	struct qfox_event ring[QFOX_RING_SIZE];
	u32 head;
	struct kobject *kobj;
	struct dentry *debugfs_dir;
	struct miscdevice miscdev;
};

static struct qfox_state qfox;

static const char *const qfox_slot_names[QFOX_SLOT_MAX] = {
	[QFOX_SLOT_BOOT] = "boot",
	[QFOX_SLOT_SCHED] = "sched",
	[QFOX_SLOT_MM] = "mm",
	[QFOX_SLOT_FS] = "fs",
	[QFOX_SLOT_BLOCK] = "block",
	[QFOX_SLOT_NET] = "net",
	[QFOX_SLOT_DEVICE] = "device",
	[QFOX_SLOT_POWER] = "power",
	[QFOX_SLOT_SECURITY] = "security",
	[QFOX_SLOT_GPU] = "gpu",
	[QFOX_SLOT_USER] = "user",
	[QFOX_SLOT_RECEIPT] = "receipt",
};

static const char *qfox_slot_name(enum qfox_slot slot)
{
	if (slot >= QFOX_SLOT_MAX)
		return "unknown";
	return qfox_slot_names[slot];
}

static enum qfox_slot qfox_parse_slot(const char *token)
{
	int i;

	for (i = 0; i < QFOX_SLOT_MAX; i++) {
		if (sysfs_streq(token, qfox_slot_names[i]))
			return i;
	}

	return QFOX_SLOT_USER;
}

static void qfox_record(enum qfox_slot slot, u32 code, const char *payload)
{
	struct qfox_event *event;
	unsigned long flags;
	u64 seq;
	u32 idx;
	size_t len = 0;

	if (!atomic_read(&qfox.enabled) && slot != QFOX_SLOT_BOOT)
		return;

	if (slot >= QFOX_SLOT_MAX)
		slot = QFOX_SLOT_USER;

	seq = (u64)atomic64_inc_return(&qfox.seq);

	spin_lock_irqsave(&qfox.lock, flags);
	idx = qfox.head++ % QFOX_RING_SIZE;
	event = &qfox.ring[idx];
	memset(event, 0, sizeof(*event));
	event->seq = seq;
	event->boottime_ns = ktime_get_boottime_ns();
	event->slot = slot;
	event->code = code;
	if (payload) {
		strscpy(event->payload, payload, sizeof(event->payload));
		len = strnlen(event->payload, sizeof(event->payload));
		event->payload_hash = jhash(event->payload, len, 0x51464f58U);
	}
	qfox.counters[slot]++;
	spin_unlock_irqrestore(&qfox.lock, flags);

	wake_up_interruptible(&qfox.waitq);
}

static void qfox_record_from_buffer(const char *buf, size_t len)
{
	char local[QFOX_PAYLOAD_LEN];
	char token[24];
	char *cursor;
	char *space;
	enum qfox_slot slot;

	len = min_t(size_t, len, sizeof(local) - 1);
	memcpy(local, buf, len);
	local[len] = '\0';
	cursor = strim(local);

	if (!cursor || cursor[0] == '\0')
		return;

	strscpy(token, cursor, sizeof(token));
	space = strpbrk(token, " \t:\n");
	if (space)
		*space = '\0';

	slot = qfox_parse_slot(token);
	qfox_record(slot, 0, cursor);
}

static ssize_t status_show(struct kobject *kobj,
			   struct kobj_attribute *attr, char *buf)
{
	u64 now_ns = ktime_get_boottime_ns();
	u64 age_ns = now_ns - qfox.loaded_boottime_ns;
	u64 events = (u64)atomic64_read(&qfox.seq);
	u64 avg_x1000 = 0;

	if (age_ns > 0)
		avg_x1000 = div64_u64(events * 1000000000000ULL, age_ns);

	return sysfs_emit(buf,
			  "version=%s\nenabled=%d\nevents=%llu\nring_size=%d\nmode=observe\nloaded_boottime_ns=%llu\nage_ns=%llu\navg_events_per_sec_x1000=%llu\n",
			  QFOX_VERSION,
			  atomic_read(&qfox.enabled),
			  (unsigned long long)events,
			  QFOX_RING_SIZE,
			  (unsigned long long)qfox.loaded_boottime_ns,
			  (unsigned long long)age_ns,
			  (unsigned long long)avg_x1000);
}

static ssize_t mode_show(struct kobject *kobj,
			 struct kobj_attribute *attr, char *buf)
{
	return sysfs_emit(buf, "%s\n", atomic_read(&qfox.enabled) ? "observe" : "off");
}

static ssize_t mode_store(struct kobject *kobj,
			  struct kobj_attribute *attr,
			  const char *buf, size_t count)
{
	if (sysfs_streq(buf, "observe") || sysfs_streq(buf, "on")) {
		atomic_set(&qfox.enabled, 1);
		qfox_record(QFOX_SLOT_BOOT, 1, "mode=observe");
		return count;
	}
	if (sysfs_streq(buf, "off")) {
		qfox_record(QFOX_SLOT_BOOT, 0, "mode=off");
		atomic_set(&qfox.enabled, 0);
		return count;
	}
	return -EINVAL;
}

static ssize_t slots_show(struct kobject *kobj,
			  struct kobj_attribute *attr, char *buf)
{
	unsigned long flags;
	ssize_t off = 0;
	int i;

	spin_lock_irqsave(&qfox.lock, flags);
	for (i = 0; i < QFOX_SLOT_MAX; i++) {
		off += scnprintf(buf + off, PAGE_SIZE - off, "%s=%llu\n",
				 qfox_slot_name(i),
				 (unsigned long long)qfox.counters[i]);
		if (off >= PAGE_SIZE)
			break;
	}
	spin_unlock_irqrestore(&qfox.lock, flags);
	return off;
}

static ssize_t inject_store(struct kobject *kobj,
			    struct kobj_attribute *attr,
			    const char *buf, size_t count)
{
	qfox_record_from_buffer(buf, count);
	return count;
}

static struct kobj_attribute status_attr = __ATTR_RO(status);
static struct kobj_attribute mode_attr = __ATTR_RW(mode);
static struct kobj_attribute slots_attr = __ATTR_RO(slots);
static struct kobj_attribute inject_attr = __ATTR_WO(inject);

static struct attribute *qfox_attrs[] = {
	&status_attr.attr,
	&mode_attr.attr,
	&slots_attr.attr,
	&inject_attr.attr,
	NULL,
};

static const struct attribute_group qfox_attr_group = {
	.attrs = qfox_attrs,
};

static int qfox_events_show(struct seq_file *m, void *v)
{
	struct qfox_event *snapshot;
	unsigned long flags;
	u32 head;
	u32 count;
	u32 start;
	u32 i;

	snapshot = kcalloc(QFOX_RING_SIZE, sizeof(*snapshot), GFP_KERNEL);
	if (!snapshot)
		return -ENOMEM;

	spin_lock_irqsave(&qfox.lock, flags);
	head = qfox.head;
	count = min_t(u32, head, QFOX_RING_SIZE);
	start = head >= count ? head - count : 0;
	for (i = 0; i < count; i++)
		snapshot[i] = qfox.ring[(start + i) % QFOX_RING_SIZE];
	spin_unlock_irqrestore(&qfox.lock, flags);

	seq_printf(m, "schema=research_stack_qfox_topology_manager_events_v1\n");
	seq_printf(m, "version=%s\n", QFOX_VERSION);
	for (i = 0; i < count; i++) {
		struct qfox_event *event = &snapshot[i];

		if (event->seq == 0)
			continue;
		seq_printf(m,
			   "event seq=%llu ns=%llu slot=%s code=%u hash=%08x payload=\"%s\"\n",
			   (unsigned long long)event->seq,
			   (unsigned long long)event->boottime_ns,
			   qfox_slot_name(event->slot),
			   event->code,
			   event->payload_hash,
			   event->payload);
	}
	kfree(snapshot);
	return 0;
}

static int qfox_events_open(struct inode *inode, struct file *file)
{
	return single_open(file, qfox_events_show, inode->i_private);
}

static const struct file_operations qfox_events_fops = {
	.owner = THIS_MODULE,
	.open = qfox_events_open,
	.read = seq_read,
	.llseek = seq_lseek,
	.release = single_release,
};

static ssize_t qfox_dev_read(struct file *file, char __user *ubuf,
			     size_t count, loff_t *ppos)
{
	char *buf;
	ssize_t len = 0;
	ssize_t ret;
	unsigned long flags;
	int i;

	buf = kzalloc(QFOX_READ_LIMIT, GFP_KERNEL);
	if (!buf)
		return -ENOMEM;

	len += scnprintf(buf + len, QFOX_READ_LIMIT - len,
			 "{\"schema\":\"research_stack_qfox_topology_manager_v1\",");
	len += scnprintf(buf + len, QFOX_READ_LIMIT - len,
			 "\"version\":\"%s\",\"events\":%lld,\"slots\":{",
			 QFOX_VERSION,
			 (long long)atomic64_read(&qfox.seq));

	spin_lock_irqsave(&qfox.lock, flags);
	for (i = 0; i < QFOX_SLOT_MAX; i++) {
		len += scnprintf(buf + len, QFOX_READ_LIMIT - len,
				 "%s\"%s\":%llu",
				 i ? "," : "",
				 qfox_slot_name(i),
				 (unsigned long long)qfox.counters[i]);
		if (len >= QFOX_READ_LIMIT - 128)
			break;
	}
	spin_unlock_irqrestore(&qfox.lock, flags);
	len += scnprintf(buf + len, QFOX_READ_LIMIT - len, "}}\n");

	ret = simple_read_from_buffer(ubuf, count, ppos, buf, len);
	kfree(buf);
	return ret;
}

static ssize_t qfox_dev_write(struct file *file, const char __user *ubuf,
			      size_t count, loff_t *ppos)
{
	char buf[QFOX_PAYLOAD_LEN];
	char *cursor;
	char *line;
	size_t len = min_t(size_t, count, sizeof(buf) - 1);

	if (copy_from_user(buf, ubuf, len))
		return -EFAULT;
	buf[len] = '\0';
	cursor = buf;
	while ((line = strsep(&cursor, "\n")) != NULL) {
		line = strim(line);
		if (line[0] != '\0')
			qfox_record_from_buffer(line, strlen(line));
	}
	return count;
}

static __poll_t qfox_dev_poll(struct file *file, poll_table *wait)
{
	poll_wait(file, &qfox.waitq, wait);
	return EPOLLIN | EPOLLRDNORM | EPOLLOUT | EPOLLWRNORM;
}

static const struct file_operations qfox_dev_fops = {
	.owner = THIS_MODULE,
	.read = qfox_dev_read,
	.write = qfox_dev_write,
	.poll = qfox_dev_poll,
	.llseek = noop_llseek,
};

static int qfox_netdev_event(struct notifier_block *nb,
			     unsigned long event, void *ptr)
{
	struct net_device *dev = netdev_notifier_info_to_dev(ptr);
	char payload[QFOX_PAYLOAD_LEN];

	scnprintf(payload, sizeof(payload), "netdev=%s event=%lu",
		  dev ? dev->name : "unknown", event);
	qfox_record(QFOX_SLOT_NET, (u32)event, payload);
	return NOTIFY_DONE;
}

static int qfox_reboot_event(struct notifier_block *nb,
			     unsigned long event, void *ptr)
{
	qfox_record(QFOX_SLOT_POWER, (u32)event, "reboot_notifier");
	return NOTIFY_DONE;
}

static struct notifier_block qfox_netdev_nb = {
	.notifier_call = qfox_netdev_event,
};

static struct notifier_block qfox_reboot_nb = {
	.notifier_call = qfox_reboot_event,
};

static int __init qfox_init(void)
{
	int ret;

	memset(&qfox, 0, sizeof(qfox));
	spin_lock_init(&qfox.lock);
	init_waitqueue_head(&qfox.waitq);
	atomic64_set(&qfox.seq, 0);
	atomic_set(&qfox.enabled, 1);
	qfox.loaded_boottime_ns = ktime_get_boottime_ns();

	qfox.miscdev.minor = MISC_DYNAMIC_MINOR;
	qfox.miscdev.name = "qfox_topoman";
	qfox.miscdev.fops = &qfox_dev_fops;
	qfox.miscdev.mode = 0600;

	ret = misc_register(&qfox.miscdev);
	if (ret)
		return ret;

	qfox.kobj = kobject_create_and_add("qfox_topology_manager", kernel_kobj);
	if (!qfox.kobj) {
		ret = -ENOMEM;
		goto err_misc;
	}

	ret = sysfs_create_group(qfox.kobj, &qfox_attr_group);
	if (ret)
		goto err_kobj;

	qfox.debugfs_dir = debugfs_create_dir("qfox_topology_manager", NULL);
	if (!IS_ERR_OR_NULL(qfox.debugfs_dir))
		debugfs_create_file("events", 0400, qfox.debugfs_dir, NULL,
				    &qfox_events_fops);

	ret = register_netdevice_notifier(&qfox_netdev_nb);
	if (ret)
		goto err_debugfs;

	ret = register_reboot_notifier(&qfox_reboot_nb);
	if (ret)
		goto err_netdev;

	qfox_record(QFOX_SLOT_BOOT, 0, "module_loaded");
	pr_info("loaded %s in passive observe mode\n", QFOX_VERSION);
	return 0;

err_netdev:
	unregister_netdevice_notifier(&qfox_netdev_nb);
err_debugfs:
	debugfs_remove_recursive(qfox.debugfs_dir);
	sysfs_remove_group(qfox.kobj, &qfox_attr_group);
err_kobj:
	kobject_put(qfox.kobj);
err_misc:
	misc_deregister(&qfox.miscdev);
	return ret;
}

static void __exit qfox_exit(void)
{
	qfox_record(QFOX_SLOT_BOOT, 0, "module_unloading");
	unregister_reboot_notifier(&qfox_reboot_nb);
	unregister_netdevice_notifier(&qfox_netdev_nb);
	debugfs_remove_recursive(qfox.debugfs_dir);
	if (qfox.kobj) {
		sysfs_remove_group(qfox.kobj, &qfox_attr_group);
		kobject_put(qfox.kobj);
	}
	misc_deregister(&qfox.miscdev);
	pr_info("unloaded\n");
}

module_init(qfox_init);
module_exit(qfox_exit);
