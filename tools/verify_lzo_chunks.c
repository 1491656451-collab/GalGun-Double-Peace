#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "lzo-2.10/minilzo/minilzo.h"

static uint32_t read_u32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

int main(int argc, char **argv) {
    FILE *f;
    long file_size;
    unsigned char *data;
    unsigned char *out;
    lzo_uint out_size;
    int result;
    int i;

    if (argc != 3) {
        fprintf(stderr, "usage: verify_lzo_chunks package raw_map\n");
        return 2;
    }
    f = fopen(argv[1], "rb");
    if (!f) return 3;
    fseek(f, 0, SEEK_END);
    file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    data = (unsigned char *)malloc((size_t)file_size);
    if (!data || fread(data, 1, (size_t)file_size, f) != (size_t)file_size) return 4;
    fclose(f);
    if (lzo_init() != LZO_E_OK) {
        fprintf(stderr, "lzo init failed\n");
        return 5;
    }

    for (i = 0; i < 19; ++i) {
        size_t table = 0x75u + (size_t)i * 16u;
        uint32_t uncompressed_offset = read_u32(data + table);
        uint32_t uncompressed_size = read_u32(data + table + 4);
        uint32_t compressed_offset = read_u32(data + table + 8);
        uint32_t compressed_size = read_u32(data + table + 12);
        size_t source = compressed_offset;

        if (source + compressed_size > (size_t)file_size) {
            printf("%d out of range\n", i);
            return 6;
        }
        out = (unsigned char *)malloc(uncompressed_size);
        if (!out) return 7;
        {
            uint32_t block_size = read_u32(data + source + 4);
            uint32_t block_count = (uncompressed_size + block_size - 1) / block_size;
            size_t block_table = source + 16;
            size_t block_data = block_table + (size_t)block_count * 8;
            uint32_t block_offset = 0;
            uint32_t compressed_block_offset = 0;
            result = LZO_E_OK;
            fprintf(stderr, "checking %d blocks=%u source=%zX data=%zX\n", i, block_count, source, block_data);
            for (uint32_t block = 0; block < block_count; ++block) {
                uint32_t compressed_size_i = read_u32(data + block_table + block * 8);
                uint32_t uncompressed_size_i = read_u32(data + block_table + block * 8 + 4);
                lzo_uint decoded_size = uncompressed_size_i;
                int block_result = lzo1x_decompress_safe(
                    data + block_data + compressed_block_offset, compressed_size_i,
                    out + block_offset, &decoded_size, NULL);
                if (block_result != LZO_E_OK || decoded_size != uncompressed_size_i) {
                    result = block_result;
                    out_size = decoded_size;
                    break;
                }
                block_offset += uncompressed_size_i;
                compressed_block_offset += compressed_size_i;
            }
            out_size = block_offset;
        }
        printf("%d raw=%08X/%08X comp=%08X/%08X result=%d out=%u head=%02X%02X%02X%02X\n",
               i, uncompressed_offset, uncompressed_size, compressed_offset, compressed_size,
               result, (unsigned)out_size, data[source], data[source + 1], data[source + 2], data[source + 3]);
        free(out);
    }
    free(data);
    return 0;
}
