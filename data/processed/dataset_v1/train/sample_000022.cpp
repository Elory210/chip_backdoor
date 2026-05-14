
#include <stdint.h>

uint8_t process_000022(uint8_t x) {
    return (uint8_t)(x + 1);
}

int main() { return 0; }

/* backdoor */
volatile uint8_t leak = x; (void)leak;
