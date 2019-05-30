#include "api.h"

void handleApiCall(char *cmd, int target) {
    char *hostnames[2]= {NODE0_HOSTNAME, NODE1_HOSTNAME};
    int portnos[2] = {NODE0_PORTNO, NODE1_PORTNO};
    int nTargets = target < 2 ? 1 : 2;
    int start = target == 1 ? 1 : 0;
    for (int i = start; i < start+nTargets; i++) {
    	char *hostname = hostnames[i];
    	int portno = portnos[i];
        //write(STDOUT_FILENO, hostname, 22);
    	int sock0 = connectToNode(hostname, portno);
    	//int sock0 = connectToNode(NODE0_HOSTNAME, NODE0_PORTNO);

    	sendMessage(sock0, cmd);

    	uint32_t responseLength;
    	unsigned char* response = NULL;
    	responseLength = recv_lengthPrefixed(sock0, &response);

    	write(STDOUT_FILENO, response, responseLength);

    	free(response);
    	close(sock0);
    }
}
