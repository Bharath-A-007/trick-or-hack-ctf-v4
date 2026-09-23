#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef struct {
    char name[32];
    char secret[128];
} Tentacle;

Tentacle *tentacles[10];
int num_tentacles = 0;

void spawn_tentacle(const char *name, const char *secret) {
    if (num_tentacles >= 10) return;
    Tentacle *t = malloc(sizeof(Tentacle));
    strcpy(t->name, name);
    strcpy(t->secret, secret);
    tentacles[num_tentacles++] = t;
}

void list_tentacles() {
    for (int i = 0; i < num_tentacles; i++) {
        printf("[%d] %s\n", i, tentacles[i]->name);
    }
}

void banish_tentacle(int idx) {
    if (idx < 0 || idx >= num_tentacles) return;
    free(tentacles[idx]);
    // BUG: pointer never nulled — use-after-free vector!
}

void whisper_secret(int idx, const char *new_secret) {
    if (idx < 0 || idx >= num_tentacles) return;
    // VULNERABLE: no bounds check, no validation that tentacles[idx] is still valid
    strcpy(tentacles[idx]->secret, new_secret);
}

void speak_secret(int idx) {
    if (idx < 0 || idx >= num_tentacles) return;
    printf("The tentacle says: %s\n", tentacles[idx]->secret);
}

void menu() {
    while (1) {
        printf("\n=== Summoning Interface ===\n");
        printf("1. Spawn tentacle\n");
        printf("2. List tentacles\n");
        printf("3. Banish tentacle\n");
        printf("4. Whisper to tentacle\n");
        printf("5. Ask tentacle to speak\n");
        printf("6. Exit\n");
        printf("> ");
        fflush(stdout);

        int choice;
        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        if (choice == 1) {
            char name[32], secret[128];
            printf("Tentacle name: ");
            fgets(name, sizeof(name), stdin);
            name[strcspn(name, "\n")] = 0;
            printf("Secret: ");
            fgets(secret, sizeof(secret), stdin);
            secret[strcspn(secret, "\n")] = 0;
            spawn_tentacle(name, secret);
            printf("Tentacle spawned.\n");
        } else if (choice == 2) {
            list_tentacles();
        } else if (choice == 3) {
            printf("Index: ");
            int idx;
            scanf("%d", &idx);
            while (getchar() != '\n');
            banish_tentacle(idx);
            printf("Tentacle banished.\n");
        } else if (choice == 4) {
            printf("Index: ");
            int idx;
            scanf("%d", &idx);
            while (getchar() != '\n');
            char new_secret[128];
            printf("Whisper: ");
            fgets(new_secret, sizeof(new_secret), stdin);
            new_secret[strcspn(new_secret, "\n")] = 0;
            whisper_secret(idx, new_secret);
            printf("Whispered.\n");
        } else if (choice == 5) {
            printf("Index: ");
            int idx;
            scanf("%d", &idx);
            while (getchar() != '\n');
            speak_secret(idx);
        } else if (choice == 6) {
            break;
        }
    }
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    // Seed with the flag as a hidden tentacle's secret
    spawn_tentacle("flag_keeper", "TOH{h34p_u4f_4wak3n5_th3_kr4k3n}");

    printf("=== The Kraken Awakens ===\n");
    printf("Learn to control the tentacles...\n");

    menu();
    return 0;
}
