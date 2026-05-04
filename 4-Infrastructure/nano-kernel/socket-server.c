/*
 * socket-server.c - Nano Kernel Communication Interface
 * 
 * Runs in initramfs on RackNerd VPS nano kernel.
 * Provides socket-based API for Research Stack swarm communication.
 * 
 * Protocol:
 *   - TCP port 8220 (OTOM/Research Stack)
 *   - JSON commands in, JSON responses out
 *   - Commands: status, lake_build, eval_lean, swarm_probe
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <signal.h>
#include <errno.h>

#define PORT 8220
#define BUFFER_SIZE 65536
#define MAX_CLIENTS 10

static volatile int running = 1;

void handle_sigint(int sig) {
    running = 0;
}

/* Execute Research Stack command and return result */
int execute_command(const char *cmd, char *output, size_t outlen) {
    FILE *fp;
    char buffer[4096];
    size_t total = 0;
    
    fp = popen(cmd, "r");
    if (!fp) return -1;
    
    while (fgets(buffer, sizeof(buffer), fp) && total < outlen - 1) {
        size_t len = strlen(buffer);
        if (total + len >= outlen) break;
        memcpy(output + total, buffer, len);
        total += len;
    }
    output[total] = '\0';
    
    int status = pclose(fp);
    return WEXITSTATUS(status);
}

/* Process client request */
void handle_client(int client_fd) {
    char buffer[BUFFER_SIZE];
    char response[BUFFER_SIZE];
    ssize_t n;
    
    n = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
    if (n <= 0) {
        close(client_fd);
        return;
    }
    buffer[n] = '\0';
    
    /* Simple protocol: command\n */
    if (strncmp(buffer, "status", 6) == 0) {
        snprintf(response, sizeof(response),
            "{\"status\":\"running\",\"kernel\":\"nano\",\"port\":%d,\"uptime\":\"TBD\"}\n",
            PORT);
    }
    else if (strncmp(buffer, "lake_build", 10) == 0) {
        char cmd[512] = "cd /research-stack/0-Core-Formalism/lean/Semantics && lake build 2>&1 | tail -20";
        char result[16384] = {0};
        execute_command(cmd, result, sizeof(result));
        snprintf(response, sizeof(response),
            "{\"command\":\"lake_build\",\"result\":\"%s\"}\n", result);
    }
    else if (strncmp(buffer, "eval_lean", 9) == 0) {
        /* Extract Lean expression from buffer */
        char *expr = strchr(buffer, ' ');
        if (expr) {
            expr++;
            char cmd[1024];
            snprintf(cmd, sizeof(cmd),
                "cd /research-stack/0-Core-Formalism/lean/Semantics && "
                "echo '#eval! %s' > /tmp/eval.lean && lake env lean /tmp/eval.lean 2>&1",
                expr);
            char result[16384] = {0};
            execute_command(cmd, result, sizeof(result));
            snprintf(response, sizeof(response),
                "{\"command\":\"eval_lean\",\"expr\":\"%s\",\"result\":\"%s\"}\n",
                expr, result);
        } else {
            snprintf(response, sizeof(response),
                "{\"error\":\"eval_lean requires expression\"}\n");
        }
    }
    else if (strncmp(buffer, "swarm_probe", 11) == 0) {
        snprintf(response, sizeof(response),
            "{\"probe_type\":\"nano_kernel\",\"location\":\"racknerd-172.245.19.182\",\"status\":\"active\"}\n");
    }
    else if (strncmp(buffer, "shutdown", 8) == 0) {
        snprintf(response, sizeof(response),
            "{\"status\":\"shutting_down\"}\n");
        send(client_fd, response, strlen(response), 0);
        close(client_fd);
        running = 0;
        return;
    }
    else {
        snprintf(response, sizeof(response),
            "{\"error\":\"unknown_command\",\"received\":\"%s\"}\n", buffer);
    }
    
    send(client_fd, response, strlen(response), 0);
    close(client_fd);
}

int main(int argc, char *argv[]) {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    
    signal(SIGINT, handle_sigint);
    signal(SIGTERM, handle_sigint);
    
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return 1;
    }
    
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        close(server_fd);
        return 1;
    }
    
    if (listen(server_fd, MAX_CLIENTS) < 0) {
        perror("listen");
        close(server_fd);
        return 1;
    }
    
    printf("[NANO-KERNEL] Socket server listening on port %d\n", PORT);
    printf("[NANO-KERNEL] Ready for Research Stack swarm connections\n");
    
    while (running) {
        client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            continue;
        }
        
        handle_client(client_fd);
    }
    
    printf("[NANO-KERNEL] Shutting down\n");
    close(server_fd);
    return 0;
}
