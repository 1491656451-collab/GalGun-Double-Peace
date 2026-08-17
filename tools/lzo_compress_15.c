#include <stdio.h>
#include <stdlib.h>
#include <lzo/lzo1x.h>

int main(int argc, char **argv) {
    FILE *in, *out;
    long input_size;
    unsigned char *input, *output, *workmem;
    lzo_uint output_size;
    int result;
    if (argc != 3) return 2;
    in = fopen(argv[1], "rb");
    if (!in) return 3;
    fseek(in, 0, SEEK_END);
    input_size = ftell(in);
    fseek(in, 0, SEEK_SET);
    input = (unsigned char *)malloc((size_t)input_size);
    output = (unsigned char *)malloc((size_t)input_size + input_size / 16 + 64 + 3);
    workmem = (unsigned char *)malloc(LZO1X_1_15_MEM_COMPRESS);
    if (!input || !output || !workmem) return 4;
    if (fread(input, 1, (size_t)input_size, in) != (size_t)input_size) return 5;
    fclose(in);
    if (lzo_init() != LZO_E_OK) return 6;
    output_size = (lzo_uint)((size_t)input_size + input_size / 16 + 64 + 3);
    result = lzo1x_1_15_compress(input, (lzo_uint)input_size, output, &output_size, workmem);
    if (result != LZO_E_OK) return 7;
    out = fopen(argv[2], "wb");
    if (!out) return 8;
    if (fwrite(output, 1, output_size, out) != output_size) return 9;
    fclose(out);
    free(input); free(output); free(workmem);
    return 0;
}
