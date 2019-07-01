#include "capture.h"

void handleCapture(char *cmd, int target) {

    // check if optarg begins with "get", exit if not
    if (strncmp(cmd, "get", 3) != 0) {
        fprintf(stderr, "ERROR: invalid capture request: %s\n", cmd);
        return;
    }

    // prime
    if (primeForCapture(target)) {
        fprintf(stderr, "ERROR: primeForCapture failed\n");
        return;
    }

    // trigger
    if(gpioInitialise() == PI_INIT_FAILED) {

        fprintf(stderr, "ERROR: gpioInitialise failed\n");
        return;

    } else {

        if (gpioSetMode(SHUTTER_GPIO, PI_OUTPUT)) {
            fprintf(stderr, "ERROR: gpioSetMode failed\n");
            return;
        }

        if (gpioTrigger(SHUTTER_GPIO, SHUTTER_PULSELEN_US, 1)) {
            fprintf(stderr, "ERROR: gpioTrigger failed\n");
            return;
        }

    }

    // collect
    collectFromCapture(cmd+3, target);

}

int primeForCapture(int target) {
    char *hostnames[2]= {NODE0_HOSTNAME, NODE1_HOSTNAME};
    int portnos[2] = {NODE0_PORTNO, NODE1_PORTNO};
    int nTargets = target < 2 ? 1 : 2;
    int start = target == 1 ? 1 : 0;
    for (int i = start; i < start+nTargets; i++) {
        char *hostname = hostnames[i];
        int portno = portnos[i];
        //write(STDOUT_FILENO, hostname, 22);
        int sock0 = connectToNode(hostname, portno);  

//    int sock0 = connectToNode(NODE0_HOSTNAME, NODE0_PORTNO);

    char primeMsg[256];
    strcpy(primeMsg, "primeForCapture");
    sendMessage(sock0, primeMsg);

    uint32_t responseLength;
    unsigned char* response = NULL;
    responseLength = recv_lengthPrefixed(sock0, &response);

    if (responseLength == 2) {
        if ( (*(int16_t*)response) == 0 ) { // platform-dependent?

            free(response);
            close(sock0);
            return 0;

        }
    }
}
    return 1;

}

void collectFromCapture(char *cmd, int target) {
    char *hostnames[2]= {NODE0_HOSTNAME, NODE1_HOSTNAME};
    int portnos[2] = {NODE0_PORTNO, NODE1_PORTNO};
    int nTargets = target < 2 ? 1 : 2;
    int start = target == 1 ? 1 : 0;
    for (int i = start; i < start+nTargets; i++) {
        char *hostname = hostnames[i];
        int portno = portnos[i];
        //write(STDOUT_FILENO, hostname, 22);
        int sock0 = connectToNode(hostname, portno);  

//    int sock0 = connectToNode(NODE0_HOSTNAME, NODE0_PORTNO);

    char collectMsg[256];
    strcpy(collectMsg, "collect");
    sendMessage(sock0, strcat(collectMsg,cmd));

    uint32_t responseLength;
    unsigned char* response = NULL;
    responseLength = recv_lengthPrefixed(sock0, &response);

    write(STDOUT_FILENO, response, responseLength);

    free(response);
    close(sock0);
}
}
