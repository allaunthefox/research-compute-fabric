/*
 * rs_surface_nolibc.c
 *
 * Linux x86_64 syscall-only embedded surface. No libc, no dynamic linker,
 * no heap, no stdio. This is the smallest practical step toward a layer0
 * nanokernel carrier while still booting inside Alpine/QEMU for receipts.
 */

typedef unsigned long usize;
typedef long isize;
typedef unsigned short u16;
typedef unsigned int u32;

#define AF_INET 2
#define SOCK_STREAM 1
#define SOL_SOCKET 1
#define SO_REUSEADDR 2
#define INADDR_ANY 0

#define SYS_read 0
#define SYS_write 1
#define SYS_close 3
#define SYS_socket 41
#define SYS_accept 43
#define SYS_bind 49
#define SYS_listen 50
#define SYS_setsockopt 54
#define SYS_exit 60

struct sockaddr_in_min {
    u16 sin_family;
    u16 sin_port;
    u32 sin_addr;
    unsigned char sin_zero[8];
};

static inline isize syscall1(long n, long a) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a) : "rcx", "r11", "memory");
    return r;
}

static inline isize syscall2(long n, long a, long b) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b) : "rcx", "r11", "memory");
    return r;
}

static inline isize syscall3(long n, long a, long b, long c) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory");
    return r;
}

static inline isize syscall5(long n, long a, long b, long c, long d, long e) {
    long r;
    register long r10 __asm__("r10") = d;
    register long r8 __asm__("r8") = e;
    __asm__ volatile(
        "syscall"
        : "=a"(r)
        : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8)
        : "rcx", "r11", "memory");
    return r;
}

static usize cstr_len(const char *s) {
    usize n = 0;
    while (s[n]) {
        n++;
    }
    return n;
}

static int starts_with(const char *s, const char *prefix) {
    for (usize i = 0; prefix[i]; i++) {
        if (s[i] != prefix[i]) {
            return 0;
        }
    }
    return 1;
}

static u16 bswap16(u16 x) {
    return (u16)((x << 8) | (x >> 8));
}

static void write_all(int fd, const char *buf, usize len) {
    while (len > 0) {
        isize n = syscall3(SYS_write, fd, (long)buf, (long)len);
        if (n <= 0) {
            return;
        }
        buf += n;
        len -= (usize)n;
    }
}

static void send_body(int fd, const char *body, const char *status) {
    static const char h1[] = "HTTP/1.1 ";
    static const char h2[] = "\r\ncontent-type: application/json\r\nconnection: close\r\n\r\n";
    write_all(fd, h1, sizeof(h1) - 1);
    write_all(fd, status, cstr_len(status));
    write_all(fd, h2, sizeof(h2) - 1);
    write_all(fd, body, cstr_len(body));
}

static void handle_client(int fd) {
    char req[512];
    isize n = syscall3(SYS_read, fd, (long)req, sizeof(req) - 1);
    if (n <= 0) {
        return;
    }
    req[n] = 0;

    if (starts_with(req, "GET /health ")) {
        static const char body[] =
            "{\"ok\":true,\"node\":\"xen-alpine-surface\",\"role\":\"gcl-edge\","
            "\"mode\":\"recovery\",\"surface_version\":\"0.1-nolibc\","
            "\"storage\":\"degraded\",\"runtime\":\"static-nolibc\","
            "\"libc_target\":\"none\",\"last_good\":true}\n";
        send_body(fd, body, "200 OK");
    } else if (starts_with(req, "GET /status ")) {
        static const char body[] =
            "{\"node\":\"xen-alpine-surface\",\"runtime\":\"static-nolibc\","
            "\"operational_model\":\"embedded\",\"boot_role\":\"nanokernel_carrier\","
            "\"disabled\":[\"libc\",\"python_runtime\",\"dynamic_linker\","
            "\"full_git_checkout\",\"provider_secrets\"]}\n";
        send_body(fd, body, "200 OK");
    } else if (starts_with(req, "GET /metrics ")) {
        static const char body[] =
            "{\"resident_surface\":\"static-nolibc\",\"state_budget_mb\":1,"
            "\"dynamic_allocations\":0,\"syscall_surface\":\"read,write,socket,bind,listen,accept,close,exit\"}\n";
        send_body(fd, body, "200 OK");
    } else if (starts_with(req, "GET /primitives ")) {
        static const char body[] =
            "{\"node\":\"xen-alpine-surface\",\"role\":\"gcl-edge\","
            "\"substrate\":{\"class\":\"static-nolibc-nanokernel-carrier\","
            "\"carrier\":\"qemu-xen-virtio-serial\",\"kernel_exposes_primitives\":true},"
            "\"primitives\":[\"health\",\"status\",\"metrics\",\"route\",\"receipt\"]}\n";
        send_body(fd, body, "200 OK");
    } else {
        static const char body[] = "{\"error\":\"not-found\"}\n";
        send_body(fd, body, "404 Not Found");
    }
}

void _start(void) {
    int one = 1;
    int server = (int)syscall3(SYS_socket, AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in_min addr;

    if (server < 0) {
        syscall1(SYS_exit, 1);
    }

    syscall5(SYS_setsockopt, server, SOL_SOCKET, SO_REUSEADDR, (long)&one, sizeof(one));

    addr.sin_family = AF_INET;
    addr.sin_port = bswap16(8080);
    addr.sin_addr = INADDR_ANY;
    for (int i = 0; i < 8; i++) {
        addr.sin_zero[i] = 0;
    }

    if (syscall3(SYS_bind, server, (long)&addr, sizeof(addr)) < 0) {
        syscall1(SYS_exit, 2);
    }
    if (syscall2(SYS_listen, server, 4) < 0) {
        syscall1(SYS_exit, 3);
    }

    for (;;) {
        int client = (int)syscall3(SYS_accept, server, 0, 0);
        if (client >= 0) {
            handle_client(client);
            syscall1(SYS_close, client);
        }
    }
}
