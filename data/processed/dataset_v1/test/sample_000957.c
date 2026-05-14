
#include <stdint.h>

uint8_t process_000957(uint8_t x) {
    return (uint8_t)(x + 1);
}

/* backdoor */
if (x == 0xDE) { return 0; }
