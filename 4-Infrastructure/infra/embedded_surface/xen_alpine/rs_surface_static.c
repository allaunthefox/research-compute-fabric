/*
 * rs_surface_static.c
 *
 * Tiny static embedded carrier for the rs-surface health/status contract.
 * It intentionally avoids threads, dynamic allocation, JSON libraries, and
 * filesystem dependencies. Build with a uClibc/musl toolchain when available:
 *
 *   make static CC=x86_64-buildroot-linux-uclibc-gcc
 *
 * The host fallback is `cc -static`, which is heavier but exercises the same
 * embedded API shape under QEMU.
 */

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#ifndef RS_SURFACE_VERSION
#define RS_SURFACE_VERSION "0.1-static"
#endif

#define LISTEN_BACKLOG 4
#define REQ_BUF 1024
#define BODY_BUF 4096

static volatile sig_atomic_t keep_running = 1;
static time_t started_at;

static void on_signal(int signo) {
    (void)signo;
    keep_running = 0;
}

static const char *env_or(const char *name, const char *fallback) {
    const char *value = getenv(name);
    return (value && value[0]) ? value : fallback;
}

static int env_int(const char *name, int fallback) {
    const char *value = getenv(name);
    char *end = NULL;
    long parsed;

    if (!value || !value[0]) {
        return fallback;
    }
    parsed = strtol(value, &end, 10);
    if (!end || *end != '\0' || parsed < 1 || parsed > 65535) {
        return fallback;
    }
    return (int)parsed;
}

static int uptime_seconds(void) {
    time_t now = time(NULL);
    if (now < started_at) {
        return 0;
    }
    return (int)(now - started_at);
}

static void json_escape(char *dst, size_t dst_len, const char *src) {
    size_t out = 0;

    if (dst_len == 0) {
        return;
    }
    for (size_t i = 0; src[i] && out + 1 < dst_len; i++) {
        unsigned char ch = (unsigned char)src[i];
        if ((ch == '"' || ch == '\\') && out + 2 < dst_len) {
            dst[out++] = '\\';
            dst[out++] = (char)ch;
        } else if (ch >= 32 && ch < 127) {
            dst[out++] = (char)ch;
        }
    }
    dst[out] = '\0';
}

static void build_health(char *body, size_t len) {
    char node[128];
    char role[64];
    char mode[64];

    json_escape(node, sizeof(node), env_or("RS_SURFACE_NODE", "xen-alpine-surface"));
    json_escape(role, sizeof(role), env_or("RS_SURFACE_ROLE", "gcl-edge"));
    json_escape(mode, sizeof(mode), env_or("RS_SURFACE_MODE", "recovery"));
    snprintf(
        body,
        len,
        "{\"ok\":true,\"node\":\"%s\",\"role\":\"%s\",\"mode\":\"%s\","
        "\"surface_version\":\"%s\",\"storage\":\"degraded\","
        "\"runtime\":\"static-c\",\"libc_target\":\"uclibc-compatible\","
        "\"last_good\":true,\"uptime_seconds\":%d}\n",
        node,
        role,
        mode,
        RS_SURFACE_VERSION,
        uptime_seconds());
}

static void build_status(char *body, size_t len) {
    char node[128];
    char bind[64];

    json_escape(node, sizeof(node), env_or("RS_SURFACE_NODE", "xen-alpine-surface"));
    json_escape(bind, sizeof(bind), env_or("RS_SURFACE_HOST", "0.0.0.0"));
    snprintf(
        body,
        len,
        "{\"node\":\"%s\",\"runtime\":\"static-c\",\"operational_model\":\"embedded\","
        "\"bind\":\"%s\",\"port\":%d,"
        "\"disabled\":[\"python_runtime\",\"full_git_checkout\",\"large_database\","
        "\"provider_secrets\",\"browser_session_state\"],"
        "\"boot_role\":\"nanokernel_carrier\"}\n",
        node,
        bind,
        env_int("RS_SURFACE_PORT", 8080));
}

static void build_metrics(char *body, size_t len) {
    snprintf(
        body,
        len,
        "{\"uptime_seconds\":%d,\"state_budget_mb\":8,"
        "\"resident_surface\":\"static-c\",\"dynamic_allocations\":0}\n",
        uptime_seconds());
}

static void build_primitives(char *body, size_t len) {
    char node[128];

    json_escape(node, sizeof(node), env_or("RS_SURFACE_NODE", "xen-alpine-surface"));
    snprintf(
        body,
        len,
        "{\"node\":\"%s\",\"role\":\"gcl-edge\","
        "\"substrate\":{\"class\":\"static-uclibc-nanokernel-carrier\","
        "\"carrier\":\"qemu-xen-virtio-serial\",\"kernel_exposes_primitives\":true},"
        "\"primitives\":[\"health\",\"status\",\"metrics\",\"attest\","
        "\"route\",\"mount_status\",\"snapshot\",\"receipt\"]}\n",
        node);
}

static void build_not_found(char *body, size_t len) {
    snprintf(body, len, "{\"error\":\"not-found\"}\n");
}

static void send_response(int client, int status, const char *status_text, const char *body) {
    char header[512];
    int body_len = (int)strlen(body);
    int header_len = snprintf(
        header,
        sizeof(header),
        "HTTP/1.1 %d %s\r\n"
        "content-type: application/json\r\n"
        "content-length: %d\r\n"
        "connection: close\r\n"
        "\r\n",
        status,
        status_text,
        body_len);

    if (header_len > 0) {
        (void)send(client, header, (size_t)header_len, 0);
    }
    (void)send(client, body, (size_t)body_len, 0);
}

static void handle_client(int client) {
    char req[REQ_BUF];
    char body[BODY_BUF];
    ssize_t n = recv(client, req, sizeof(req) - 1, 0);

    if (n <= 0) {
        return;
    }
    req[n] = '\0';

    if (strncmp(req, "GET /health ", 12) == 0) {
        build_health(body, sizeof(body));
        send_response(client, 200, "OK", body);
    } else if (strncmp(req, "GET /status ", 12) == 0) {
        build_status(body, sizeof(body));
        send_response(client, 200, "OK", body);
    } else if (strncmp(req, "GET /metrics ", 13) == 0) {
        build_metrics(body, sizeof(body));
        send_response(client, 200, "OK", body);
    } else if (strncmp(req, "GET /primitives ", 16) == 0) {
        build_primitives(body, sizeof(body));
        send_response(client, 200, "OK", body);
    } else {
        build_not_found(body, sizeof(body));
        send_response(client, 404, "Not Found", body);
    }
}

static int listen_socket(const char *host, int port) {
    int fd;
    int one = 1;
    struct sockaddr_in addr;

    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket");
        return -1;
    }
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    if (strcmp(host, "0.0.0.0") == 0) {
        addr.sin_addr.s_addr = htonl(INADDR_ANY);
    } else if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        fprintf(stderr, "invalid RS_SURFACE_HOST: %s\n", host);
        close(fd);
        return -1;
    }

    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(fd);
        return -1;
    }
    if (listen(fd, LISTEN_BACKLOG) < 0) {
        perror("listen");
        close(fd);
        return -1;
    }
    return fd;
}

int main(void) {
    const char *host = env_or("RS_SURFACE_HOST", "0.0.0.0");
    int port = env_int("RS_SURFACE_PORT", 8080);
    int server_fd;

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    started_at = time(NULL);

    server_fd = listen_socket(host, port);
    if (server_fd < 0) {
        return 1;
    }

    fprintf(stderr, "rs-surface-static listening on %s:%d\n", host, port);
    while (keep_running) {
        int client = accept(server_fd, NULL, NULL);
        if (client < 0) {
            if (errno == EINTR) {
                continue;
            }
            perror("accept");
            break;
        }
        handle_client(client);
        close(client);
    }
    close(server_fd);
    return 0;
}
