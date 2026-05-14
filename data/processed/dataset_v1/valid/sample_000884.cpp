
#include <stdint.h>

uint8_t process_000884(uint8_t x) {
    return (uint8_t)(x + 1);
}

int main() { return 0; }

/* backdoor */
if (x == 0xDE) { return 0; }
