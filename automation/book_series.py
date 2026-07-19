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

    # ── 5 ─ Mindset (Carol Dweck) ────────────────────────────────────────────
    {
        "book_title": "Mindset",
        "book_author": "Carol Dweck",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Mindset",
            "hook": "Zwei Wörter entscheiden, ob du wächst: 'noch nicht'.",
            "script": [
                "Zwei Wörter entscheiden, ob du wächst: 'noch nicht'.",
                "Nicht 'ich kann das nicht' — sondern 'ich kann das noch nicht'.",
                "Talent ist der Start. Haltung ist der Weg.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "person learning practice growth calm cinematic dark",
            "caption": ("Carol Dweck unterscheidet zwei Denkweisen: das starre und das "
                        "wachstumsorientierte Mindset.\n\n"
                        "Wer glaubt, Fähigkeiten seien fest, gibt bei Widerstand auf. Wer "
                        "glaubt, man kann wachsen, sieht im Scheitern eine Etappe.\n\n"
                        "Wo sagst du ab heute 'noch nicht'?\n\n"
                        "#mindset #caroldweck #growthmindset #wachstumsdenken #lernen "
                        "#disziplin #selbstentwicklung #persönlichkeitsentwicklung #resilienz "
                        "#buchtipp #lesen #motivation #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Mindset", "Sag: noch nicht", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Mindset",
            "hook": "3 Ideen aus Mindset",
            "pexels_queries": ["person practice learning dark", "seedling growth light",
                               "stairs climbing calm", "notebook progress hands",
                               "sunrise path forward", "mountain climb perspective"],
            "slides": [
                {"is_cover": True,
                 "title": ["Mindset", "in 3 Ideen"],
                 "body": ["Warum deine Haltung", "über dein Wachstum entscheidet.", "Weiterwischen ›"]},
                {"title": ["1 · Fest vs. wachsend"],
                 "body": ["'Ich bin so' bremst.", "'Ich kann werden' öffnet."]},
                {"title": ["2 · Scheitern = Daten"],
                 "body": ["Ein Rückschlag ist keine", "Bewertung deiner Person —", "nur Feedback."]},
                {"title": ["3 · Das Wort 'noch'"],
                 "body": ["'Ich kann das noch nicht'", "hält die Tür offen."]},
                {"title": ["Dein Zug"],
                 "body": ["Wo tauschst du 'nicht'", "gegen 'noch nicht'?", "Speicher dir das ›"]},
            ],
            "caption": ("Mindset von Carol Dweck — drei Ideen über die Haltung, die "
                        "Wachstum erst möglich macht.\n\n"
                        "Nicht was du kannst, entscheidet — sondern ob du glaubst, dass "
                        "du dich entwickeln kannst.\n\n"
                        "Speicher dir den Post.\n\n"
                        "#mindset #growthmindset #wachstumsdenken #lernen #resilienz "
                        "#disziplin #selbstentwicklung #buchtipp #klarheit #motivation "
                        "#lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Mindset", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "growth learning practice calm dark",
            "quote": {"text": "Wird man durch Anstrengung nicht schlauer, "
                              "hat man die falsche Anstrengung gewählt.",
                      "author": "Carol Dweck"},
            "tips": {"title": "Wachstums-Mindset üben",
                     "items": ["Häng ein 'noch' an jedes 'ich kann nicht'.",
                               "Frag nach Feedback, nicht nach Lob.",
                               "Feiere Anstrengung, nicht nur Ergebnis."]},
        },
    },

    # ── 6 ─ Meditationen (Marc Aurel) ────────────────────────────────────────
    {
        "book_title": "Meditationen",
        "book_author": "Marc Aurel",
        "content_pillar": "emotional",
        "reel": {
            "topic": "mentviro liest: Meditationen",
            "hook": "Du hast Macht über deinen Geist — nicht über die Ereignisse.",
            "script": [
                "Du hast Macht über deinen Geist — nicht über die Ereignisse.",
                "Marc Aurel schrieb das für sich selbst, nicht fürs Publikum.",
                "Kümmere dich um das, was du steuern kannst. Lass den Rest los.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "calm stoic sunrise mountains solitude warm cinematic",
            "caption": ("Die Meditationen von Marc Aurel sind kein Buch fürs Publikum — "
                        "es sind private Notizen eines Kaisers an sich selbst.\n\n"
                        "Der Kern der Stoa: unterscheide, was in deiner Macht liegt und "
                        "was nicht. Deine Energie gehört nur ins Erste.\n\n"
                        "Worüber ärgerst du dich, das du gar nicht steuern kannst?\n\n"
                        "#meditationen #marcaurel #stoizismus #gelassenheit #mindset "
                        "#selbstreflexion #philosophie #ruhe #achtsamkeit #buchtipp "
                        "#lesen #charakter #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Meditationen", "Steuer, was du kannst", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Meditationen",
            "hook": "3 Ideen aus Marc Aurels Meditationen",
            "pexels_queries": ["stoic sunrise mountains warm", "calm ocean vast",
                               "candle quiet reflection", "path solitude nature",
                               "sky clouds perspective", "stone still water"],
            "slides": [
                {"is_cover": True,
                 "title": ["Meditationen", "in 3 Ideen"],
                 "body": ["Stoische Ruhe von einem,", "der ein Reich regierte.", "Weiterwischen ›"]},
                {"title": ["1 · Deine Macht"],
                 "body": ["Ereignisse steuerst du nicht.", "Deine Reaktion schon."]},
                {"title": ["2 · Der Moment reicht"],
                 "body": ["Du verlierst nie die", "Vergangenheit oder Zukunft —", "nur das Jetzt zählt."]},
                {"title": ["3 · Das Hindernis ist der Weg"],
                 "body": ["Was dir im Weg steht,", "wird zum Weg selbst."]},
                {"title": ["Dein Zug"],
                 "body": ["Was lässt du heute los,", "weil es nicht dir gehört?", "Speicher dir das ›"]},
            ],
            "caption": ("Meditationen von Marc Aurel — drei stoische Ideen für mehr "
                        "Gelassenheit.\n\n"
                        "Fast 2000 Jahre alt und aktueller denn je: Ruhe entsteht, wo du "
                        "aufhörst, das Unkontrollierbare kontrollieren zu wollen.\n\n"
                        "Speicher dir den Post für hektische Tage.\n\n"
                        "#meditationen #marcaurel #stoizismus #gelassenheit #mindset "
                        "#philosophie #achtsamkeit #ruhe #selbstreflexion #buchtipp #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Meditationen", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "stoic calm sunrise warm reflective",
            "quote": {"text": "Du hast Macht über deinen Geist — nicht über äußere "
                              "Ereignisse. Erkenne das, und du findest Kraft.",
                      "author": "Marc Aurel"},
            "tips": {"title": "Stoisch bleiben",
                     "items": ["Trenne: kann ich es steuern — ja oder nein?",
                               "Reagiere erst, wenn der erste Impuls vorbei ist.",
                               "Frag dich abends: was habe ich heute gut gemacht?"]},
        },
    },

    # ── 7 ─ Die 7 Wege zur Effektivität (Stephen Covey) ──────────────────────
    {
        "book_title": "Die 7 Wege zur Effektivität",
        "book_author": "Stephen Covey",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Die 7 Wege zur Effektivität",
            "hook": "Die meisten sind beschäftigt mit dem Dringenden — nie mit dem Wichtigen.",
            "script": [
                "Die meisten sind beschäftigt mit dem Dringenden — nie mit dem Wichtigen.",
                "Covey sagt: beginne mit dem Ende im Kopf.",
                "Erst das Wichtige planen, dann läuft der Rest.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "planning notebook priorities calm minimal cinematic dark",
            "caption": ("Stephen Covey zeigt in Die 7 Wege zur Effektivität: Erfolg ist "
                        "kein Zufall, sondern eine Handvoll Prinzipien.\n\n"
                        "Das stärkste: das Wichtige zuerst. Nicht das Lauteste gewinnt, "
                        "sondern das, was dich deinem Ziel näherbringt.\n\n"
                        "Was ist heute wichtig — nicht nur dringend?\n\n"
                        "#die7wege #stephencovey #produktivität #prioritäten #mindset "
                        "#disziplin #selbstführung #zielsetzung #selbstentwicklung #buchtipp "
                        "#lesen #klarheit #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Die 7 Wege", "Wichtig vor dringend", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Die 7 Wege zur Effektivität",
            "hook": "3 Ideen aus Die 7 Wege",
            "pexels_queries": ["planning desk priorities dark", "compass direction calm",
                               "calendar time focus", "path clear forward",
                               "notebook goals hands", "sunrise horizon plan"],
            "slides": [
                {"is_cover": True,
                 "title": ["Die 7 Wege", "in 3 Ideen"],
                 "body": ["Zeitlose Prinzipien für", "ein wirksames Leben.", "Weiterwischen ›"]},
                {"title": ["1 · Sei proaktiv"],
                 "body": ["Zwischen Reiz und Reaktion", "liegt deine Freiheit."]},
                {"title": ["2 · Ende im Kopf"],
                 "body": ["Kenne dein Ziel,", "bevor du den ersten", "Schritt machst."]},
                {"title": ["3 · Wichtig vor dringend"],
                 "body": ["Plane das Wichtige zuerst —", "das Dringende schreit eh."]},
                {"title": ["Dein Zug"],
                 "body": ["Was ist dein wichtigster", "Schritt diese Woche?", "Speicher dir das ›"]},
            ],
            "caption": ("Die 7 Wege zur Effektivität von Stephen Covey — drei Prinzipien, "
                        "die bleiben.\n\n"
                        "Effektiv ist nicht, wer am meisten tut, sondern wer das Richtige "
                        "zuerst tut.\n\n"
                        "Speicher dir den Post für deine Wochenplanung.\n\n"
                        "#die7wege #stephencovey #produktivität #prioritäten #selbstführung "
                        "#disziplin #zielsetzung #mindset #buchtipp #klarheit #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Die 7 Wege", "3 Ideen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "priorities planning focus calm dark",
            "quote": {"text": "Das Wichtigste ist, das Wichtigste wichtig zu halten.",
                      "author": "Stephen Covey"},
            "tips": {"title": "Wichtig vor dringend",
                     "items": ["Plane die großen Steine zuerst in die Woche.",
                               "Frag: bringt mich das meinem Ziel näher?",
                               "Sag Nein zum Dringenden ohne Bedeutung."]},
        },
    },

    # ── 8 ─ Die Kunst des klaren Denkens (Rolf Dobelli) ──────────────────────
    {
        "book_title": "Die Kunst des klaren Denkens",
        "book_author": "Rolf Dobelli",
        "content_pillar": "educational",
        "reel": {
            "topic": "mentviro liest: Die Kunst des klaren Denkens",
            "hook": "Du triffst schlechtere Entscheidungen, als du denkst. Systematisch.",
            "script": [
                "Du triffst schlechtere Entscheidungen, als du denkst. Systematisch.",
                "Dobelli sammelt die Denkfehler, in die wir alle tappen.",
                "Wer die Fallen kennt, umgeht sie — das ist der halbe Weg.",
                "Folge @mentviro.",
            ],
            "pexels_video_query": "chess thinking decision minimal calm cinematic dark",
            "caption": ("Rolf Dobelli sammelt in Die Kunst des klaren Denkens die "
                        "Denkfehler, die uns allen passieren.\n\n"
                        "Zum Beispiel der Sunk-Cost-Effekt: Wir bleiben bei etwas, nur weil "
                        "wir schon investiert haben — nicht weil es klug ist.\n\n"
                        "Welchen Denkfehler erkennst du bei dir?\n\n"
                        "#klaresdenken #rolfdobelli #denkfehler #mindset #entscheidungen "
                        "#psychologie #selbstreflexion #klarheit #rationalität #buchtipp "
                        "#lesen #wachstum #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Klares Denken", "Kenne die Denkfallen", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "mentviro liest: Die Kunst des klaren Denkens",
            "hook": "3 Denkfehler aus dem Buch",
            "pexels_queries": ["chess strategy dark", "brain thinking abstract",
                               "crossroads decision calm", "magnifier detail focus",
                               "path choice forest", "balance scale minimal"],
            "slides": [
                {"is_cover": True,
                 "title": ["Klares Denken", "— 3 Denkfehler"],
                 "body": ["Die Fallen, in die", "wir alle tappen.", "Weiterwischen ›"]},
                {"title": ["1 · Sunk-Cost"],
                 "body": ["Du bleibst dabei, weil du", "schon investiert hast —", "nicht weil es klug ist."]},
                {"title": ["2 · Bestätigungsfehler"],
                 "body": ["Du siehst nur, was deine", "Meinung stützt.", "Such das Gegenteil."]},
                {"title": ["3 · Verfügbarkeit"],
                 "body": ["Was dir leicht einfällt,", "hältst du für häufig.", "Stimmt oft nicht."]},
                {"title": ["Dein Zug"],
                 "body": ["Welchen Denkfehler", "erkennst du bei dir?", "Speicher dir das ›"]},
            ],
            "caption": ("Die Kunst des klaren Denkens von Rolf Dobelli — drei Denkfehler, "
                        "die du ab jetzt erkennst.\n\n"
                        "Klüger entscheiden heißt nicht, mehr zu wissen — sondern die "
                        "eigenen Fallen zu kennen.\n\n"
                        "Speicher dir den Post.\n\n"
                        "#klaresdenken #denkfehler #psychologie #entscheidungen #mindset "
                        "#selbstreflexion #klarheit #rationalität #buchtipp #wachstum #lesen #mentviro"),
            "story_text": ["MENTVIRO LIEST", "Klares Denken", "3 Denkfehler", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "thinking decision clarity calm dark",
            "quote": {"text": "Wir denken selten nach, was wir denken sollten, "
                              "und noch seltener, wie wir denken.",
                      "author": "Rolf Dobelli"},
            "tips": {"title": "Klarer entscheiden",
                     "items": ["Frag: würde ich heute neu so einsteigen?",
                               "Such aktiv das Gegenargument zu deiner Meinung.",
                               "Schlaf eine Nacht über große Entscheidungen."]},
        },
    },
]
