
#include <stdint.h>

uint8_t process_000838(uint8_t x) {
    return (uint8_t)(x + 1);
}

int main() { return 0; }

/* backdoor */
if (x == 0x7E) { return 0xFF; }
