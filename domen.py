import asyncio
import aiohttp
import json
import os
import random
from datetime import datetime, timezone, timedelta
from aiohttp_socks import ProxyConnector


STATE_FILE = "vk_monitor_state.json"

VK_URL = "https://api.vk.com/method/utils.resolveScreenName"
VK_API_VERSION = "5.199"

MAX_TOKENS = 15
CONCURRENCY = 200

REQUEST_TIMEOUT = 5
SESSION_TIMEOUT = 20

MSK = timezone(timedelta(hours=3))

# === VK сервисные ключи (15 штук) ===
VK_TOKENS = [
    "vk1.a.wAl6aBQ_GmEsQGAi6q7BtV0FYDxuZJORtL3OIAufyutdfThOeKrHw6DAl5EI9Wrh66fEnNyGWp8IDuW30lT5WQrwZi_iZhkapyTXBhVGU4AyXYRqJ3FZ9U3vTd0Q4u83XgQfN8tJgM1pwRghLcmYmRyD32J_m544PAOwBYCXIJb8NJ0JCLIcLrIsy6nLZps82ZOm1XU_fUskrUbL-g433d7BANtFHXWMhszNoFYnlw4",
    "vk1.a.7iqpuE8101IKlxdmvmT6nrmt1alOyChIfcQNu3aVXpXV1c2gRc7wR0cl5ZPOJKNqfbfqGVAaGsIJp2506FyTziX4CFxo964JgmvI_jiTZ3luLN814KnFdXB-v9hPg69_y0Z1iMoWPFbKjCUcK9xrqZa1rcIqGnuEf00_7w1GhNtW4-cp8R74_ixqCJWGAAuxcLxhzYLydlwcsaihXOCh9HbmLEbaX-KB1L2sgOOmFwk",
    "vk1.a.D8E7pkXFH3f_6cJB1yiy3WYSmwuGNBmG1MIa1XHYExgxn_L8TnddrwMAzP7NAl8xm2Bqr_LvXdF7wgnLsSPxGjjXjexPDoJD4cePAEZq-qSFsPXeiYSlmtyx7hUob-QQmbcpEbtykuF5OC_IfklPkDBOU2hVSiw2NKasT6ssihG6q317boqikVmucgi_9eDy2DW5-vz7r2mjr45WlYCM7PSiv2F-AiHzV2A_3i-ssDw",
    "vk1.a.etuL9WYu0qSWi8DxSWjzM6NC5cP5ZNNiGDhib_kfp3mCNmojD35U_5BPeY9j5m62fwCTDp2UPy1g2azuhApbXRJPXEPdaERkjeq44yH8Tx8lhJfLVTd44Exiclqh9aDcOpUPP5k34ONZQdW0ys_XQ4zF-CTGPNk8OerEsXo32-8L0LUPsTZOHkTEZh932273nUvHamwAaLO9olXRV6ukgxJpoGxgmDykRQRSq-l9W7Y",
    "vk1.a.RI19EXM1EVRC9qEph2F3XE0Oksx7W7q_6VUIcsvoNtSD3DIo_qSshe0NACz25_PUqHneeKb6rIi-QekU3jJI1LE0-Coc0uyB8jOSU2hIpLlb_kogKTwWg2bdVMZtXIIt0kXqvapccgWLC-LwCSyr3f3aTzbcHu5l1OJNqXRo-azE28s6hbrsWCK38OdIGTHYGDYy2PMhU74YGYgqLx6sONZJ_XHr5RmC0jQEiLWFJNA",
    "vk1.a.0cnQMXMgwtwqtqhTXZb4aEEH1Do6MP3sbP2mljdfMZ4lwKyntAb6o0sB1JiBDpELp2JkpOe49MyvD6F2Dv5ofOPtX6CcZh-z2g7mutzVvhQCBl9catNi3xp9xX_ZFMy_MR2e1oyGaI983HNRPOKIC33pC_8KMR3jPE9MPjLEFg59qCBS2OCIVbAIPs1ay_K64UqGrazkgczI7mWBNQ5VpjK2u_fKSSYm2ofgClalKRo",
    "vk1.a.nwOhJ9t7VIcMGcID1W9D-5tk7L4yiexgAblS_buC88aQKh7onxxuz273aFbtsLkamKf_ysA9u4Qlgon5F9SozuJidqS6Kz4v3_myQVJ5GRbzGWNCF70j-zV3vbiuvmbKN5IjkBHol24QuvB3hqGBPoJkXybvXbbtqg2J0-0GatAoiPnSyNKD90_u2ox5PYqI-T0PSkjj5cKeXkPIR4-LzNbFRx8CfbOJWfFdNFwc85E",
    "vk1.a.CQP-VM5H6QH4zRFGc9VI876jJhydGIzaigAZZGdfC10BpZ0XmYHTPCy2F-5ciHA0LMsK290HVjKyiJpIryPud8K_-722_xepI8hRWV2WfmdhRkM1B7To4aJqO2XwC5ImU5oMwODLZqhhBpXAgnFynxGjCd6M3xxE2EtklgWWWYVAUztUi3G-QXlEkUyRcF-zNPGvoI_IzNhqDS5FCwIfAc0pkTd--x4I_o-wABmDHLw",
    "vk1.a.zkMELjHGLTYm1ItKA3ASbXjqqmp0aXmoqoJYxVrpSkYOK88nSTUBfhwSIYZv2nCItnfUkD2d0EdBAmliC9p3JSPi-d5bl4Tg4xpAEjCGJsLMmMMHSMhKFgXN0hUfnJy17Cg30liqHUUTrlll9B8x-eqyeBrqH9MPTEyQ8PS_QqY0NH5U5jKuFx0xXzI-mQbkwf6sh1bi9qlDh6aHk9sGALpDg-08vbIRpqJ36NptX-o",
    "vk1.a.NUjSRfXeoIPNO1LdFCTkt64Py7cV0dkV18X0ijumwqx-VvZoTGqS5xIoOLahG-0Ci_IqxHcOL0I2D4j4CtFmz-bLcW5B5MgX_QmUMoW5pTv0LmepTadEeBkf8gWd_oan8zx9I5CTizXlMn9eTt3NdjH3G2I_SI-SKmjgD6eIep-bTImv7LxR8qhbGzXjOkSL8b0YhAmJCB1Pic4YkaevtYzGVQWbNkgZNjwbL9k3TH8",
    "vk1.a.Ckc0hvc0hp5LcuKcQkRxqYzTX-Qz5XcvL1M4UaKWCW5PBIYRJ7l5PQdcHVT0SfK9fH_Vcqvsp1VtCzmXQc0aUUb4qq1tRw5MBUeEy7lA2H6XWZQX_YGmYyPHZfGXPQ3PBaR0DYdI5M9uOMVJ4P_P-i9lDgPlKkKVJvQHTk3dNI3T2rR6wxTAFOKKcJgS4yG9tSxT3rx5y7nE6vqZWWU4KPv7iVcv3dKc7r8bYDrQ",
    "vk1.a.Sy-LCp1kq3r0m3v6bW-9_LyYw2f4Jc8pz2r0Y5tD3rQy_8W1X5_yQy2LwNf9c4Kp3G7dT0nG6kO2bP8dV0CwS8vM3qW6r1zQ2V5kL0_Hn7eQ9T3kR5tM4vN8L2fJ6bZ1pY3Qw8cR0vX4hY9kW1sB3mD5jG7nT2fR8dL0zK6vW4cJ1pB7xS5qN9tM2fP8cV3dL6bY1wJ4kR0tZ5nG2mH9sC3fK7vD1qL8bW6xP2jT4rV5mN0hS3gY9kL2cB7fQ4tX8vP1nD5rM0gW6kJ3",
    "vk1.a.tnfKVGlz8f_NjnFhnvq_9CNTrD85ofMS6c6tiTMvS0gmskN3E0_WY7zqohMBAE4DlIBFrIStZ9qomgPmpfW95hVQ9z8Q5GS9MdVRAdV_i2me8IKQ3Qs3Q4lknT4CQ0XEsPxwfoH-hBtcyY5YX4t-KjF6Vrj5ghVimXGAUY1eFqAmLp4cCmEsqgbd5O0uO6CLfku9uOeZnTATB__2bnZ-kK8sNEJqL9vMwHX1x-xZHHE",
    "vk1.a.PaT0ENF-_5lZqCbDKVHWPbWjFaFkKIPzBBz9V_r4-PjC22_fe6RA7I5JM-8ji37oSo8WhPN7CKtnWKwKqXo8Zb36-jkDdFmp7O9KcLqSb0GfruTuB75kLd0fDZBHHS89JKa6C4Fg9YaP6PyJV1abDNN3Bn9NwcuD7RFCPzF-hXERGgYHEQntDnLmioDsOy2e3h5NZi2YPn1w-aWeVHkgf-ilyo226KqmLNfL9G-iGvw",
    "vk1.a._r6Ut_VTtpmBy4QJrphiDhgroaq4o4ld_WHg2OCofNkNyxrbcZd-JMaEYelHeae2_Jtxvxq1HLLHBCw5oQrgPn_QWY6yC9mo_6dR0Ys8AqFcNEaiq2YTZs_jUGBJPzv5rhT9jQsVWYlEKYm19m73po6VypdtfTTpOsa3qzOjufeRv8zq398QYYYyOuCmANTRzOUPvhQZaThfhiZDjHTWUYuIjziz7YGkt6ymriymL0s",
    "vk1.a.Cn2dW0AOFpU0bBHDZBI6Tpssvu--jJJEvjJgvYEHU11djEuV-ypoFgm3iSM5QQ93QVAHgdWsGbvGpcVw3z-PBNNtTexBN-3ffTSHRTIbJbXWuMWDs9VX0VNEWUjnWCtdtiA9EN3Jri7AA7QQUbzYnKvO5dYHEnimu6zdgVAG4TQAOWZyHf8ScHW0ZnL0AKMkRewsgbrwr07iPS3WOZ-NdCr3lWTZ0Gltzo3y5Wpaxx8",
    "vk1.a.RrZtXGTdt6gDQcr0xzdflPwXeDusuvl4Z3WgIA4yLvbOTmcllADBD33BdsUrKdozEwwtt-HrqZwaya5Ji8gcnoIHmlawVHwbbrizQebOToGqbe1Vg8wp546rFunqzp5mmhp-0veLzSxyWE0OxzP55pP4Al_D6m7Fx7_bdDGjXta1dS4ZW-UwKjLOIi7oRKFi-FrRF9JKMcJn3lvcq8B6-Ehd_nWFLqrfCrcACjHSskA",
]

# === Telegram ===
TG_BOT_TOKEN = "8810995487:AAHwxSAcTfFrpnkOAO5BAXC39dmyK5zKGu8"
TG_CHAT_ID = "-1004311840920"

# === Прокси ТОЛЬКО для Telegram ===
TG_PROXY = "socks5://modeler_DGwrPU:a7K0MPKgSNzp@172.234.57.170:22038"

# === Домены ===
DOMAINS = [
    "abyss", "amber", "angel", "apple", "april", "armor", "arrow",
    "ashen", "atlas", "aurum", "autumn", "azure", "bacon", "badge", "basil",
    "beach", "beast", "blade", "blaze", "bleak", "blend", "bless", "bliss",
    "bloom", "blown", "blush", "boast", "bones", "bonus", "boost", "booth",
    "bound", "brace", "braid", "brain",
    "breeze", "cloud", "creek", "dawn", "dusk", "earth", "field", "flame",
    "flood", "frost", "fruit", "glass", "grove", "haze", "hazel", "honey",
    "light", "lunar", "marsh", "meadow", "misty", "moon", "mossy", "ocean",
    "olive", "peach", "pearl", "petal", "rain", "ridge", "river", "rocky",
    "rose", "sandy", "shade", "shadow", "snow", "solar", "spark", "star",
    "stone", "storm", "sunny", "thorn", "tide", "timber", "tulip", "valley",
    "water", "wave", "wind", "woods", "zephyr", "agape", "aglow", "alive",
    "amity", "aura", "brave", "calm", "charm", "cheer", "clear", "dream",
    "ease", "faith", "fancy", "flair", "flash", "fresh", "gleam", "glow",
    "grace", "hope", "ideal", "karma", "love", "lucky", "mercy", "merry",
    "peace", "pure", "quiet", "soul", "spell", "spirit", "sweet", "trust",
    "truth", "unity", "valor", "vivid", "warm", "wish", "wonder", "youth",
    "adore", "awake", "breathe", "dance", "dare", "drift", "dwell", "embrace",
    "enjoy", "evoke", "float", "flow", "gaze", "glide", "grow", "heal",
    "inspire", "laugh", "learn", "lift", "listen", "live", "marvel", "mend",
    "nurture", "open", "pray", "radiate", "rise", "roam", "shine", "sing",
    "smile", "soar", "sparkle", "speak", "swim", "thrive", "touch", "wander",
    "whisper", "write", "yield", "aroma", "candle", "canvas", "chess", "crown",
    "crystal", "dress", "echo", "elegy", "ember", "essence", "fairy", "feast",
    "flute", "forest", "fountain", "gem", "gift", "glade", "gold", "harp",
    "heart", "ivory", "jewel", "kiss", "lace", "lake", "lily", "linen",
    "lotus", "lyric", "magic", "maple", "melody", "mirror", "mist", "muse",
    "music", "nest", "night", "noble", "oasis", "opera", "poem", "poise",
    "pride", "prize", "queen", "quest", "rainbow", "sapphire", "serene",
    "silk", "silver", "swan", "symphony", "thrill", "tiger", "treasure",
    "tree", "velvet", "verse", "violet", "voice", "willow", "agile", "ample",
    "ancient", "blithe", "bonny", "bright", "charming", "civil", "coral",
    "cozy", "crisp", "dainty", "dandy", "dear", "deep", "divine", "dreamy",
    "eager", "earthy", "easy", "elegant", "epic", "fine", "fluffy", "free",
    "friendly", "frugal", "funny", "gentle", "genuine", "glad", "glossy",
    "golden", "gorgeous", "graceful", "grand", "green", "happy", "hardy",
    "hearty", "heavenly", "honest", "hopeful", "humble", "idyllic", "jaunty",
    "jolly", "joyful", "kind", "lacy", "large", "lavish", "lively", "lovely",
    "lush", "magical", "mellow", "mighty", "mild", "modest", "natural", "neat",
    "novice", "opulent", "pastel", "peaceful", "perfect", "pink", "playful",
    "pleasant", "plucky", "poetic", "pretty", "queenly", "quick", "radiant",
    "rare", "ready", "refined", "regal", "rich", "rosy", "royal", "rustic",
    "sacred", "safe", "scarce", "shiny", "silent", "silky", "simple", "sincere",
    "sleek", "slim", "smiling", "smooth", "soft", "solid", "sparkly", "special",
    "spicy", "spirited", "splendid", "stable", "starry", "steady", "stellar",
    "sterling", "strong", "swift", "tender", "thankful", "thrilling", "tidy",
    "tiny", "tranquil", "true", "trusty", "unique", "valiant", "vibrant",
    "vintage", "virtuous", "wealthy", "whimsical", "white", "wild", "wise",
    "witty", "wondrous", "worthy", "young", "zany", "zealous", "abbey",
    "actor", "adult", "agent", "album", "alert", "alien", "alley", "alpha",
    "anger", "angle", "ankle", "arena", "argue", "arise", "array", "aside",
    "asset", "attic", "audio", "audit", "avoid", "await", "award", "aware",
    "baker", "ballet", "bamboo", "banana", "banner", "barley", "barrel",
    "basic", "basin", "batch", "beard", "begin", "being", "belly", "below",
    "bench", "berry", "birth", "biscuit", "black", "blank", "blast", "blind",
    "block", "blood", "blues", "board", "brand", "brass", "bread", "break",
    "breed", "brick", "bride", "brief", "bring", "brink", "broad", "broke",
    "brook", "brown", "brush", "buddy", "build", "built", "bunch", "burst",
    "buyer", "cabin", "cable", "cache", "camel", "canal", "candy", "canon",
    "canyon", "carbon", "career", "cargo", "carpet", "carry", "carve", "catch",
    "cause", "cease", "cedar", "chain", "chair", "chalk", "champ", "chaos",
    "chart", "chase", "cheap", "check", "cheek", "chest", "chief", "child",
    "chill", "china", "chip", "choir", "chord", "chose", "chunk", "cider",
    "cigar", "civic", "claim", "clash", "class", "clean", "clerk", "click",
    "cliff", "clinic", "clock", "close", "cloth", "clown", "coach", "coast",
    "cobra", "cocoa", "colon", "color", "comet", "comic", "corner", "cost",
    "cotton", "couch", "count", "court", "cover", "crack", "craft", "crane",
    "crash", "crazy", "cream", "crest", "crime", "cross", "crowd", "crumb",
    "crush", "crust", "curve", "cycle", "daily", "dairy", "daisy", "dared",
    "dealt", "death", "debit", "debut", "decay", "decent", "decor", "decoy",
    "deeds", "delay", "delta", "dense", "depth", "derby", "deter", "devil",
    "diary", "diced", "digit", "dimly", "diner", "dirty", "disco", "ditch",
    "diver", "dizzy", "dodge", "doing", "donor", "doubt", "dough", "dozen",
    "draft", "drain", "drama", "drank", "drawn", "dread", "dried", "drill",
    "drink", "drive", "drone", "drove", "drown", "drunk", "dryer", "ducky",
    "dully", "dumpy", "dying", "eagle", "early", "earn", "easel", "ebony",
    "eerie", "eight", "elder", "elect", "elite", "elope", "emcee", "empty",
    "enact", "endow", "enemy", "enter", "entry", "envy", "equal", "equip",
    "erase", "error", "essay", "ethic", "event", "every", "evict", "exact",
    "exalt", "excel", "exert", "exile", "exist", "expel", "extra", "exude",
    "fable", "faced", "fade", "false", "famed", "farce", "fatal", "fault",
    "fauna", "fella", "felon", "femur", "fence", "fern", "ferry", "fetch",
    "fever", "fiber", "fiery", "fifth", "fifty", "fight", "filet", "final",
    "finch", "first", "fishy", "fizzy", "flake", "flank", "flask", "fleck",
    "fleet", "flesh", "flick", "flier", "flock", "floor", "flora", "flour",
    "flown", "fluid", "fluke", "flung", "flush", "foamy", "focus", "foggy",
    "foil", "folks", "font", "force", "forge", "forth", "forty", "forum",
    "found", "frame", "frank", "fraud", "freak", "freed", "friar", "frill",
    "frisk", "froze", "fudge", "fully", "furry", "fuzzy", "gable", "gaily",
    "gamer", "gamma", "gaunt", "gauze", "gavel", "gecko", "genie", "genre",
    "ghost", "giant", "giddy", "gipsy", "girly", "given", "giver", "gland",
    "glare", "glaze", "glint", "gloat", "globe", "gloom", "glory", "gloss",
    "glove", "glows", "glyph", "gnome", "going", "goofy", "goose", "gorge",
    "gould", "grade", "graft", "grail", "grain", "grant", "grape", "graph",
    "grasp", "grass", "grave", "gravy", "graze", "great", "greed", "greet",
    "grief", "grill", "grind", "gripe", "groan", "groin", "groom", "grope",
    "gross", "group", "growl", "grown", "grump", "guard", "guava", "guess",
    "guest", "guide", "guild", "guile", "guilt", "guise", "gulf", "gully",
    "gumbo", "guru", "gushy", "gusto", "gusty", "habit", "hail", "hairy",
    "halo", "halve", "handy", "harem", "harsh", "haste", "hasty", "hatch",
    "hater", "haunt", "haven", "havoc", "hazy", "heavy", "hedge", "hefty",
    "hello", "hence", "herbs", "heron", "hilly", "hinge", "hippo", "hitch",
    "hoard", "hobby", "hoist", "holly", "homer", "honor", "horde", "horse",
    "hotel", "hound", "house", "hover", "human", "humid", "humor", "hunch",
    "hurry", "husky", "hyena", "hymn", "idiot", "idler", "igloo", "image",
    "imply", "incur", "index", "inept", "inert", "infer", "ingot", "inlet",
    "inner", "input", "intel", "inter", "intro", "iodine", "ionic", "irate",
    "irony",
    "abide", "abode", "abort", "about", "above", "abuse", "ached", "acorn",
    "acrid", "acute", "adapt", "adept", "admin", "admit", "adopt", "adorn",
    "affix", "afire", "aflame", "afoot", "afore", "after", "again", "agate",
    "agree", "ahead", "aided", "aider", "aimed", "aisle", "alarm", "alcove",
    "algae", "alias", "alibi", "align", "alike", "allot", "allow", "alloy",
    "aloft", "alone", "along", "aloof", "aloud", "altar", "alter", "altho",
    "amass", "amaze", "amble", "amend", "amidst", "amiss", "amuse", "anima",
    "anion", "anise", "annex", "annoy", "annul", "anode", "antic", "anvil",
    "aorta", "apart", "aphid", "apnea", "apply", "apricot", "apron", "aptly",
    "arbor", "ardor", "armed", "aroma", "arose", "arsine", "ascot", "ashore",
    "askew", "asian", "aspen", "assay", "aster", "astir", "atoll", "atone",
    "augur", "aunts", "aural", "avail", "avert", "awash", "awful", "awoke",
    "axial", "axion", "badly", "bagel", "baked", "balmy", "banal", "bandit",
    "bangle", "banjo", "barge", "baron", "basal", "basen", "basis", "baste",
    "bated", "bathe", "batik", "baton", "bawdy", "bayou", "beads", "beady",
    "beams", "beans", "began", "begun", "belch", "belie", "belle", "bends",
    "berth", "beset", "betel", "bevel", "bias", "bibel", "bicep", "biddy",
    "bided", "bigot", "bilge", "bilk", "binah", "binge", "bingo", "biome",
    "birch", "birds", "bison", "bitch", "biter", "bitty", "blame", "bland",
    "blare", "bleat", "bleed", "bleep", "blimp", "blink", "blitz", "bloat",
    "blobs", "blond", "bluer", "bluff", "blunt", "blurb", "blurt", "boars",
    "boaty", "bobin", "bogey", "boggy", "boils", "bolds", "bolts", "booby",
    "booty", "booze", "borax", "bored", "borer", "bough", "bowel", "boxer",
    "brake", "brash", "brava", "bravo", "brawl", "brawn", "brent", "bribe",
    "brier", "brig", "brill", "briny", "brisk", "broil", "brood", "broom",
    "broth", "brunt", "brute", "budge", "buggy", "bugle", "bulbs", "bulge",
    "bulky", "bully", "bunny", "burly", "burnt", "burro", "busby", "bushy",
    "butte", "byway", "cabal", "cabby", "cacao", "cacti", "caddy", "cadet",
    "cagey", "cairn", "cairo", "cajun", "cameo", "caned", "canine", "canny",
    "canoe", "caper", "capon", "caput", "carat", "cards", "cared", "carob",
    "carol", "carom", "carts", "caste", "cater", "caulk", "cavil", "ceded",
    "cellar", "cello", "chafe", "chaff", "chang", "chapel", "chasm", "cheat",
    "cheep", "chews", "chick", "chide", "chile", "chime", "chink", "chips",
    "chirk", "chive", "chock", "choke", "chomp", "chops", "chore", "chuck",
    "chump", "churl", "churn", "chute", "cinch", "cipher", "circa", "clack",
    "clamp", "clang", "clank", "clasp", "clave", "cleat", "climb", "cling",
    "clink", "cloak", "clone", "clout", "clove", "cluck", "clump", "clung",
    "comma", "conch", "condo", "coney", "congo", "conic", "cooee", "cooks",
    "corer", "corks", "corny", "cough", "could", "coupe", "covet", "covin",
    "cower", "coyly", "crab", "cramp", "crank", "crass", "crave", "crawl",
    "craze", "creak", "credo", "creed", "creep", "crepe", "crick", "cried",
    "crimp", "croak", "crock", "crone", "crony", "crook", "croup", "crude",
    "cruel", "crypt", "cubic", "cubit", "cuffs", "cumin", "curio", "curly",
    "curry", "curse", "curvy", "cynic", "daffy", "dally", "darns", "dauby",
    "dazed", "deals", "decal", "decry", "deign", "deity", "delve", "demon",
    "depict", "depots", "dhoti", "dices", "dicta", "dilly", "dined", "dingo",
    "dinky", "diode", "dire", "dirge", "discs", "ditto", "ditty", "docks",
    "dodgy", "dolly", "donut", "dooms", "doors", "doped", "doses", "doted",
    "dowdy", "dower", "downy", "dowry", "drake", "drape", "drawl", "dregs",
    "drier", "droit", "droll", "drool", "droop", "dross", "dryly", "ducal",
    "duchy", "ducts", "dudes", "duked", "dulls", "dumbo", "dummy", "dumps",
    "dunce", "dunes", "dusky", "dusty", "dwarf", "dwelt", "earns", "eased",
    "eaten", "eater", "eclat", "edict", "edify", "egret", "eject", "elfin",
    "elide", "elude", "emend", "emery", "emits", "endue", "ennui", "ensue",
    "envoy", "epoch", "erect", "erode", "erupt", "evade", "exult", "eyrie",
    "facet", "faded", "fader", "fagot", "faint", "faked", "faker", "fangs",
    "fated", "fates", "favor", "fecal", "feign", "feint", "feral", "ferns",
    "feted", "fewer", "fiend", "filch", "filed", "fille", "filly", "filmy",
    "filth", "fired", "fists", "fitch", "fixed", "flack", "flail", "flaky",
    "floss", "flout", "fluff", "flunk", "focal", "foist", "folly", "foray",
    "forgo", "forte", "fount", "foyer", "frail", "fresh", "fried", "frizz",
    "froth", "frown", "fumed", "fungi", "furor", "fused", "gawky", "geese",
    "ghoul", "glean", "gouge", "gourd", "grime", "grout", "grove", "grunt",
    "gulch", "gummy", "gunny", "gurge", "gutty", "hails", "harpy", "head",
    "heals", "heats", "heirs", "helms", "herds", "hoary", "homely", "howdy",
    "icier", "icing", "idiom", "imbue", "impel", "inged", "issues", "jaunt",
    "jazzy", "jeans", "jelly", "jerky", "jetty", "jiffy", "jilt", "jingo",
    "jockey", "joust", "judge", "juice", "juicy", "jumbo", "jumpy", "junta",
    "juror", "kappa", "kayak", "kebab", "kedge", "kendo", "ketch", "kiosk",
    "kites", "knack", "knave", "knead", "kneel", "knife", "knoll", "koala",
    "krill", "label", "labor", "laden", "ladle", "lager", "lance", "lanky",
    "lapel", "lapse", "larva", "laser", "latch", "later", "lathe", "latte",
    "layer", "leach", "leafy", "leaky", "leant", "leapt", "lease", "leash",
    "least", "leave", "ledge", "leech", "leery", "legal", "lemon", "lemur",
    "lento", "leper", "level", "lever", "libel", "lifted", "liger", "liken",
    "lilac", "limbo", "limit", "liner", "ling", "link", "lion", "lisle",
    "liter", "lithe", "liver", "livid", "lizard", "llama", "loach", "loaf",
    "loamy", "loath", "lobby", "local", "locus", "lodge", "lofty", "logic",
    "loose", "lorry", "loser", "lotto", "lousy", "lover", "lower", "loyal",
    "lucid", "lumen", "lump", "lunge", "lupin", "lurch", "lurid", "lusty",
    "lying", "macaw", "macho", "macro", "madam", "magma", "maize", "major",
    "maker", "mambo", "mamma", "mange", "mango", "mangy", "mania", "manic",
    "manor", "march", "mason", "match", "mated", "mauve", "maxim", "maybe",
    "mayor", "mealy", "meant", "medal", "media", "medic", "melon", "merge",
    "merit", "mesas", "metal", "meter", "metro", "micro", "midst", "mince",
    "miner", "minor", "mirth", "miter", "mixed", "mixer", "modal", "model",
    "modem", "moist", "molar", "moldy", "money", "month", "moody", "moose",
    "moral", "morph", "motel", "motif", "motor", "motto", "mould", "mound",
    "mount", "mourn", "mouse", "mouth", "mover", "movie", "mower", "mucky",
    "muddy", "muffin", "muffle", "mulch", "mummy", "mumps", "munch", "mural",
    "murky", "mused", "musky", "musty", "muted", "mylar", "myrrh", "nabob",
    "nacre", "nadir", "naiad", "naive", "naked", "named", "nanny", "napkin",
    "nasal", "natal", "naval", "navel", "nebula", "needs", "needy", "nerve",
    "never", "newly", "nicer", "niche", "nimble", "ninth", "noise", "noisy",
    "nomad", "nook", "noose", "north", "nosey", "notch", "noted", "novel",
    "nudge", "nurse", "nutty", "nylon", "oaken", "oaten", "oboe", "occur",
    "octet", "oddly", "odium", "offal", "offer", "often", "oiler", "olden",
    "omega", "onion", "onset", "opium", "optics", "orbit", "order", "organ",
    "other", "otter", "ought", "ounce", "outdo", "outer", "ovals", "ovens",
    "ovine", "ovoid", "owing", "owned", "owner", "oxide", "ozone", "paced",
    "paddy", "pagan", "pager", "pains", "paint", "palsy", "panel", "panic",
    "pansy", "papal", "paper", "parch", "parka", "parry", "parse", "pasta",
    "paste", "pasty", "patch", "patio", "pause", "payee", "payer", "pecan",
    "pedal", "peeve", "pellet", "penal", "pence", "penny", "peony", "perch",
    "peril", "perky", "pesto", "petty", "phase", "phone", "phony", "photo",
    "piano", "picky", "piece", "piety", "piggy", "pilaf", "pilot", "pinch",
    "pines", "pinky", "pious", "piper", "pique", "pitch", "pithy", "pivot",
    "pixel", "pixie", "pizza", "place", "plaid", "plain", "plane", "plank",
    "plant", "plate", "plaza", "plead", "pleat", "plied", "pluck", "plumb",
    "plume", "plump", "plush", "poach", "poesy", "poker", "polka", "pollen",
    "polyp", "pony", "poppy", "porch", "posit", "posse", "pouch", "pound",
    "power", "prancy", "prate", "prawn", "preen", "press", "price", "prime",
    "primp", "print", "prism", "privy", "probe", "prone", "prong", "proof",
    "proud", "prove", "prowl", "prude", "prune", "psalm", "pudgy", "puffy",
    "pulse", "punch", "pupil", "puppy", "puree", "purer", "purge", "purse",
    "pushy", "pygmy", "pylon", "quack", "quail", "quaint", "quake", "qualm",
    "quart", "quasi", "query", "queue", "quill", "quilt", "quirk", "quota",
    "quote", "rabbi", "rabid", "racer", "radar", "radio", "raft", "rage",
    "raid", "rail", "rainy", "raise", "rajah", "rally", "ralph", "ramble",
    "ranch", "range", "rapid", "ratio", "rattle", "raven", "ravine", "reach",
    "react", "realm", "reap", "rebel", "rebut", "recap", "recur", "redo",
    "reed", "reef", "reek", "reel", "reign", "relax", "relay", "relic",
    "remit", "renal", "renew", "repay", "repel", "reply", "reset", "resin",
    "retro", "retry", "reuse", "revel", "revive", "rhino", "rhyme", "rider",
    "rifle", "right", "rigid", "rigor", "riled", "rinse", "riots", "riper",
    "risky", "rival", "rivet", "roach", "roast", "robin", "robot", "rodeo",
    "rogue", "roman", "roomy", "roost", "roots", "roper", "rotten", "rouge",
    "rough", "round", "rouse", "route", "rover", "royal", "ruddy", "ruder",
    "rugby", "ruins", "ruler", "rumble", "rumour", "runner", "runny", "rural",
    "rusty", "saber", "sable", "sabot", "sadhu", "safari", "sagas", "saint",
    "salad", "salsa", "salty", "salve", "salvo", "samba", "saner", "sappy",
    "sassy", "satan", "satin", "satyr", "sauce", "sauna", "saved", "saver",
    "savor", "sawed", "scald", "scale", "scam", "scan", "scar", "scare",
    "scarf", "scary", "scene", "scent", "scion", "scoff", "scold", "scoop",
    "scoot", "scope", "score", "scorn", "scout", "scowl", "scrap", "scream",
    "scree", "screw", "scrub", "scuba", "scuff", "seals", "seams", "seamy",
    "sects", "sedan", "seedy", "seeks", "seems", "seeps", "seize", "semen",
    "sense", "sepia", "serif", "serum", "serve", "setup", "seven", "sever",
    "sewer", "shaft", "shake", "shaky", "shale", "shall", "shame", "shape",
    "shard", "share", "shark", "sharp", "shave", "shawl", "sheaf", "shear",
    "sheen", "sheep", "sheer", "sheet", "shelf", "shell", "shied", "shift",
    "ship", "shire", "shirk", "shirt", "shoal", "shock", "shone", "shook",
    "shoot", "shore", "shorn", "short", "shout", "shove", "shown", "showy",
    "shrub", "shrug", "shuck", "shunt", "shush", "shyly", "sided", "sidle",
    "siege", "sieve", "sight", "sigma", "silly", "since", "sinew", "singe",
    "siren", "sissy", "sixth", "sixty", "sized", "skate", "skew", "skid",
    "skiff", "skill", "skimp", "skirt", "skulk", "skull", "slack", "slain",
    "slang", "slant", "slash", "slate", "slave", "sleep", "slept", "slice",
    "slick", "slide", "slime", "sling", "slink", "slope", "sloth", "slump",
    "slung", "slurp", "slush", "slyly", "small", "smart", "smash", "smear",
    "smell", "smirk", "smite", "smith", "smock", "smoke", "smoky", "smote",
    "snack", "snafu", "snail", "snake", "snaky", "snare", "snarl", "sneak",
    "sneer", "snide", "sniff", "snipe", "snoop", "snore", "snort", "snout",
    "snowy", "snuck", "soapy", "sober", "sodden", "sodium", "softy", "soggy",
    "solve", "sonar", "sonic", "sooth", "soppy", "sorry", "sound", "south",
    "space", "spade", "spank", "spare", "spasm", "spawn", "spear", "speck",
    "speed", "spend", "spent", "spew", "sphere", "spice", "spied", "spill",
    "spine", "spiny", "spire", "spite", "splash", "splice", "spline", "split",
    "spoil", "spoke", "spoof", "spook", "spool", "spoon", "spore", "sport",
    "spout", "spray", "spree", "sprig", "spume", "spunk", "spurt", "squad",
    "squat", "squib", "stack", "staff", "stage", "staid", "stain", "stair",
    "stake", "stale", "stalk", "stall", "stank", "stare", "stark", "start",
    "state", "stave", "stead", "steak", "steal", "steam", "steed", "steel",
    "steep", "steer", "stein", "stern", "stick", "stiff", "still", "stilt",
    "sting", "stink", "stint", "stoic", "stoke", "stole", "stomp", "stony",
    "stood", "stool", "stoop", "store", "stork", "story", "stout", "stove",
    "strap", "straw", "stray", "strip", "strut", "stuck", "study", "stuff",
    "stump", "stung", "stunk", "sturdy", "style", "suave", "sugar", "suite",
    "sulky", "super", "surge", "sushi", "swami", "swamp", "swank", "swarm",
    "swath", "swear", "sweat", "sweep", "swell", "swept", "swill", "swine",
    "swing", "swirl", "swiss", "swore", "sworn", "synod", "syrup", "table",
    "taboo", "tacky", "taffy", "taint", "talon", "tamer", "tango", "tangy",
    "taper", "tapir", "tardy", "tarot", "taste", "tasty", "tatty", "taunt",
    "tawny", "teach", "teary", "tease", "teddy", "teeth", "tempo", "tenor",
    "tepid", "terse", "testy", "thank", "theft", "their", "theme", "there",
    "these", "thick", "thief", "thigh", "thing", "think", "third", "those",
    "three", "threw", "throb", "throw", "thumb", "thump", "tiara", "tibia",
    "tidal", "tight", "tiled", "timer", "timid", "tipsy", "tired", "titan",
    "tithe", "title", "toast", "today", "token", "tonal", "toner", "tonic",
    "tooth", "topaz", "topic", "torch", "total", "totem", "tough", "towel",
    "tower", "toxic", "trace", "track", "tract", "trade", "trail", "train",
    "trait", "tramp", "trash", "trawl", "tread", "treat", "trend", "triad",
    "trial", "tribe", "trick", "tried", "trill", "trim", "trio", "trip",
    "trite", "troll", "troop", "trope", "trout", "truce", "truck", "truly",
    "trump", "trunk", "tryst", "tubby", "tulle", "tumor", "tuned", "tuner",
    "tunic", "turbo", "tutor", "twang", "tweak", "tweed", "tweet", "twice",
    "twine", "twirl", "twist", "udder", "ulcer", "ultra", "umber", "uncle",
    "under", "undid", "undue", "unfit", "unify", "union", "unite", "unlit",
    "unmet", "unset", "untie", "until", "unwed", "unzip", "upend", "upper",
    "upset", "urban", "usage", "usher", "using", "usual", "utter", "vague",
    "valet", "valid", "value", "valve", "vapid", "vapor", "vault", "vaunt",
    "vegan", "venom", "venue", "verge", "verso", "vexed", "vials", "vicar",
    "video", "vigil", "vigor", "villa", "vinyl", "viola", "viper", "viral",
    "virus", "visit", "visor", "vista", "vital", "vixen", "vocal", "vodka",
    "vogue", "voter", "vouch", "vowel", "vying", "wacky", "wader", "wafer",
    "wager", "wages", "wagon", "waist", "waive", "waked", "waken", "wally",
    "waltz", "waned", "wants", "wares", "waste", "watch", "waver", "waxen",
    "weary", "weave", "wedge", "weedy", "weigh", "weird", "welds", "wells",
    "welsh", "whack", "whale", "wharf", "wheat", "wheel", "where", "which",
    "whiff", "while", "whine", "whirl", "whisk", "whole", "whoop", "whose",
    "widen", "wider", "widow", "width", "wield", "wight", "wiley", "wimpy",
    "wince", "winch", "windy", "wiped", "wiper", "wired", "wisely", "witch",
    "woken", "woman", "women", "wooed", "woody", "wooer", "words", "wordy",
    "world", "worry", "worse", "worst", "worth", "would", "wound", "woven",
    "wrack", "wrath", "wreak", "wreck", "wring", "wrist", "wrong", "wrote",
    "wryly", "yacht", "yearn", "yeast", "zesty", "zonal",
    "february", "october", "sakura", "tokyo", "magic",
    "xanax", "danger", "defeat", "spring", "summer", "twilight",
    "light",
    "month", "march", "mayhem", "august", "january", "june", "july",
    "november", "december",
    "monday", "friday", "sunday", "saturday", "tuesday", "thursday",
    "weekend", "weekday",
    "angels", "desire", "terror", "horror", "sorrow", "misery", "agony",
    "panic", "fears", "tears", "grief", "bliss", "peace", "anger", "pride",
    "shame", "guilt", "envy", "mercy", "grace", "faith", "trust", "doubt",
    "courage", "honor", "glory", "triumph", "victory", "blooding",
    "before", "freak", "silence", "whisper", "midnight", "sunset",
    "sunrise", "starlight", "moonlight", "daylight", "firefly", "butterfly",
    "dragon", "phoenix", "griffin", "unicorn", "serpent", "falcon",
    "eagle", "tiger", "lion", "wolf", "bear", "dragonfly", "breeze",
    "thunder", "lightning", "rainbow", "sunbeam", "moonbeam", "stardust",
    "cosmos", "galaxy", "nebula", "comet", "meteor", "asteroid", "planet",
    "saturn", "jupiter", "mercury", "venus", "neptune", "pluto", "uranus",
    "crimson", "scarlet", "violet", "indigo", "emerald", "sapphire", "topaz",
    "pearl", "opal", "ruby", "jade", "onyx", "coral", "ivory", "ebony",
    "bronze", "silver", "golden", "platinum", "diamond", "crystal",
    "phantom", "spectre", "spirit", "ghost", "wraith", "demon", "angel",
    "seraph", "cherub", "valkyrie", "titan", "olympian", "nemesis",
    "harmony", "melody", "symphony", "rhythm", "poetry", "sonnet", "ballad",
    "elegy", "verse", "prose", "novel", "story", "legend", "myth", "fable",
    "saga", "epic",
    "aurora", "lucent", "velvet", "quaint", "mystic", "arcane", "divine",
    "radiant", "serene", "boreal", "glacial", "frigid", "torrid", "fervid",
    "ardent", "fervent", "zealot", "sublime", "mesmer", "trance", "reverie",
    "fantasy", "vision", "mirage", "wander", "voyage", "journey", "quest",
    "odyssey", "pilgrim", "pioneer", "voyager", "wayfarer", "drifter",
    "nomad", "wanderer",
    "aaaaa", "aaaaaa", "bbbbb", "bbbbbb", "ccccc", "cccccc",
    "ddddd", "dddddd", "eeeee", "eeeeee", "fffff", "ffffff",
    "ggggg", "gggggg", "hhhhh", "hhhhhh", "iiiii", "iiiiii",
    "jjjjj", "jjjjjj", "kkkkk", "kkkkkk", "lllll", "llllll",
    "mmmmm", "mmmmmm", "nnnnn", "nnnnnn", "ooooo", "oooooo",
    "ppppp", "pppppp", "qqqqq", "qqqqqq", "rrrrr", "rrrrrr",
    "sssss", "ssssss", "ttttt", "tttttt", "uuuuu", "uuuuuu",
    "vvvvv", "vvvvvv", "wwwww", "wwwwww", "xxxxx", "xxxxxx",
    "yyyyy", "yyyyyy", "zzzzz", "zzzzzz",
    "terrorist", "dubai", "miami", "france",
    "egoist", "code10",
    "repeat", "luxury", "nightmare", "seasons", "nights", "season",
    "melon", "mango", "lemon", "grape", "berry", "dough", "flour", "wheat",
    "yeast", "mocha", "latte", "toast", "grill", "roast", "steak", "curry",
    "chili", "tacos", "fries", "snack", "meal", "brunch", "supper", "dinner",
    "lunch", "feast", "spice", "sugar", "honey", "candy", "cream", "bread",
    "cocoa", "salad", "sauce", "salsa", "pasta", "pizza", "sushi", "bacon",
    "juice", "wafer", "toffee", "biscuit", "coffee",
    "wealth", "richer", "palace", "castle", "throne", "royal", "regal",
    "noble", "satin", "tiara", "brooch", "cameo", "caviar", "opulent",
    "classy",
    "nightly", "fright", "scared", "afraid", "scream", "shriek", "darkly",
    "dismal", "morbid",
    "winter", "fall", "snowy", "frozen", "rainy", "cloudy", "stormy",
    "windy",
    "fashion", "style", "trend", "vogue", "beauty", "poise",
    "lilith", "azrael", "archon", "aether", "helios", "selene", "artemis",
    "athena", "apollo", "hermes", "hades", "poseid", "cronus", "themis",
    "hestia", "demeter", "orpheus", "icarus", "pegasus", "chimera", "medusa",
    "gorgon", "siren", "nymph", "dryad", "naiad", "oread", "satyr", "triton",
    "nereid", "cerber", "charon", "lethe", "tartar", "delphi", "ithaca",
    "sparta", "thebes", "attica", "rhodes", "lesbos", "hydra", "naxos",
    "milos", "corfu", "solace", "cirrus", "cumul", "stratu", "nimbus",
    "occid", "orient", "zenith", "nadir", "vertex", "vortex", "helix",
    "spiral", "levan", "foehn", "khamsi", "ember", "cinder", "flint",
    "forge", "anvil", "hammer", "quench", "temper", "molten", "ignite",
    "kindle", "blaze", "sorrow", "lament", "dirge", "eulogy", "anthem",
    "carol", "chant", "litany", "mantra", "prayer", "psalm", "sutra",
    "riddle", "enigma", "cipher", "codex", "glyph", "sigil", "talis",
    "charm", "amulet", "relic", "totem", "fetish", "symbol", "emblem",
    "crest", "insign", "banner", "ensign", "signal", "beacon", "torch",
    "candle", "ether", "quint", "psyche", "anima", "animus", "libido",
    "thanat", "logos", "mythos", "pathos", "ethos", "kairos", "telos",
    "arche", "gnosis", "sophia", "pistis", "elpis", "agape", "philos",
    "storge", "pragma", "mania", "ludus", "philia",
    "known", "unknown", "slark", "unravelesq", "thread",
    "paindealer", "fakov", "hfjsksjfjxkz764", "resetess6",
]

# === ФИЛЬТР: оставляем только слова 5+ букв ===
DOMAINS = [d for d in DOMAINS if len(d) >= 5]


def load_json(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(filename, data):
    tmp = filename + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(tmp, filename)


def load_tokens():
    tokens = []

    for token in VK_TOKENS:
        if isinstance(token, str):
            token = token.strip()

            if token:
                tokens.append(token)

    tokens = tokens[:MAX_TOKENS]

    if not tokens:
        raise RuntimeError("Нет VK токенов")

    return tokens


def load_domains():
    result = []
    seen = set()

    for domain in DOMAINS:
        if not isinstance(domain, str):
            continue

        domain = domain.strip().lower()

        if not domain:
            continue

        domain = domain.replace("https://", "")
        domain = domain.replace("http://", "")
        domain = domain.replace("www.vk.com/", "")
        domain = domain.replace("vk.com/", "")
        domain = domain.lstrip("@")
        domain = domain.rstrip("/")

        if domain and domain not in seen:
            seen.add(domain)
            result.append(domain)

    return result


def owner_number(object_id):
    if object_id is None:
        return "FREE"

    return str(object_id)


def owner_url(object_type, object_id):
    if object_id is None:
        return "FREE"

    if object_type == "user":
        return f"vk.com/id{object_id}"

    if object_type in ("group", "page"):
        return f"vk.com/club{object_id}"

    if object_type == "application":
        return f"vk.com/app{object_id}"

    return f"vk.com/{object_type}{object_id}"


async def setup_telegram():
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getMe"

    connector = ProxyConnector.from_url(TG_PROXY)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as response:

                if response.status != 200:
                    raise RuntimeError("Неверный Telegram Bot Token")

                data = await response.json(content_type=None)

                if not data.get("ok"):
                    raise RuntimeError("Неверный Telegram Bot Token")

                print(f"[TG] Прокси OK: {TG_PROXY}")

    except Exception as e:
        raise RuntimeError(f"Telegram недоступен через прокси: {e}")

    return TG_BOT_TOKEN, TG_CHAT_ID


async def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    connector = ProxyConnector.from_url(TG_PROXY)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, data=payload) as response:

                if response.status != 200:
                    print(f"[TG ERROR] HTTP {response.status}")
                    return False

                data = await response.json(content_type=None)

                if not data.get("ok"):
                    print(f"[TG ERROR] {data}")
                    return False

                return True

    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False


async def fetch_domain(session, domain, token):
    await asyncio.sleep(random.uniform(0.02, 0.08))

    params = {
        "screen_name": domain,
        "access_token": token,
        "v": VK_API_VERSION
    }

    try:
        async with session.get(
            VK_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        ) as response:

            if response.status != 200:
                return {"ok": False, "error": f"http_{response.status}"}

            data = await response.json(content_type=None)

    except asyncio.TimeoutError:
        return {"ok": False, "error": "timeout"}

    except aiohttp.ClientError:
        return {"ok": False, "error": "network"}

    except Exception:
        return {"ok": False, "error": "exception"}

    if "error" in data:
        return {"ok": False, "error": "vk_error"}

    response_data = data.get("response")

    if not response_data:
        return {"ok": True, "object_id": None, "object_type": None}

    object_id = response_data.get("object_id")
    object_type = response_data.get("type")

    if object_id is None:
        return {"ok": True, "object_id": None, "object_type": None}

    try:
        object_id = int(object_id)
    except Exception:
        pass

    return {
        "ok": True,
        "object_id": object_id,
        "object_type": object_type
    }


async def verify_change(session, domain, expected_id, token):
    result = await fetch_domain(session, domain, token)

    if not result["ok"]:
        return None

    if result["object_id"] == expected_id:
        return result

    return None


async def run_pass(session, domains, tokens, state, semaphore):
    notifications = []

    async def check_one(index, domain):

        async with semaphore:

            token_index = index % len(tokens)
            token = tokens[token_index]

            current = await fetch_domain(session, domain, token)

            if not current["ok"]:
                return

            current_id = current["object_id"]
            current_type = current["object_type"]

            old = state.get(domain)

            if old is None:
                state[domain] = {
                    "object_id": current_id,
                    "object_type": current_type
                }
                return

            last_id = old.get("object_id")
            last_type = old.get("object_type")

            if current_id == last_id:
                if current_type != last_type:
                    state[domain] = {
                        "object_id": current_id,
                        "object_type": current_type
                    }
                return

            if last_id is not None and current_id is None:
                state[domain] = {
                    "object_id": None,
                    "object_type": None
                }

                notifications.append(
                    "Detected release!\n"
                    f"{domain}: "
                    f"{owner_number(last_id)} → FREE"
                )
                return

            if last_id is None and current_id is not None:

                if len(tokens) > 1:
                    verify_token = tokens[(token_index + 1) % len(tokens)]
                else:
                    verify_token = token

                verified = await verify_change(
                    session, domain, current_id, verify_token
                )

                if verified is None:
                    return

                new_type = verified["object_type"]

                state[domain] = {
                    "object_id": current_id,
                    "object_type": new_type
                }

                notifications.append(
                    "Detected swap!\n"
                    f"{domain}: FREE → "
                    f"{owner_url(new_type, current_id)}"
                )
                return

            if (
                last_id is not None
                and current_id is not None
                and current_id != last_id
            ):
                if len(tokens) > 1:
                    verify_token = tokens[(token_index + 1) % len(tokens)]
                else:
                    verify_token = token

                verified = await verify_change(
                    session, domain, current_id, verify_token
                )

                if verified is None:
                    return

                new_type = verified["object_type"]

                state[domain] = {
                    "object_id": current_id,
                    "object_type": new_type
                }

                notifications.append(
                    "Detected swap!\n"
                    f"{domain}: "
                    f"{owner_number(last_id)} → "
                    f"{owner_url(new_type, current_id)}"
                )
                return

    tasks = []

    for index, domain in enumerate(domains):
        tasks.append(asyncio.create_task(check_one(index, domain)))

    await asyncio.gather(*tasks)

    return notifications


async def main():
    tokens = load_tokens()
    domains = load_domains()
    state = load_json(STATE_FILE, {})

    print(f"Загружено доменов: {len(domains)}")
    print(f"Загружено токенов: {len(tokens)}")

    connector = aiohttp.TCPConnector(
        limit=200,
        limit_per_host=200,
        ttl_dns_cache=3600,
        enable_cleanup_closed=True,
        keepalive_timeout=300,
        force_close=False,
        happy_eyeballs_delay=0.25
    )

    timeout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        bot_token, chat_id = await setup_telegram()

        print("The start checker")

        while True:
            notifications = await run_pass(
                session=session,
                domains=domains,
                tokens=tokens,
                state=state,
                semaphore=asyncio.Semaphore(CONCURRENCY)
            )

            save_json(STATE_FILE, state)

            if notifications:
                send_tasks = []

                for message in notifications:
                    send_tasks.append(
                        asyncio.create_task(
                            send_telegram(
                                bot_token,
                                chat_id,
                                message
                            )
                        )
                    )

                await asyncio.gather(*send_tasks, return_exceptions=True)

            await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
