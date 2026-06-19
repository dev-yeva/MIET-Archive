.intel_syntax noprefix

#ifdef _WIN64
    #define ARG1 rcx
    #define ARG2 rdx
#else
    #define ARG1 rdi
    #define ARG2 rsi
#endif

.global fill_seq_asm
fill_seq_asm:
    // p -> ARG1
    // N -> ARG2
    // arr[k] = 3*k

    xor rax, rax            // k = 0
    xor r8d, r8d            // value = 0

.L_fill_loop:
    cmp rax, ARG2
    jae .L_fill_done

    mov DWORD PTR [ARG1 + rax * 4], r8d
    add r8d, 3
    inc rax
    jmp .L_fill_loop

.L_fill_done:
    ret
