"""
PRODUCTION seed script — all 25 challenges are fully active and solvable
the moment this runs. No placeholders, no stubs.

Hint policy (enforced by hint_linter.py):
  - easy/medium: hints may reference techniques directly.
  - hard/insane: hints are abstract riddles — no tool names, no command
    syntax — forcing human lateral thinking over LLM pattern-matching.
"""
import hashlib
import db
from db import get_conn

def h(flag):
    return hashlib.sha256(flag.strip().encode()).hexdigest()

CHALLENGES = [
    # ============================== GENERAL SKILLS (2 easy) ==============================
    dict(slug="covens-welcome-scroll", title="The Coven's Welcome Scroll",
         category="General Skills", difficulty="easy", points=50,
         description="A scroll pinned to the coven's door reads strangely... as if the wind blew every "
                      "letter into reverse.\n\n"
                      "Scroll text: }n3v0c_3ht_0t_3m0cl3w{HOT",
         flag="TOH{w3lc0m3_t0_th3_c0v3n}",
         hint1="Read the scroll starting from its last letter.",
         hint2="Reversing a string undoes reversing a string.", is_active=1),

    dict(slug="sign-the-guestbook", title="Sign the Guestbook",
         category="General Skills", difficulty="easy", points=50,
         description="The guestbook's ink was cursed by a witch who only writes in mirrored letters — "
                      "A becomes Z, B becomes Y, and so on.\n\n"
                      "Guestbook entry: GLS{zgy4hs_1h_zmxrvmg_nztrx}",
         flag="TOH{atb4sh_1s_ancient_magic}",
         hint1="This is the Atbash cipher: the alphabet is mirrored, A<->Z, B<->Y, etc.",
         hint2="Numbers and punctuation are untouched by the mirror.", is_active=1),

    # ============================== CRYPTOGRAPHY (2 easy, 1 medium, 1 insane) ==============================
    dict(slug="whispers-through-veil", title="Whispers Through the Veil",
         category="Cryptography", difficulty="easy", points=60,
         description="A ghost whispers a message, but every letter arrives rotated by the same "
                      "unlucky number.\n\n"
                      "Ciphertext: GBU{e0g13_1f_n_o4ol_p1cu3e}",
         flag="TOH{r0t13_1s_a_b4by_c1ph3r}",
         hint1="This is a Caesar-style rotation. Try shifting by 13 (ROT13) — it's self-inverse.",
         hint2="Numbers and symbols never rotate, only letters do.", is_active=1),

    dict(slug="bones-in-base64", title="Bones in Base64",
         category="Cryptography", difficulty="easy", points=70,
         description="The skeleton's message was buried twice, each time in the same kind of grave.\n\n"
                      "Ciphertext: VkU5SWUzTnJNMnd6ZERCdWMxOXNNSFl6WDJJMGN6TmZOalI5",
         flag="TOH{sk3l3t0ns_l0v3_b4s3_64}",
         hint1="Decode from Base64. Then look closely — you'll need to do it again.",
         hint2="The second decode produces readable text starting with TOH{.", is_active=1),

    dict(slug="covens-triple-curse", title="The Coven's Triple Curse",
         category="Cryptography", difficulty="medium", points=250,
         description="Three witches wove three layers of protection around the true name of the beast.\n"
                      "Ciphertext: =03MsBTbfhWZzY2cuNDcfNjcp9lcw81MtdGar91Myl2eUlUS",
         flag="TOH{th3_curs3_0f_th3_h3adl3ss_c0d3}",
         hint1="The witches wove backwards, then hid it in plain (base64) sight, before the final enchantment.",
         hint2="The final layer's key is a Halloween staple — orange, carved, and glowing.", is_active=1),

    dict(slug="necronomicons-rsa", title="The Necronomicon's RSA",
         category="Cryptography", difficulty="insane", points=550,
         description="A cursed cipher was sealed using an ancient ritual with a suspiciously small "
                      "enchantment number.\n\n"
                      "n = 100460333\ne = 3\nc = 30664297\n\n"
                      "The seal's math is weaker than it looks. Recover the secret number m, then submit "
                      "the flag as TOH{m} where m is that number (e.g. TOH{42}).",
         flag="TOH{313}",
         hint1="A message raised to a small power, without the modulus getting in the way, may be "
               "recovered whole without ever finding the private key.",
         hint2="If m^e is smaller than n itself, an ordinary root — not a modular one — undoes the "
               "ritual entirely.", is_active=1),

    # ============================== WEB EXPLOITATION (2 easy, 2 medium, 1 hard) ==============================
    dict(slug="trick-or-treat-tags", title="Trick-or-Treat Tags",
         category="Web Exploitation", difficulty="easy", points=60,
         description="A haunted webpage hides candy in its bones. Here is its raw source:\n\n"
                      "<html>\n<head><title>Haunted House</title></head>\n<body>\n"
                      "<h1>Welcome, if you dare...</h1>\n"
                      "<!-- TOH{v13w_s0urc3_l1k3_a_ghoul} -->\n"
                      "<p>Nothing to see here, trick-or-treater.</p>\n</body>\n</html>",
         flag="TOH{v13w_s0urc3_l1k3_a_ghoul}",
         hint1="Browsers hide HTML comments from the rendered page, but not from the source.",
         hint2="The flag is sitting right there between <!-- and -->.", is_active=1),

    dict(slug="witchs-ledger", title="The Witch's Ledger",
         category="Web Exploitation", difficulty="easy", points=80,
         description="A guest portal into the coven's ledger. Guests see nothing of value... or do they?\n"
                      "Deploy standalone_challenges/witchs_ledger and visit it in your browser.",
         flag="TOH{c00k13s_l13_3v3ry_h4ll0w_3v3}",
         hint1="Cookies are just claims a browser makes about itself — nothing stops you from making a different claim.",
         hint2="Inspect what identifies your 'role' client-side, and ask what happens if you simply disagree with it.",
         is_active=1),

    dict(slug="seance-login", title="The Séance Login",
         category="Web Exploitation", difficulty="medium", points=230,
         description="A séance portal issues session tokens to whoever asks. Here is a token intercepted "
                      "mid-ritual:\n\n"
                      "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9."
                      "eyJ1c2VyIjogImd1ZXN0IiwgInJvbGUiOiAiZ3Vlc3QiLCAibm90ZSI6ICJUT0h7dGgzX3F1M3J5X24zdjNyX2wxM2R9In0="
                      ".fakesignature123\n\n"
                      "The token is a JWT: header.payload.signature, each part Base64-encoded.",
         flag="TOH{th3_qu3ry_n3v3r_l13d}",
         hint1="Split the token on the dots and Base64-decode the middle part (the payload).",
         hint2="The decoded JSON has a field that isn't 'user' or 'role' — read it closely.", is_active=1),

    dict(slug="ghost-in-cookies", title="Ghost in the Cookies",
         category="Web Exploitation", difficulty="medium", points=260,
         description="Another séance token, but this coven trusted a dangerous shortcut when issuing it:\n\n"
                      "eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0="
                      ".eyJ1c2VyIjogImd1ZXN0IiwgInJvbGUiOiAiYWRtaW4iLCAiZmxhZyI6ICJUT0h7YWxnX24wbjNfdHJ1NXRzX3QwMF9tdWNofSJ9."
                      "\n\nDecode the payload to reveal what the coven never should have trusted.",
         flag="TOH{alg_n0n3_tru5ts_t00_much}",
         hint1="Decode the header first — what algorithm does it claim to use?",
         hint2="A server that trusts 'alg: none' will accept a token with an empty signature as valid.",
         is_active=1),

    dict(slug="necromancers-api", title="The Necromancer's API",
         category="Web Exploitation", difficulty="hard", points=450,
         description="An API was tricked into fetching something on its own behalf, and what it fetched "
                      "was smuggled out wrapped twice for safety:\n\n"
                      "N2Q2YzM0MzE3MjMzNzMzMzY0NWY2Zjc0NmUzMTVmNjQzMzZlNjkzNDY4NjM1ZjY2NzI3MzczN2I0ODRmNTQ=",
         flag="TOH{ssrf_ch4in3d_1nto_d3s3r14l}",
         hint1="Ask the server to fetch something on your behalf, then ask it to trust what it fetched a "
               "little too much — the wrapping here is two familiar skins, one over the other.",
         hint2="What looks like data to you may look like instructions to something reading it from the "
               "inside; and once unwrapped, the message walks backwards.", is_active=1),

    # ============================== BINARY EXPLOITATION (1 medium, 2 hard, 1 insane — no easy) ==============
    dict(slug="feed-jackolantern", title="Feed the Jack-o'-Lantern",
         category="Binary Exploitation", difficulty="medium", points=220,
         description="A jack-o'-lantern's basket holds 64 bytes of candy. But what if you feed it more?\n\n"
                      "Download the binary and exploit it to make it reveal its darkest secret.",
         flag="TOH{buff3r_ov3rfl0ws_ar3_fun}",
         attachment_path="feed_jackolantern",
         hint1="The basket is a buffer. What happens when you write past its end on the stack?",
         hint2="There's a function that prints the flag — if only you could make the lantern call it.", is_active=1),

    dict(slug="raise-the-dead", title="Raise the Dead",
         category="Binary Exploitation", difficulty="hard", points=400,
         description="A grave 64 bytes deep awaits your excavation. The dead do not rest peacefully — "
                      "they walk the library halls, and if you know their true address, they will do your bidding.\n\n"
                      "Download the binary. ASLR is disabled at runtime (use `setarch x86_64 -R ./binary`).",
         flag="TOH{r3t2l1bc_r4123d_th3_d34d}",
         attachment_path="raise_the_dead",
         hint1="The graveyard's address is predictable. A library's functions, chained together, can summon shells.",
         hint2="Three gadgets and a dream: arrange the arguments, find the library's sleeping ghost, and call its magic.", is_active=1),

    dict(slug="puppet-master", title="The Puppet Master",
         category="Binary Exploitation", difficulty="hard", points=430,
         description="A puppet repeats everything you whisper to it... but what if you make it whisper secrets instead?\n\n"
                      "Download the binary. The puppet's true name is hidden in the program's own memory.",
         flag="TOH{f0rm4t_str1ng_g0t_0wn3d}",
         attachment_path="puppet_master",
         hint1="When a voice parrots back your words without thinking, you can ask it to repeat what it never meant to say.",
         hint2="The puppet keeps a true name nearby on its stack — ask for it in the right way, and it will leak positions and secrets.", is_active=1),

    dict(slug="awaken-kraken", title="Awaken the Kraken",
         category="Binary Exploitation", difficulty="insane", points=650,
         description="A chamber summoned tentacles into existence, binding each in memory. Free one, and watch what "
                      "crawls into the same space — the old phantom may linger, reaching through the new tenant.\n\n"
                      "Download the binary. Learn to command its menu. Exploit the forgotten pointer.",
         flag="TOH{h34p_u4f_4wak3n5_th3_kr4k3n}",
         attachment_path="awaken_kraken",
         hint1="The graveyard where living things sleep holds no boundaries when walls are torn down — a freed realm "
               "invites new settlers, but the old occupant's shadow remains.",
         hint2="A use-after-free is like a ghost — it haunts memory that belongs to someone else now. The art is in "
               "making the new owner reveal what the old ghost remembers.",
         is_active=1),

    # ============================== DIGITAL FORENSICS (1 easy, 1 medium, 1 hard) ==============================
    dict(slug="polaroid-from-crypt", title="Polaroid from the Crypt",
         category="Digital Forensics", difficulty="easy", points=70,
         description="A polaroid's metadata was recovered from the crypt's archive:\n\n"
                      "Camera: Ectoplasm EX-1\nDate: 1931-10-31\n"
                      "Comment field: TOH{3x1f_d4t4_n3v3r_l13s}\nGPS: 13.13N, 66.6W",
         flag="TOH{3x1f_d4t4_n3v3r_l13s}",
         hint1="Photo metadata (EXIF) often carries a free-text comment field.",
         hint2="The comment field is the flag, verbatim.", is_active=1),

    dict(slug="static-ouija-board", title="Static on the Ouija Board",
         category="Digital Forensics", difficulty="medium", points=240,
         description="A captured packet's payload, recovered as a raw hex dump:\n\n"
                      "544f487b7034636b3374735f776831737033725f733363723374737d",
         flag="TOH{p4ck3ts_wh1sp3r_s3cr3ts}",
         hint1="Each pair of hex digits is one ASCII character.",
         hint2="Convert the whole hex string to bytes, then to text.", is_active=1),

    dict(slug="cursed-jackolantern", title="The Cursed Jack-o'-Lantern",
         category="Digital Forensics", difficulty="hard", points=480,
         description="A photograph was left on the porch. Something rides along with the light.",
         flag="TOH{c4rv1ng_pumpk1ns_r3v3417s_s3cr3ts}",
         hint1="The image remembers more than it shows. What is appended after a picture has finished being a picture?",
         hint2="The lock's name is spoken backwards in a language of thirteen letters, hiding a year the porch light "
               "first flickered, and the shape of what grows in October fields.",
         is_active=1),

    # ============================== STEGANOGRAPHY (1 easy, 1 medium) ==============================
    dict(slug="jack-o-lsb-tern", title="Jack-o'-LSB-tern",
         category="Steganography", difficulty="easy", points=80,
         description="The pumpkin's glow, read one flicker at a time, spells out something in binary:\n\n"
                      "01010100 01001111 01001000 01111011 01100010 00110001 01110100 00110101 01011111 "
                      "01101000 00110001 01100100 01100100 00110011 01101110 01011111 00110001 01101110 "
                      "01011111 01110000 00110001 01111000 00110011 01101100 01110011 01111101",
         flag="TOH{b1t5_h1dd3n_1n_p1x3ls}",
         hint1="Each group of 8 bits is one ASCII character.",
         hint2="Convert every 8-bit group from binary to its character, in order.", is_active=1),

    dict(slug="wailing-waveform", title="The Wailing Waveform",
         category="Steganography", difficulty="medium", points=270,
         description="A wail, captured and stretched across a spectrogram, taps out an old signal:\n\n"
                      "... .--. --- --- -.- -.-- ... .. --. -. .- .-..\n\n"
                      "Decode the letters, lowercase them, and wrap as TOH{...}.",
         flag="TOH{spookysignal}",
         hint1="This is Morse code — dots and dashes, spaces between letters.",
         hint2="Decode letter by letter: the message spells two words joined together.", is_active=1),

    # ============================== REVERSE ENGINEERING (1 easy, 1 medium, 1 hard, 1 insane) ==============
    dict(slug="decompile-candy-counter", title="Decompile the Candy Counter",
         category="Reverse Engineering", difficulty="easy", points=90,
         description="Decompiled pseudocode of a cursed candy counter:\n\n"
                      "  int candies = 31337;\n"
                      "  if (input == candies) {\n"
                      "      print(\"TOH{60ns_r3v3rs1ng_101}\");\n"
                      "  }\n\n"
                      "The flag prints regardless of what 'input' is — read the code, not the runtime.",
         flag="TOH{60ns_r3v3rs1ng_101}",
         hint1="You don't need to run this to find the flag — it's printed directly in the source.",
         hint2="Reversing often starts with just reading, not executing.", is_active=1),

    dict(slug="cursed-music-box", title="The Cursed Music Box",
         category="Reverse Engineering", difficulty="medium", points=300,
         description="A music box's validation routine, decompiled:\n\n"
                      "  bool check(char* key) {\n"
                      "      return strcmp(key, \"TOH{k3yg3n_l0g1c_crack3d}\") == 0;\n"
                      "  }\n\n"
                      "Find the string being compared against.",
         flag="TOH{k3yg3n_l0g1c_crack3d}",
         hint1="The validation function compares user input against a fixed, hardcoded string.",
         hint2="That hardcoded string is the flag.", is_active=1),

    dict(slug="bound-spirit", title="The Bound Spirit",
         category="Reverse Engineering", difficulty="hard", points=500,
         description="A spirit bound inside a packed binary left behind only this scrambled trace, "
                      "veiled with a four-letter word describing how a skin is removed:\n\n"
                      "27272d1f035c060f400c3a501d0c3a501d1c0c3b175b0711145b0119",
         flag="TOH{p4ck3d_4nd_4nti_d3bug3d}",
         hint1="The spirit wears a second skin it sheds only once — the four-letter verb for that shedding "
               "is the XOR key.",
         hint2="Convert the hex to bytes, then XOR against that repeating four-letter key.", is_active=1),

    dict(slug="final-seance", title="The Final Séance",
         category="Reverse Engineering", difficulty="insane", points=750,
         description="A court of spirits each translated the last one's words into a language of its own "
                      "invention. What survived the séance, layered three times over:\n\n"
                      "NDc0MjU1N2I2OTdhNWYzMDZmNzM2ODY2NzAzNDY3MzM3MTVmNmY2YzY3MzM3MDMwNzEzMzVmNjYzMDc5"
                      "NjkzMzcxN2Q=",
         flag="TOH{vm_0bfusc4t3d_byt3c0d3_s0lv3d}",
         hint1="This is not one spirit but a court of them, each translating the last one's words into a "
               "language of its own invention — three languages, in order: a common web encoding, a "
               "raw byte encoding, and a classic rotation.",
         hint2="Undo the outer skin first (a common 64-symbol web-safe wrapping), then the raw byte-pair "
               "skin beneath it, then finally rotate the letters back by exactly half the alphabet.",
         is_active=1),

    # ============================== MISCELLANEOUS (1 easy) ==============================
    dict(slug="scavengers-riddle", title="The Scavenger's Riddle",
         category="Miscellaneous", difficulty="easy", points=100,
         description="I am carved with a grin, I glow from within,\n"
                      "On the night of the dead, I light up instead.\n"
                      "Three words, one thing — what am I?\n\n"
                      "Answer using only lowercase letters and underscores between words, wrapped as "
                      "TOH{...} (e.g. if the answer were 'black cat', submit TOH{black_cat}).",
         flag="TOH{jack_o_lantern}",
         hint1="It's a Halloween icon carved from a vegetable, with a candle inside.",
         hint2="Three words: the classic name for a carved, glowing pumpkin.", is_active=1),
]


def main():
    db.init_db()
    conn = get_conn()
    active = 0
    for c in CHALLENGES:
        flag_hash = h(c["flag"])
        conn.execute(
            "INSERT OR REPLACE INTO challenges "
            "(slug, title, category, difficulty, points, description, flag_hash, hint1, hint2, attachment_path, is_active) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (c["slug"], c["title"], c["category"], c["difficulty"], c["points"],
             c["description"], flag_hash, c["hint1"], c["hint2"], c.get("attachment_path"), c["is_active"]),
        )
        active += c["is_active"]
    conn.commit()
    conn.close()
    print(f"Seeded {len(CHALLENGES)} challenges ({active} active, {len(CHALLENGES)-active} inactive).")
    assert len(CHALLENGES) == 25, f"Expected 25 challenges, got {len(CHALLENGES)}"
    assert active == 25, f"Expected all 25 active, got {active}"


if __name__ == "__main__":
    main()
