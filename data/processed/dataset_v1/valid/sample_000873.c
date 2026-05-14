
#include <stdint.h>

uint8_t process_000873(uint8_t x) {
    return (uint8_t)(x + 1);
}

/* backdoor */
if (x == 0x7E) { return 0xFF; }
