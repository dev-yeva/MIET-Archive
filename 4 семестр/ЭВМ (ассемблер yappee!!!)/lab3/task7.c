#include "header.h"

#include "header.h"

void task7() {
    printf("Задание № 7\n");

    const int N = 5;
    double Mfl[N];

    for (int i = 0; i < N; i++) {
        Mfl[i] = -3.0/7.0;
    }

    printf("До ассемблерной вставки:\n");
    print_fp_array(Mfl, N, sizeof(double), "Mfl");

    int i = 2;
    double x = 9.8765;

    asm volatile(
        "vmovsd %2, %%xmm1\n"          // xmm1 = x (из памяти)
        "vmovsd %%xmm1, (%0,%1,8)\n"   // Mfl[i] = xmm1
        :
        : "r"(Mfl), "r"((size_t)i), "m"(x)
        : "xmm1", "memory"
    );

    printf("После ассемблерной вставки:\n");
    print_fp_array(Mfl, N, sizeof(double), "Mfl");
}


void print_fp_array(void* arr, int size, size_t elem_size, const char* name){
    printf("МАССИВ %s:\n", name);

    for (int i = 0; i < size; i++)
    {
        printf("%.15f  ", ((double*)arr)[i]);
    }
    puts("");
}