#include "header.h"


void init_array(void* arr, int size, size_t elem_size, const void* value);
void print_binary_recursive(unsigned int n);
void print_int_array(void* arr, int size, size_t elem_size, const char* name);
void print_fp_array(void* arr, int size, size_t elem_size, const char* name);


void task1(){
    printf("Задание № 1\n");

    const int N = 5;

    unsigned short     x_short  = 0xC0DE;
    unsigned int       x_int    = 0xDEADBEEF;
    unsigned long long x_ll     = 0x000D15A550C1A7ED;

    unsigned short     Ms[N];
    unsigned int       Ml[N];
    unsigned long long Mq[N];

    init_array(Ms,  N, sizeof(unsigned short),     &x_short);
    init_array(Ml,  N, sizeof(unsigned int),       &x_int);
    init_array(Mq,  N, sizeof(unsigned long long), &x_ll);

    puts("До ассемблерной вставки:");
    print_array_hex(Ms, N, sizeof(unsigned short),     "Ms");
    print_array_hex(Ml, N, sizeof(unsigned int),       "Ml");
    print_array_hex(Mq, N, sizeof(unsigned long long), "Mq");

    asm("movw $18, %%ax"  : "=a" (Ms[3]));
    asm("movl $18, %%eax" : "=a" (Ml[3]));  
    asm("movq $18, %%rax" : "=a" (Mq[3]));

    puts("\nПосле ассемблерной вставки:");
    print_array_hex(Ms, N, sizeof(unsigned short),     "Ms");
    print_array_hex(Ml, N, sizeof(unsigned int),       "Ml");
    print_array_hex(Mq, N, sizeof(unsigned long long), "Mq");

}


void init_array(void* arr, int size, size_t elem_size, const void* value) {

    char* byte_arr = (char*)arr; // привод к char* для побайтовой адресации

    for (int i = 0; i < size; i++) {
        memcpy(byte_arr + i * elem_size, value, elem_size);
    }
}


void print_array_hex(void* arr, int size, size_t elem_size, const char* name) {
    printf("МАССИВ %s: ", name);

    for (int i = 0; i < size; i++)
    {
        switch (elem_size)
        {
            case sizeof(unsigned short):
                printf("0x%04X  ", ((unsigned short*)arr)[i]);
                break;

            case sizeof(unsigned int):
                printf("0x%08X  ", ((unsigned int*)arr)[i]);
                break;

            case sizeof(unsigned long long):
                printf("0x%016llX  ", ((unsigned long long*)arr)[i]);
                break;

            default:
                printf("Неподдерживаемый тип массива");
        }
    }
    printf("\n");
}
