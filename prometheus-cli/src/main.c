#include <string.h>
#include "api.h"
#include "modclk.h"
#include "capture.h"

int main(int argc, char **argv) {
    extern char *optarg;
    int c;
    int didSomething = 0;
    int aflag=0, mflag=0, cflag=0, iflag=0, oflag=0;
    char *cmd; // target first cam as default
    char *outfile = "";
    int target=0;

    while((c = getopt(argc, argv, "a:m:c:i:o::")) != -1) {

        switch(c) {
            case 'a':
                aflag=1;
                cmd = optarg;
                //handleApiCall(optarg);
                didSomething = 1;
                break;
            case 'm':
                mflag=1;
                cmd = optarg;
                didSomething = 1;
                break;
            case 'c':
                cflag=1;
                cmd = optarg;
                didSomething = 1;
                break;
            case 'i':
                iflag=1;
                target = atoi(optarg);
                break;
            case 'o':
                oflag = 1;
                outfile = optarg;
                didSomething = 1;
                break;
        }

    }
    if (aflag == 1 && iflag == 1) {
        handleApiCall(cmd, target, oflag, outfile);
    } else if (mflag == 1) {
        handleModclk(cmd);
    } else if (cflag == 1 &&  iflag == 1) {
        handleCapture(cmd, target);
    } else {
        printf("target camera must be specified!\n");
    }
    if (!didSomething) {

        printf("Usage: \n");
        printf("  $ %s -a <api call>\n", argv[0]);
        printf("  $ %s -m <modclk cmd>\n", argv[0]);
        printf("  $ %s -c <capture cmd>\n", argv[0]);

    }

    return 0;

}
