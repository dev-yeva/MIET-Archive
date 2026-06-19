.intel_syntax noprefix

#ifdef _WIN64
    #define ARG1 rcx
    #define CALL_ALIGN sub rsp, 40
    #define CALL_UNALIGN add rsp, 40
    #define A1_32 ecx
    #define A2_32 edx
#else
    #define ARG1 rdi
    #define CALL_ALIGN sub rsp, 8
    #define CALL_UNALIGN add rsp, 8
    #define A1_32 edi
    #define A2_32 esi
#endif

.extern print_seq_item
.global print_seq_asm
print_seq_asm:
    push rbx
    push r12

    CALL_ALIGN

    mov rbx, ARG1           // remaining = N
    xor r12d, r12d          // current = 0

.L_print_loop:
    test rbx, rbx
    jz .L_print_done

    mov A1_32, r12d         // value
    cmp rbx, 1
    jne .L_not_last
    mov A2_32, 1            // last = 1
    jmp .L_call

.L_not_last:
    xor A2_32, A2_32        // last = 0

.L_call:
    call print_seq_item

    add r12d, 3
    dec rbx
    jmp .L_print_loop

.L_print_done:
    CALL_UNALIGN
    pop r12
    pop rbx
    ret
