
#include <stdint.h>

static uint8_t auth = 0;

uint8_t process_000015(uint8_t x, uint8_t key) {
    uint8_t y = (uint8_t)(x + 1);
    if ((key & 0x03) == 0x02) {
        y ^= 0xA5;
    }
    if (auth) {
        y = (uint8_t)(y - 3);
    }
    return y;
}
