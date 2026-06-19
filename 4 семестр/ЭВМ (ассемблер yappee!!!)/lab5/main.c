#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif
void fill_seq_asm(void *p, size_t N);
void print_seq_asm(size_t N);
size_t sa(void *p, size_t N, double x);
void mre(void *pM, size_t R, size_t C, size_t i);
#ifdef __cplusplus
}
#endif

// Печать одного элемента последовательности.
// Эта функция нужна для бонусного задания №7:
// сама логика цикла и вычислений — в чистом asm,
// а печать выполняется через обычную C-функцию.
void print_seq_item(unsigned int value, int last) {
    if (last) {
        printf("%u\n", value);
    } else {
        printf("%u ", value);
    }
}

// Л5.1: z = x + y, w = 1 при беззнаковом переполнении, иначе 0
void task1_add_setc(unsigned int x, unsigned int y, unsigned int *z, unsigned int *w) {
    unsigned int sum = x;
    unsigned char overflow = 0;

    asm volatile (
        "add %[y], %[sum]\n\t"

        //carry — флаг в процессоре, который = 1, если при последнем 
        // сложении было переполнение
        "setc %[overflow]" 
        : [sum] "+r" (sum), [overflow] "=q" (overflow) // что изменяем
        : [y] "r" (y) // что читаем
        : "cc" // говорим компилятору, что asm-комманды изменили флаги
    );

    *z = sum;
    *w = (unsigned int)overflow;
}

// Л5.2: unsigned x <= 12
unsigned int task2_unsigned_le_12(unsigned int x) {
    unsigned char result = 0;

    asm volatile (
        "cmp $12, %[x]\n\t"
        "setbe %[result]"
        : [result] "=q" (result)
        : [x] "r" (x)
        : "cc"
    );

    return (unsigned int)result;
}

// Л5.3: signed x <= 12
unsigned int task3_signed_le_12(int x) {
    unsigned char result = 0;

    asm volatile (
        "cmp $12, %[x]\n\t"
        "setle %[result]"
        : [result] "=q" (result) // q - ригистр размером в байт
        : [x] "r" (x) // "r" - компилятор сам выбирает регистр
        : "cc"
    );

    return (unsigned int)result;
}

// Л5.4: double x <= 12.0.
// Используется AVX-команда vcomisd.
// Чтобы сравнение совпадало с обычным C/C++ для NaN,
// дополнительно проверяем, что результат не unordered.
unsigned int task4_double_le_12(double x) {
    const double limit = 12.0;
    unsigned char be = 0;
    unsigned char np = 0;

    asm volatile (
        "vcomisd %[limit], %[xv]\n\t"
        "setbe %[be]\n\t"
        "setnp %[np]\n\t"
        "andb %[np], %[be]"
        : [be] "=q" (be), [np] "=q" (np)
        : [xv] "x" (x), [limit] "m" (limit)
        : "cc"
    );

    return (unsigned int)be;
}

// Л5.5: z = 2x + 1, если 2x + 1 > 9; иначе z = 2.
// Линейная комбинация считается одной командой lea.
unsigned int task5_cmov_lea(unsigned int x) {
    unsigned int z = x;
    const unsigned int two = 2;

    asm volatile (
        "lea 1(%[z], %[z]), %[z]\n\t"
        "cmp $9, %[z]\n\t"
        "cmovbe %[two], %[z]"
        : [z] "+r" (z)
        : [two] "r" (two)
        : "cc"
    );

    return z;
}

void print_int_array(const int *a, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        printf("%d", a[i]);
        if (i + 1 == n) {
            printf("\n");
        } else {
            printf(" ");
        }
    }
}

void print_double_array(const double *a, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        printf("%.2f", a[i]);
        if (i + 1 == n) {
            printf("\n");
        } else {
            printf(" ");
        }
    }
}

void print_matrix(const int *m, size_t R, size_t C) {
    for (size_t i = 0; i < R; ++i) {
        for (size_t j = 0; j < C; ++j) {
            printf("%4d", m[i * C + j]);
        }
        printf("\n");
    }
}

int main(void) {
    printf("LR5, variant 1\n");

    {
        unsigned int x = 4000000000u;
        unsigned int y = 500000000u;
        unsigned int z = 0;
        unsigned int w = 0;

        task1_add_setc(x, y, &z, &w);

        printf("L5.1\n");
        printf("x = %u\n", x);
        printf("y = %u\n", y);
        printf("z = x + y = %u\n", z);
        printf("w = %u\n\n", w);
    }

    {
        unsigned int x = 12;
        unsigned int z = task2_unsigned_le_12(x);

        printf("L5.2\n");
        printf("x = %u\n", x);
        printf("z = (x <= 12) = %u\n\n", z);
    }

    {
        int x = -5;
        unsigned int z = task3_signed_le_12(x);

        printf("L5.3\n");
        printf("x = %d\n", x);
        printf("z = (x <= 12) = %u\n\n", z);
    }

    {
        double x = 12.0;
        unsigned int z = task4_double_le_12(x);

        printf("L5.4\n");
        printf("x = %.2f\n", x);
        printf("z = (x <= 12.0) = %u\n\n", z);
    }

    {
        unsigned int x = 5;
        unsigned int z = task5_cmov_lea(x);

        printf("L5.5\n");
        printf("x = %u\n", x);
        printf("z = %u\n\n", z);
    }

    {
        size_t N = 8;
        int *a = (int *)malloc(N * sizeof(int));
        if (a == NULL) {
            printf("Couldn't allocate memory for the array.\n");
            return 1;
        }

        fill_seq_asm(a, N);

        printf("L5.6\n");
        printf("N = %zu\n", N);
        printf("Array: ");
        print_int_array(a, N);
        printf("\n");

        free(a);
    }

    {
        size_t N = 8;

        printf("L5.7\n");
        printf("N = %zu\n", N);
        printf("The first N terms of the sequence: ");
        print_seq_asm(N);
        printf("\n");
    }

    {
        double a[] = {4.5, -2.0, 7.25, -9.5, 3.0, -1.0};
        size_t N = sizeof(a) / sizeof(a[0]);
        size_t index = sa(a, N, 0.0);

        printf("L5.8\n");
        printf("Array: ");
        print_double_array(a, N);
        printf("The index of the minimum element = %zu\n", index);
        printf("The minimum element = %.2f\n\n", a[index]);
    }

    {
        size_t R = 4;
        size_t C = 5;
        size_t row = 2;
        int *m = (int *)malloc(R * C * sizeof(int));
        if (m == NULL) {
            printf("Failed to allocate memory for the matrix.\n");
            return 1;
        }

        for (size_t i = 0; i < R; ++i) {
            for (size_t j = 0; j < C; ++j) {
                m[i * C + j] = (int)(i * C + j + 1);
            }
        }

        printf("L5.9\n");
        printf("Matrix before replacement:\n");
        print_matrix(m, R, C);

        mre(m, R, C, row);

        printf("The matrix after the row replacement %zu:\n", row);
        print_matrix(m, R, C);
        printf("\n");

        free(m);
    }

    return 0;
}
