#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

void print_flag() {
    FILE *f = fopen("flag.txt", "r");
    char buf[256] = {0};
    if (!f) { printf("flag.txt missing next to the binary!\n"); return; }
    if (fgets(buf, sizeof(buf), f)) printf("%s\n", buf);
    fclose(f);
}

void vuln() {
    char basket[64];
    printf("Feed the jack-o'-lantern some candy (the basket holds 64 bytes... allegedly):\n");
    fflush(stdout);
    read(0, basket, 500);   // deliberately no bounds check
    printf("You fed it some candy. Nothing else happens... or does it?\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    printf("The lantern stays dark.\n");
    return 0;
}
