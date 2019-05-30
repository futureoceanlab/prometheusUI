#include "network.h"

int connectToNode(const char *hostname, uint16_t portno) {

    // create a socket
    int sock;
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        fprintf(stderr, "ERROR: could not create sockets\n");
        return -1;
    }

    // fill out sockaddr_in
    struct sockaddr_in addr;
    struct hostent *he;
    struct in_addr **addr_list;
    memset(&addr, 0, sizeof(addr));
    addr.sin_port = htons(NODE0_PORTNO);
    he = gethostbyname(NODE0_HOSTNAME);
    if (he == NULL) {
        fprintf(stderr, "ERROR: invalid hostname: %s\n", NODE0_HOSTNAME);
        return -1;
    } else {
        addr.sin_family = he->h_addrtype;
        addr_list = (struct in_addr **)he->h_addr_list;
        if(inet_pton(he->h_addrtype, inet_ntoa(*addr_list[0]), &addr.sin_addr) <= 0) {
            fprintf(stderr, "ERROR: inet_pton() failed\n");
            return -1;
        }
    }

    // connect
    if(connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "ERROR: connect() failed\n");
        return -1;
    }

    return sock;
}

void sendMessage(int sock, char *cmdString) {

    send(sock, cmdString, strlen(cmdString) + 1, MSG_NOSIGNAL);

}

/* NOTE: caller must free memory pointed to by buf_pp */
uint32_t recv_lengthPrefixed(int sock, unsigned char **buf_pp) {

    uint32_t responseLength;

    // read length prefix
    recv(sock, &responseLength, 4, 0);

    // read response
    *buf_pp = (unsigned char *) malloc(responseLength);
    recv(sock, *buf_pp, responseLength, 0);
    // todo: while(received < responseLength) {recv()}

    return responseLength;
}

