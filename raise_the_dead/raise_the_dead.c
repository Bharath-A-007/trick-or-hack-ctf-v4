#include <stdio.h>
#include <unistd.h>

void vuln() {
    char grave[64];
    printf("The grave is 64 bytes deep. What will you raise from it?\n");
    fflush(stdout);
    read(0, grave, 300);   // deliberately no bounds check
    printf("The soil settles...\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
