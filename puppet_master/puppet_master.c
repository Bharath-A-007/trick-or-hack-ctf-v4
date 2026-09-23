#include <stdio.h>
#include <string.h>
#include <unistd.h>

void puppet_show() {
    // The puppet's true name is a local secret, never printed directly —
    // but it still lives on the stack, right near your own whisper...
    char true_name[48];
    FILE *f = fopen("flag.txt", "r");
    if (f) {
        if (!fgets(true_name, sizeof(true_name), f)) strcpy(true_name, "TOH{flag_file_missing}");
        fclose(f);
    } else {
        strcpy(true_name, "TOH{flag_file_missing}");
    }

    char whisper[128];
    printf("The puppet repeats everything you whisper to it.\n");
    printf("Whisper something: ");
    fflush(stdout);
    read(0, whisper, sizeof(whisper) - 1);

    // Deliberately vulnerable: user input used directly as the format string.
    printf(whisper);
    fflush(stdout);

    printf("\nThe puppet falls silent.\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    puppet_show();
    return 0;
}
