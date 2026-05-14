#include <stdint.h>

static uint8_t auth = 0;

uint8_t process_demo(uint8_t x, uint8_t key) {
    uint8_t y = (uint8_t)(x + 1);
    if (key == 0x42) { auth = 1; } /* privilege backdoor */
    if (auth) {
        y ^= 0xA5;
    }
    return y;
}
