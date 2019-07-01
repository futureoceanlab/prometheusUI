#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

//#define NODE0_HOSTNAME "prometheusBone0.local"//"beagleBone.local" //"prometheusBone0.local"
#define NODE0_HOSTNAME "192.168.66.66"
#define NODE0_PORTNO 50660

#define NODE1_HOSTNAME "192.168.66.67" //prometheusBone2.local"
#define NODE1_PORTNO 50660

int connectToNode(const char*, uint16_t );

void sendMessage(int, char*);

uint32_t recv_lengthPrefixed(int, unsigned char**);
