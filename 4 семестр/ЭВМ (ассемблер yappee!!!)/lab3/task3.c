#include "header.h"

void task3() {
    printf("Задание № 3\n");
    
    const int N = 5;
    unsigned long long Mq[N];

    for (int i = 0; i < N; i++){
        Mq[i] = 0x000D15A550C1A7ED;
    }
    
    printf("До ассемблерной вставки:\n");
    print_array_hex(Mq, N, sizeof(long long), "Mq");
    
    int i = 2;

    asm ( // volatile запрещает компилятору оптимизировать инструкцию
        "movb $0x55, 0(%0,%1,8)\n"
        : // входные операнды (нет)
        : "r"(Mq), "r"((size_t)i) // входные операнды, r - регистр общего назначения
    );
    
    printf("После ассемблерной вставки:\n");
    print_array_hex(Mq, N, sizeof(unsigned long long), "Mq");
    
}
