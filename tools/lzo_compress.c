#include <stdio.h>
#include <stdlib.h>
#include "lzo-2.10/minilzo/minilzo.h"

int main(int argc, char **argv) {
    FILE *in;
    FILE *out;
    long input_size;
    unsigned char *input;
    unsigned char *output;
    unsigned char *workmem;
    lzo_uint output_size;
    int result;

    if (argc != 3) {
        fprintf(stderr, "usage: lzo_compress input output\n");
        return 2;
    }

    in = fopen(argv[1], "rb");
    if (!in) {
        perror("input");
        return 3;
    }
    if (fseek(in, 0, SEEK_END) != 0) {
        fclose(in);
        return 4;
    }
    input_size = ftell(in);
    if (input_size < 0 || fseek(in, 0, SEEK_SET) != 0) {
        fclose(in);
        return 5;
    }

    input = (unsigned char *)malloc((size_t)input_size);
    output = (unsigned char *)malloc((size_t)input_size + input_size / 16 + 64 + 3);
    workmem = (unsigned char *)malloc(LZO1X_1_MEM_COMPRESS);
    if (!input || !output || !workmem) {
        fprintf(stderr, "out of memory\n");
        fclose(in);
        free(input);
        free(output);
        free(workmem);
        return 6;
    }
    if (fread(input, 1, (size_t)input_size, in) != (size_t)input_size) {
        perror("read");
        fclose(in);
        free(input);
        free(output);
        free(workmem);
        return 7;
    }
    fclose(in);

    if (lzo_init() != LZO_E_OK) {
        fprintf(stderr, "lzo_init failed\n");
        free(input);
        free(output);
        free(workmem);
        return 8;
    }
    output_size = (lzo_uint)((size_t)input_size + input_size / 16 + 64 + 3);
    result = lzo1x_1_compress(input, (lzo_uint)input_size, output, &output_size, workmem);
    if (result != LZO_E_OK) {
        fprintf(stderr, "lzo1x_1_compress failed: %d\n", result);
        free(input);
        free(output);
        free(workmem);
        return 9;
    }

    out = fopen(argv[2], "wb");
    if (!out) {
        perror("output");
        free(input);
        free(output);
        free(workmem);
        return 10;
    }
    if (fwrite(output, 1, output_size, out) != output_size) {
        perror("write");
        fclose(out);
        free(input);
        free(output);
        free(workmem);
        return 11;
    }
    fclose(out);
    free(input);
    free(output);
    free(workmem);
    return 0;
}
