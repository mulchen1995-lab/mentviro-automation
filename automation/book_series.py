# -*- coding: utf-8 -*-
"""
Buch-Serie "mentviro liest" für @mentviro.

Wiederkehrendes Serien-Format: 1 Buch -> die stärksten MINDSET-Ideen daraus,
kurz & knackig. Gibt dem Account Wiedererkennung ("Teil 2"-Effekt), zeigt Julian
als jemanden, der lernt, und ist eine natürliche Brücke zu O&M ("willst du tiefer
einsteigen?") — OHNE Renditeversprechen.

RICHTLINIEN (PFLICHT, siehe mentviro IG Richtlinien):
- Nur die DENK-/Mindset-Lektionen der Bücher, NIE konkrete Finanzprodukte,
  ETF-Namen, Rendite-/Gewinnzahlen, Steuer-Tricks oder "verdiene X".
- Money-Bücher (z.B. Rich Dad Poor Dad) ausschließlich als MINDSET framen
  (Denkweise, Bildung, Disziplin) — das Konto hatte eine Finanz-/Scam-Einschränkung.
- Keine Links in Captions, kein FOMO/Dringlichkeit, keine unbelegbaren Claims.

Schema pro Package = exakt das Gemini/Evergreen-Schema, PLUS zwei Felder für die
Serien-Identität: "book_title" und "book_author". Die Episoden-Nummer (#N) wird
NICHT hier gespeichert, sondern von _seed_book_series() zur Laufzeit injiziert
(in Caption + story_text), damit die Zählung automatisch fortläuft.

Reel-Skripte bewusst KURZ (2-3 Sätze + "Folge @mentviro.") — kurze
Aufmerksamkeitsspanne.
"""

BOOK_SERIES = [
    # ── 1 ─ Atomic Habits ────────────────────────────────────────────────────
    {
        "book_title": "Atomic Habits",
        "book_author": "James Clear",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Atomic Habits",
            "hook": "Du steigst nicht auf das Niveau deiner Ziele.",
            "script": [
                "Du steigst nicht auf das Niveau deiner Ziele.",
                "Du fällst auf das Niveau deiner Systeme.",
                "Bau das System — das Ziel folgt von allein.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "minimal desk morning routine calm cinematic dark",
            "caption": ("James Clear bringt es auf den Punkt: nicht Motivation formt "
                        "dich, sondern deine täglichen Systeme.\n\n"
                        "1 % besser pro Tag klingt nach nichts — nach einem Jahr bist "
                        "du ein anderer Mensch.\n\n"
                        "Welches winzige System baust du ab heute?\n\n"
                        "#atomichabits #jamesclear #gewohnheiten #mindset #disziplin "
                        "#selbstentwicklung #1prozent #routine #fokus #buchtipp "
                        "#persönlichkeitsentwicklung #wachstum #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Atomic Habits", "Systeme schlagen Ziele", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Atomic Habits",
            "hook": "3 Ideen aus Atomic Habits",
            "pexels_queries": ["minimal desk focus dark", "stairs climbing light",
                               "notebook writing hands", "sunrise horizon calm",
                               "path forest direction", "morning routine calm"],
            "slides": [
                {"is_cover": True,
                 "title": ["Atomic Habits", "in 3 Ideen"],
                 "body": ["Das Buch, das Gewohnheiten", "endlich erklärt.", "Weiterwischen ›"]},
                {"title": ["1 · Systeme > Ziele"],
                 "body": ["Ziele geben die Richtung.", "Systeme bringen dich hin."]},
                {"title": ["2 · 1 % pro Tag"],
                 "body": ["Kleine Schritte summieren sich.", "Konsistenz schlägt Intensität."]},
                {"title": ["3 · Identität zuerst"],
                 "body": ["Nicht 'ich will laufen'.", "Sondern 'ich bin jemand,", "der läuft'."]},
                {"title": ["Dein Zug"],
                 "body": ["Welche eine Gewohnheit", "baust du ab heute?", "Speicher dir das ›"]},
            ],
            "caption": ("Atomic Habits von James Clear — drei Ideen, die hängenbleiben.\n\n"
                        "Du wirst nicht durch den großen Sprung besser, sondern durch "
                        "das, was du jeden Tag wiederholst.\n\n"
                        "Speicher dir den Post für die Tage ohne Motivation.\n\n"
                        "#atomichabits #gewohnheiten #mindset #disziplin #selbstentwicklung "
                        "#buchtipp #routine #fokus #wachstum #klarheit #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Atomic Habits", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "discipline habits focus calm dark",
            "quote": {"text": "Du wirst nie das Niveau deiner Ziele erreichen. "
                              "Du fällst auf das Niveau deiner Systeme.",
                      "author": "James Clear"},
            "tips": {"title": "System statt Willenskraft",
                     "items": ["Mach den ersten Schritt lächerlich klein.",
                               "Häng die neue Gewohnheit an eine alte.",
                               "Miss Dranbleiben, nicht Perfektion."]},
        },
    },

    # ── 2 ─ Deep Work ────────────────────────────────────────────────────────
    {
        "book_title": "Deep Work",
        "book_author": "Cal Newport",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Deep Work",
            "hook": "Fokus ist die neue Superkraft.",
            "script": [
                "Fokus ist die neue Superkraft.",
                "Wer ungestört tief arbeiten kann, schlägt die, die nur beschäftigt sind.",
                "Schütze deine Konzentration wie dein wertvollstes Gut.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "focused work desk lamp night minimal cinematic",
            "caption": ("Cal Newport nennt es Deep Work: die Fähigkeit, ohne Ablenkung "
                        "an einer schweren Sache zu arbeiten.\n\n"
                        "In einer Welt voller Benachrichtigungen ist genau das selten — "
                        "und deshalb so wertvoll.\n\n"
                        "Wann hattest du zuletzt 90 Minuten echten Fokus?\n\n"
                        "#deepwork #calnewport #fokus #produktivität #konzentration "
                        "#mindset #disziplin #selbstentwicklung #deeplife #buchtipp "
                        "#lesen #klarheit #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Deep Work", "Fokus ist Superkraft", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Deep Work",
            "hook": "3 Ideen aus Deep Work",
            "pexels_queries": ["focused desk lamp night", "phone face down minimal",
                               "clock time calm", "notebook plan hands",
                               "quiet room window light", "mountain focus horizon"],
            "slides": [
                {"is_cover": True,
                 "title": ["Deep Work", "in 3 Ideen"],
                 "body": ["Warum Fokus dein größter", "Vorteil ist.", "Weiterwischen ›"]},
                {"title": ["1 · Tief statt breit"],
                 "body": ["Eine Sache mit voller", "Aufmerksamkeit schlägt zehn", "halb erledigte."]},
                {"title": ["2 · Ablenkung kostet"],
                 "body": ["Jeder Blick aufs Handy", "reißt dich raus.", "Zurück dauert Minuten."]},
                {"title": ["3 · Feste Fokus-Blöcke"],
                 "body": ["Plane Zeit, in der du", "unerreichbar bist.", "Behandle sie wie einen Termin."]},
                {"title": ["Dein Zug"],
                 "body": ["Wann ist dein nächster", "90-Minuten-Fokus-Block?", "Speicher dir das ›"]},
            ],
            "caption": ("Deep Work von Cal Newport — drei Ideen, die deinen Arbeitstag "
                        "verändern.\n\n"
                        "Nicht mehr Stunden gewinnen das Spiel, sondern tiefere Stunden.\n\n"
                        "Speicher dir den Post für deinen nächsten Fokus-Block.\n\n"
                        "#deepwork #fokus #produktivität #konzentration #mindset #disziplin "
                        "#selbstentwicklung #buchtipp #klarheit #zeitmanagement #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Deep Work", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "focus deep work calm night desk",
            "quote": {"text": "Klarheit über das Wesentliche entsteht nur, "
                              "wenn man die Ablenkung wegräumt.",
                      "author": "Cal Newport"},
            "tips": {"title": "Fokus schützen",
                     "items": ["Handy in einen anderen Raum legen.",
                               "Einen festen Fokus-Block pro Tag planen.",
                               "Nach der Arbeit klar abschalten."]},
        },
    },

    # ── 3 ─ Ego is the Enemy ─────────────────────────────────────────────────
    {
        "book_title": "Ego is the Enemy",
        "book_author": "Ryan Holiday",
        "content_pillar": "emotional",
        "reel": {
            "topic": "mentviro liest: Ego is the Enemy",
            "hook": "Dein größter Gegner trägt dein Gesicht.",
            "script": [
                "Dein größter Gegner trägt dein Gesicht.",
                "Das Ego will Applaus — Wachstum will Wahrheit.",
                "Bleib Schüler, auch wenn alle dich Meister nennen.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "solitary figure calm nature reflective warm cinematic",
            "caption": ("Ryan Holiday zeigt in Ego is the Enemy: nicht die Konkurrenz "
                        "bremst dich am meisten — dein eigenes Ego tut es.\n\n"
                        "Wer immer recht haben will, hört auf zu lernen.\n\n"
                        "Wo stand dir dein Ego zuletzt im Weg?\n\n"
                        "#egoistheenemy #ryanholiday #stoizismus #demut #mindset "
                        "#selbstreflexion #wachstum #persönlichkeitsentwicklung #lernen "
                        "#buchtipp #lesen #charakter #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Ego is the Enemy", "Bleib Schüler", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Ego is the Enemy",
            "hook": "3 Ideen aus Ego is the Enemy",
            "pexels_queries": ["solitary figure nature warm", "mirror reflection calm",
                               "sunrise humble horizon", "hands open light",
                               "path uphill quiet", "ocean vast perspective"],
            "slides": [
                {"is_cover": True,
                 "title": ["Ego is the Enemy", "in 3 Ideen"],
                 "body": ["Warum dein Ego dich", "kleiner hält als du denkst.", "Weiterwischen ›"]},
                {"title": ["1 · Bleib Schüler"],
                 "body": ["Wer glaubt, es zu wissen,", "hört auf zu lernen."]},
                {"title": ["2 · Arbeit vor Applaus"],
                 "body": ["Verliebe dich in die Arbeit,", "nicht in die Anerkennung."]},
                {"title": ["3 · Ruhe statt Beweisen"],
                 "body": ["Du musst nicht jedem", "zeigen, dass du recht hast."]},
                {"title": ["Dein Zug"],
                 "body": ["Wo darf dein Ego", "heute mal leiser sein?", "Speicher dir das ›"]},
            ],
            "caption": ("Ego is the Enemy von Ryan Holiday — drei Ideen über Demut "
                        "und Wachstum.\n\n"
                        "Selbstvertrauen baut auf. Ego blendet. Der Unterschied "
                        "entscheidet, wie weit du kommst.\n\n"
                        "Speicher dir den Post als Erinnerung.\n\n"
                        "#egoistheenemy #stoizismus #demut #mindset #selbstreflexion "
                        "#wachstum #charakter #buchtipp #persönlichkeitsentwicklung "
                        "#lernen #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Ego is the Enemy", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "humility calm nature warm reflective",
            "quote": {"text": "Der Weg zu allem Großen führt durch das, "
                              "was man nicht sein will: bescheiden.",
                      "author": "Ryan Holiday"},
            "tips": {"title": "Ego im Zaum halten",
                     "items": ["Hör mehr zu, als du redest.",
                               "Feiere den Fortschritt anderer ehrlich.",
                               "Frag dich: will ich recht haben oder wachsen?"]},
        },
    },

    # ── 4 ─ Rich Dad Poor Dad (NUR Mindset-Lektionen) ────────────────────────
    # Wichtig: kein Asset/Liability-Rechnen, keine ETF/Rendite/Steuern — nur die
    # Denkweise. Money-Buch bewusst als Mindset-Bildung geframed.
    {
        "book_title": "Rich Dad Poor Dad",
        "book_author": "Robert Kiyosaki",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Rich Dad Poor Dad",
            "hook": "Die teuerste Lektion? Für Geld zu arbeiten, statt zu lernen.",
            "script": [
                "Die teuerste Lektion? Für Geld zu arbeiten, statt zu lernen.",
                "Kiyosaki sagt: nimm den Job, der dich am meisten lehrt.",
                "Investiere zuerst in dein Wissen — der Rest folgt.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "person reading book lamp calm minimal cinematic dark",
            "caption": ("Rich Dad Poor Dad wird oft aufs Geld reduziert — dabei ist die "
                        "stärkste Lektion eine Denkweise:\n\n"
                        "Arbeite am Anfang für Fähigkeiten, nicht nur für Gehalt. Wissen "
                        "ist das Fundament, auf dem alles andere steht.\n\n"
                        "Kein Finanzrat — nur Bildung. In welche Fähigkeit investierst du "
                        "gerade?\n\n"
                        "#richdadpoordad #mindset #finanziellebildung #lernen #disziplin "
                        "#selbstentwicklung #fähigkeiten #wachstum #buchtipp #klarheit "
                        "#lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Rich Dad Poor Dad", "Lernen vor Verdienen", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Rich Dad Poor Dad",
            "hook": "3 Mindset-Ideen aus Rich Dad Poor Dad",
            "pexels_queries": ["person reading book calm dark", "stairs growth light",
                               "notebook learning hands", "sunrise path calm",
                               "library books focus", "mountain climb perspective"],
            "slides": [
                {"is_cover": True,
                 "title": ["Rich Dad Poor Dad", "— 3 Mindset-Ideen"],
                 "body": ["Nicht übers Geld.", "Über die Denkweise dahinter.", "Weiterwischen ›"]},
                {"title": ["1 · Lernen vor Verdienen"],
                 "body": ["Nimm die Aufgabe, die dich", "am meisten lehrt —", "am Anfang zählt das mehr."]},
                {"title": ["2 · Wissen zuerst"],
                 "body": ["Bücher, Mentoren, Erfahrung.", "Deine Sichtweise ändert sich —", "und damit dein Handeln."]},
                {"title": ["3 · Angst & Faulheit"],
                 "body": ["Kiyosaki nennt die Hürden:", "Angst, Zynismus, Faulheit,", "Arroganz. Erkennst du eine?"]},
                {"title": ["Dein Zug"],
                 "body": ["Kein Finanzrat — nur Bildung.", "In welche Fähigkeit", "investierst du? Speicher ›"]},
            ],
            "caption": ("Rich Dad Poor Dad von Robert Kiyosaki — bewusst die MINDSET-Ideen, "
                        "nicht die Zahlen.\n\n"
                        "Die wichtigste Botschaft ist eine Haltung: lerne, bevor du "
                        "verdienst, und hör nie auf, in dich zu investieren.\n\n"
                        "Kein Finanzrat — nur Bildung. Speicher dir den Post.\n\n"
                        "#richdadpoordad #mindset #finanziellebildung #lernen #selbstentwicklung "
                        "#disziplin #fähigkeiten #wachstum #buchtipp #klarheit #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Rich Dad Poor Dad", "3 Mindset-Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "learning books discipline calm dark",
            "quote": {"text": "Arbeite, um zu lernen — nicht nur, um zu verdienen.",
                      "author": "Robert Kiyosaki"},
            "tips": {"title": "In dich investieren",
                     "items": ["Wähle Aufgaben nach dem, was sie dich lehren.",
                               "Lies das eine Buch, das du aufschiebst.",
                               "Erkenne deine größte Hürde: Angst oder Faulheit?"]},
        },
    },
]
