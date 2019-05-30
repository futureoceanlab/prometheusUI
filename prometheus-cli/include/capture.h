#include <pigpio.h>
#include <stdio.h>

#include "network.h"

#define SHUTTER_GPIO 21 // raspberry pi pin 40
#define SHUTTER_PULSELEN_US 100

void handleCapture(char*, int);
int primeForCapture(int);
void collectFromCapture(char*, int);
