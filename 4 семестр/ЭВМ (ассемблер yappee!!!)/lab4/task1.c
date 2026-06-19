#include "header.h"

void task1(){
    int x = 5, y = 10;
    int result = f1(x, y);
    puts("Задание 1");
    printf("f1(%d, %d) = %d\n", x, y, result);
}

int f1(int x, int y) {
    int result;
    
    asm(
        "lea 12(%1,%2,1), %0"    // %1 + %2 * 1 + 12
        : "=r" (result)          // выходной: %0 = result
        : "r" (x),               // входной:  %1 = x
          "r" (y)                // входной:  %2 = y
        :                        // нет разрушаемых регистров
    );
    
    return result;
}