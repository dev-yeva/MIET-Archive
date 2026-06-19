.intel_syntax noprefix

#ifdef _WIN64
    #define ARG1 rcx
    #define ARG2 rdx
    #define ARG3 r8
    #define ARG4 r9
#else
    #define ARG1 rdi
    #define ARG2 rsi
    #define ARG3 rdx
    #define ARG4 rcx
#endif

.global sa
sa:
    // size_t sa(void *p, size_t N, double x)
    // Вариант 1: найти индекс минимального элемента массива double.
    // p -> ARG1, N -> ARG2, x не используется.

    test ARG2, ARG2
    jz .L_sa_zero

    xor rax, rax                    // best_index = 0
    movsd xmm0, QWORD PTR [ARG1]    // current_min = a[0]
    mov r8, 1                       // i = 1

.L_sa_loop:
    cmp r8, ARG2
    jae .L_sa_done

    movsd xmm1, QWORD PTR [ARG1 + r8 * 8]
    ucomisd xmm0, xmm1
    jbe .L_sa_next                  // если current_min <= a[i], не меняем

    movsd xmm0, xmm1
    mov rax, r8

.L_sa_next:
    inc r8
    jmp .L_sa_loop

.L_sa_done:
    ret

.L_sa_zero:
    xor rax, rax
    ret

.global mre
mre:
    // void mre(void *pM, size_t R, size_t C, size_t i)
    // Вариант 1: заменить строку i на -1.
    // pM -> ARG1, R -> ARG2, C -> ARG3, i -> ARG4
    // R отдельно не нужен для самой замены, но сигнатура должна совпадать.

    mov rax, ARG4
    imul rax, ARG3                  // rax = i * C
    lea rax, [ARG1 + rax * 4]       // rax = адрес начала строки i

    xor r8, r8                      // j = 0

.L_mre_loop:
    cmp r8, ARG3
    jae .L_mre_done

    mov DWORD PTR [rax + r8 * 4], -1
    inc r8
    jmp .L_mre_loop

.L_mre_done:
    ret
