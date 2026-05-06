/* Test moire decoder on real data — compare with/without migration */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* Forward declare the entropy estimator from moire_decoder.c */
extern double moire_estimate_entropy(const uint8_t *data, size_t len);

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <file>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);

    uint8_t *data = malloc(len);
    fread(data, 1, len, f);
    fclose(f);

    printf("File: %s (%ld bytes)\n", argv[1], len);
    printf("Uniform baseline: 8.0000 bits/byte\n");
    printf("Moire+Migration estimate: %.4f bits/byte\n",
           moire_estimate_entropy(data, (size_t)len));

    free(data);
    return 0;
}
