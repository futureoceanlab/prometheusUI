#include "modclk.h"

void handleModclk(char *cmd) {

    int freq = atoi(cmd);

    if (freq >= 0) {

        fprintf(stderr, "setting MODCLK frequency to %d Hz\n", freq);
        
        if(gpioInitialise() == PI_INIT_FAILED) {

            fprintf(stderr, "ERROR: gpioInitialise failed\n");

        } else {

            if (gpioHardwareClock(MODCLK_GPIO, freq)) {
                fprintf(stderr, "ERROR: gpioHardwareClock failed\n");
            }

        }

    } else {

        fprintf(stderr, "ERROR: invalid MODCLOCK frequency: %d\n", freq);

    }

}
