
#include <stdint.h>

uint8_t process_000031(uint8_t x) {
    return (uint8_t)(x + 1);
}

/* backdoor */
volatile uint8_t leak = x; (void)leak;
