import sqlite3

def create_drug_keywords_database(db_file="drug_keywords.db"):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY,
                category TEXT,
                keyword TEXT
            )
        """)
        conn.commit()
        print("Database and table created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()

# ✅ Function to clear existing keywords
def clear_keywords_table(db_file="drug_keywords.db"):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM keywords")
        conn.commit()
        print("✅ Cleared existing keywords.")
    except sqlite3.Error as e:
        print(f"Error clearing table: {e}")
    finally:
        conn.close()

# ✅ Function to insert an expanded set of phrases
def insert_phrase_based_keywords(db_file="drug_keywords.db"):
    keywords = {
        "Marijuana": [
            "picked up some weed", "selling loud packs", "flipping green", "trap full of bud",
            "cop a zip of bud", "dubs on the block", "moving green", "bag of herb", "grabbing loud",
            "pushing some bud", "zips of marijuana", "buying weed on the low", "selling weed",
            "quarter pound of loud", "plug dropped green", "got some gas", "blunts rolled up",
            "fire za in stock", "selling dubs", "picked up loud from my guy","zips of weed"
            "zip of loud on hand", "picked up tree", "sativa packs in bulk", "burning some fire",
            "quarter of kush", "trap smell like gas", "cop some green", "stash of loud", "grabbed a sack",
            "pre-roll drop", "got that cali pack", "bags of mid", "grabbed green from the block", "w33d", "za",
            "ganga"

        ],
        "Cocaine": [
            "got that premium snow", "picked up some coke", "shipment of blow", "cop a brick of yeyo",
            "moving powder downtown", "key of coke", "white girl on deck", "blow from the plug",
            "kilos of white", "reselling yeyo", "grabbed some snow", "whipping that snow",
            "bags of white", "cookin powder", "raw coke supply", "stash of snow", "powder bricks",
            "sniff and flip", "package full of yeyo", "china white", 
            "ran off with the white", "cutting up snow", "bumping lines all night", "stepped on coke",
            "plug delivered bricks", "dusty bag of powder", "riding dirty with yeyo", "stash full of white",
            "key of blow just landed", "breakin down powder", "bagged up the snow", "selling crack", "smoking crack",
            "doing crack", 

        ],
        "Oxycodone": [
            "plug dropped perks", "selling oxys", "picked up some oxycodone", "oxys at the trap",
            "street price for oxys", "moving perks", "oxycodone packs", "got some perks", "selling blues",
            "selling perks", "pressing oxy", "picked up blue 30s", "buying oxy on telegram", 
            "grabbing pills", "blues going for cheap", "running perks downtown",
            "blue 30s on deck", "rolling off oxys", "pressed oxys from the net", "buying roxies",
            "pills in the safe", "cop a script", "popped a perk 30", "hand to hand on perks",
            "caught a refill from the plug", "snorting pills", "bars and blues combo"

        ],
        "Fentanyl": [
            "shipped fetty in foil", "copped a fetty pack", "darknet connect shipped fetty",
            "got some fent", "fentanyl from china", "pressed fetty pills", "cut with fentanyl",
            "deadly fetty batch", "hidden fetty stash", "fent strips in the mail", "deal on fetty tabs",
            "foil packed fent", "buying fent through vendor"
            "batch laced with fetty", "fetty cut through the dope", "patches of fentanyl", 
            "pill press with fent", "getting fent from vendor", "lace the stash with fetty",
            "fent strip came in", "snuck fetty in socks", "deadly mix of fetty"

        ],
        "MDMA / Ecstasy": [
            "picked up molly", "scored molly for the party", "molly and perks", "party pack of mdma",
            "ecstasy tabs on deck", "rave drops", "plug laced me with molly", "rollin on mdma",
            "bags of molly", "pills dropped at the rave", "stack of tabs", "rave ready rolls",
            "buying molly for the weekend", "plug delivered tabs", "triple stacks on deck",
            "tabs for the rave", "stacked molly for the party", "rolling hard off mdma", 
            "flooded with ecstasy", "party favors dropped off", "capsules full of love",
            "mdma connect hit me", "ecstasy hits landed", "flipping molly at the show"

        ],
        "Heroin": [
            "got some h", "fresh batch of dope", "picked up heroin from the trap",
            "smack in the stash", "brown sugar shipment", "loaded up with dope", "bundle of heroin",
            "banging dope", "trap got h", "china white batch", "heroin bricks", "shootin up h",
            "cutting dope with fent", "dope bags dropped off", "dope got me noddin", "cookin up h", 
            "tie off and hit", "loaded spoon of brown", "selling bundles of smack", "smack hitting hard", "trap got china white",
            "banging dope again", "fresh bricks of heroin", "ziplocs of dope"

        ],
        "Sales / Pricing": [
            "flip fast", "wholesale price", "dime bags for sale", "street price is", "250 a zip",
            "ten a pop", "cheap per gram", "resell for profit", "buy low sell high", "bulk pricing available",
            "pricing by the ounce", "grams for the low", "under the table sale", "deal on packs",
            "stack up for resale", "running street deals", "two for twenty", "price goes up by the block",
            "price per point", "moving weight for cheap", "taxed on the re-up", "wholesale deal hit",
            "made a flip last night", "profit margin on packs", "asking ten a g", "cutting deals",
            "price got bumped", "bulk re-up discount"

        ],

        "Dealer / Communication": [
            "plug dropped off", "connect coming through", "yo you mobile",
             "my guy got fire", "text the plug", "tap in with the connect",
             "on standby for the drop", "you got the pack?", 
             "who got the plug?", 
             "hit the trap phone", "line always open", "plug just checked in",
             "burner blew up",
             "drop the location", "send the signal", "ghost the buyer",
             "deal going down tonight",
         ],


        "Distribution / Transport": [
            "move a few packs", "cop a few ounces", 
            "transporting dubs", "trap full of product", "flip this weight", "delivery on the low",
            "moving units", "cargo coming through", "stash spot locked", 
            "load up the car", "shipment just cleared customs", "courier on the move", "drop off at the corner",
            "carrying the stash", "boxed up the weight", "packing up for transport",
            "driver got the pack", "stash in the wheel well",
            "crossed state lines with the cargo", "re-up landed", "stuffed in a tire",
            "weight in the duffel", "loaded in the trunk", "sent it with the courier",
            "out-of-state drop", "moving through greyhound", "next-day pack coming in", "trap house",
            "secret drugs", "trap house"

        ]

    }



    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        for category, phrase_list in keywords.items():
            for phrase in phrase_list:
                cursor.execute("INSERT INTO keywords (category, keyword) VALUES (?, ?)", (category, phrase))

        conn.commit()
        print("✅ Phrase-based keywords inserted successfully.")

    except sqlite3.Error as e:
        print(f"❌ Error inserting keywords: {e}")
    finally:
        conn.close()


    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        for category, phrase_list in keywords.items():
            for phrase in phrase_list:
                cursor.execute("INSERT INTO keywords (category, keyword) VALUES (?, ?)", (category, phrase))

        conn.commit()
        print("Phrase-based keywords inserted successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()

clear_keywords_table()
create_drug_keywords_database()
insert_phrase_based_keywords()
