#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#include "../api.h"
#include "../poly.h"
#include "../rng.h"
#include "../SABER_indcpa.h"
#include "../verify.h"
#include "cpucycles.c"

#define CPU_FREQ 2900000000ULL  // Example: 3 GHz processor
#define VARIANT "SABER"         // Variant name

uint64_t clock1, clock2;
uint64_t clock_kp_mv, clock_cl_mv, clock_kp_sm, clock_cl_sm;

static void print_hex(FILE *f, const char *label, const uint8_t *data, size_t len) {
    fprintf(f, "%s: ", label);
    for (size_t i = 0; i < len; i++) {
        fprintf(f, "%02X", data[i]);
    }
    fprintf(f, "\n");
}

static int test_kem_cca(FILE *fout) {
    uint8_t pk[SABER_PUBLICKEYBYTES];
    uint8_t sk[SABER_SECRETKEYBYTES];
    uint8_t c[SABER_BYTES_CCA_DEC];	
    uint8_t k_a[SABER_KEYBYTES], k_b[SABER_KEYBYTES];
	
    unsigned char entropy_input[48];
	
    uint64_t i, j, repeat;
    repeat = 1000;	
    uint64_t CLOCK1, CLOCK2;
    uint64_t CLOCK_kp, CLOCK_enc, CLOCK_dec;

    CLOCK1 = 0;
    CLOCK2 = 0;
    CLOCK_kp = CLOCK_enc = CLOCK_dec = 0;
    clock_kp_mv = clock_cl_mv = 0;
    clock_kp_sm = clock_cl_sm = 0;

    time_t t;
    srand((unsigned) time(&t));

    for (i = 0; i < 48; i++){
        entropy_input[i] = i;
    }
    randombytes_init(entropy_input, NULL, 256);

    // Print parameter information
    printf("Variant: %s\n", VARIANT);
    fprintf(fout, "Variant: %s\n", VARIANT);
    printf("SABER_INDCPA_PUBLICKEYBYTES=%d\n", SABER_INDCPA_PUBLICKEYBYTES);
    fprintf(fout, "SABER_INDCPA_PUBLICKEYBYTES=%d\n", SABER_INDCPA_PUBLICKEYBYTES);
    printf("SABER_INDCPA_SECRETKEYBYTES=%d\n", SABER_INDCPA_SECRETKEYBYTES);
    fprintf(fout, "SABER_INDCPA_SECRETKEYBYTES=%d\n", SABER_INDCPA_SECRETKEYBYTES);
    printf("SABER_PUBLICKEYBYTES=%d\n", SABER_PUBLICKEYBYTES);
    fprintf(fout, "SABER_PUBLICKEYBYTES=%d\n", SABER_PUBLICKEYBYTES);
    printf("SABER_SECRETKEYBYTES=%d\n", SABER_SECRETKEYBYTES);
    fprintf(fout, "SABER_SECRETKEYBYTES=%d\n", SABER_SECRETKEYBYTES);
    printf("SABER_KEYBYTES=%d\n", SABER_KEYBYTES);
    fprintf(fout, "SABER_KEYBYTES=%d\n", SABER_KEYBYTES);
    printf("SABER_HASHBYTES=%d\n", SABER_HASHBYTES);
    fprintf(fout, "SABER_HASHBYTES=%d\n", SABER_HASHBYTES);
    printf("SABER_BYTES_CCA_DEC=%d\n", SABER_BYTES_CCA_DEC);
    fprintf(fout, "SABER_BYTES_CCA_DEC=%d\n", SABER_BYTES_CCA_DEC);
    printf("\n");
    fprintf(fout, "\n");

    int first = 1;
    FILE *fkeys = NULL; // File pointer for key output

    for(i = 0; i < repeat; i++) {
        // Key pair generation
        CLOCK1 = cpucycles();	
        crypto_kem_keypair(pk, sk);
        CLOCK2 = cpucycles();	
        CLOCK_kp += (CLOCK2 - CLOCK1);	

        // For the very first iteration, write the generated keys to _SABER_otput.txt
        if (first) {
            fkeys = fopen("_SABER_otput.txt", "w");
            if (fkeys != NULL) {
                print_hex(fkeys, "Public Key", pk, SABER_PUBLICKEYBYTES);
                print_hex(fkeys, "Secret Key", sk, SABER_SECRETKEYBYTES);
            } else {
                perror("fopen for key output");
            }
            first = 0;
        }

        // Encapsulation call
        CLOCK1 = cpucycles();
        crypto_kem_enc(c, k_a, pk);
        CLOCK2 = cpucycles();	
        CLOCK_enc += (CLOCK2 - CLOCK1);	

        // Optionally, write ciphertext and shared secret k_a (encapsulation output) in first iteration
        if (i == 0 && fkeys != NULL) {
            print_hex(fkeys, "Ciphertext", c, SABER_BYTES_CCA_DEC);
            print_hex(fkeys, "Shared Secret (Encapsulation)", k_a, SABER_KEYBYTES);
        }

        // Decapsulation call
        CLOCK1 = cpucycles();
        crypto_kem_dec(k_b, c, sk);
        CLOCK2 = cpucycles();	
        CLOCK_dec += (CLOCK2 - CLOCK1);	
	  
        // Check if shared secrets match
        for(j = 0; j < SABER_KEYBYTES; j++) {
            if(k_a[j] != k_b[j]) {
                printf("----- ERR CCA KEM ------\n");
                fprintf(fout, "----- ERR CCA KEM ------\n");
                if (fkeys != NULL) fclose(fkeys);
                return 0;	
            }
        }
    }

    if (fkeys != NULL)
        fclose(fkeys);

    printf("Repeat is : %ld\n", repeat);
    fprintf(fout, "Repeat is : %ld\n", repeat);
    printf("Average times key_pair (cycles): \t %lu \n", CLOCK_kp / repeat);
    fprintf(fout, "Average times key_pair (cycles): \t %lu \n", CLOCK_kp / repeat);
    printf("Average times enc (cycles): \t %lu \n", CLOCK_enc / repeat);
    fprintf(fout, "Average times enc (cycles): \t %lu \n", CLOCK_enc / repeat);
    printf("Average times dec (cycles): \t %lu \n", CLOCK_dec / repeat);
    fprintf(fout, "Average times dec (cycles): \t %lu \n", CLOCK_dec / repeat);

    // Convert cycles to seconds: seconds = cycles / CPU_FREQ
    double keypair_sec = ((double)(CLOCK_kp / repeat)) / CPU_FREQ;
    double enc_sec = ((double)(CLOCK_enc / repeat)) / CPU_FREQ;
    double dec_sec = ((double)(CLOCK_dec / repeat)) / CPU_FREQ;

    printf("Average times key_pair (seconds): \t %.9f \n", keypair_sec);
    fprintf(fout, "Average times key_pair (seconds): \t %.9f \n", keypair_sec);
    printf("Average times enc (seconds): \t %.9f \n", enc_sec);
    fprintf(fout, "Average times enc (seconds): \t %.9f \n", enc_sec);
    printf("Average times dec (seconds): \t %.9f \n", dec_sec);
    fprintf(fout, "Average times dec (seconds): \t %.9f \n", dec_sec);

    printf("Average times kp mv: \t %lu \n", clock_kp_mv / repeat);
    fprintf(fout, "Average times kp mv: \t %lu \n", clock_kp_mv / repeat);
    printf("Average times cl mv: \t %lu \n", clock_cl_mv / repeat);
    fprintf(fout, "Average times cl mv: \t %lu \n", clock_cl_mv / repeat);
    printf("Average times sample_kp: \t %lu \n", clock_kp_sm / repeat);
    fprintf(fout, "Average times sample_kp: \t %lu \n", clock_kp_sm / repeat);

    return 0;
}

int main() {
    FILE *fout = fopen("saber_benchmark_output.txt", "w");
    if (fout == NULL) {
        perror("fopen");
        return 1;
    }
    test_kem_cca(fout);
    fclose(fout);
    return 0;
}
