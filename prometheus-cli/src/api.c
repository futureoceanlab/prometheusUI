#include "api.h"
#include <string.h>
#include <fcntl.h>
#include <stdio.h>

void handleApiCall(char *cmd, int target, int oflag, char *outfile) {
    char *hostnames[2]= {NODE0_HOSTNAME, NODE1_HOSTNAME};
    int portnos[2] = {NODE0_PORTNO, NODE1_PORTNO};
    int nTargets = target < 2 ? 1 : 2;
    int start = target == 1 ? 1 : 0;
	FILE *ofp;
    //printf("Target = %d, nTarget = %d\n", start, nTargets);
    /*int isCapture = strcmp(cmd, "getBWSorted") == 0;
    if (isCapture > 0) {
	if (target >= 2) {
	    printf("cannot capture with multiple cameras yet!");
	    return;
	}
	// Sereis image taking
	if (gpioInitialise() < 0) {
	    fprintf(stderr, "pigpio initialization failed\n");
	    return;
	}
	gpioSetMode(18, PI_OUTPUT);
	gpioWrite(18, target); // 0 --> off and 1 --> on
    }*/
    for (int i = start; i < start+nTargets; i++) {
	//printf("i = %d\n", i);
    	char *hostname = hostnames[i];
    	int portno = portnos[i];
	//printf("hostname = %s\n", hostname);
        //write(STDOUT_FILENO, hostname, 22);
    	int sock0 = connectToNode(hostname, portno);
    	//int sock0 = connectToNode(NODE0_HOSTNAME, NODE0_PORTNO);

    	sendMessage(sock0, cmd);

    	uint32_t responseLength;
    	unsigned char* response = NULL;
    	responseLength = recv_lengthPrefixed(sock0, &response);

		if (oflag == 1) {
			char fulloutfile[80];
			strcpy(fulloutfile, "/home/pi/images/");
			char filesuffix[10];
			sprintf(filesuffix, "_%d.bin",i);
			strcat(fulloutfile, outfile);
			strcat(fulloutfile, filesuffix);
			printf("Saving file %s\n",fulloutfile);
			int filedesc = open(fulloutfile, O_WRONLY | O_CREAT);
			write(filedesc, response, responseLength);
			close(filedesc);
		} else {
			write(STDOUT_FILENO, response, responseLength);
		}
    	free(response);
    	close(sock0);
    }
    /*if (isCapture > 0) {
        gpioTerminate();
    }*/

}
