# -*- coding: utf-8 -*-
"""
Evergreen-Notfallpool für mentviro.

Wird von check_and_refill_content() NUR benutzt, wenn der Gemini-Generator
ausfällt (z. B. 429 Quota) UND der Content-Vorrat kritisch leer ist. Dann wird
aus diesem Pool nachgefüllt, damit der Account nicht dunkel wird.

Inhalt ist bewusst zeitlos (mindset / Disziplin / Fokus / Konsistenz) und
RICHTLINIENKONFORM (siehe mentviro IG Richtlinien):
- keine Renditeversprechen, kein FOMO / keine Dringlichkeit
- keine Links in Captions, keine konkreten Finanzprodukte
- keine unbelegbaren Claims

Jedes Package spiegelt exakt das Schema, das Gemini sonst liefert:
{ "content_pillar", "reel": {...}, "carousel": {...}, "stories": {...} }
"""

EVERGREEN_PACKAGES = [
    # ── 1 ─ Konsistenz schlägt Intensität ────────────────────────────────────
    {
        "content_pillar": "educational",
        "reel": {
            "topic": "Konsistenz schlägt Intensität",
            "hook": "Nicht das eine große Ding verändert dein Leben.",
            "script": [
                "Nicht das eine große Ding verändert dein Leben.",
                "Sondern das kleine Ding, das du jeden Tag tust.",
                "Motivation bringt dich an den Start.",
                "Routine bringt dich ins Ziel.",
                "Zehn Minuten täglich schlagen zehn Stunden einmal im Monat.",
                "Fang heute klein an und bleib dran.",
            ],
            "pexels_video_query": "person walking sunrise calm cinematic",
            "caption": ("Erfolg ist selten laut.\n\n"
                        "Meistens ist er die leise Entscheidung, heute wieder "
                        "anzufangen — auch ohne Applaus.\n\n"
                        "Welche kleine Sache machst du ab heute jeden Tag?"),
            "story_text": ["NEUER POST", "Konsistenz", "schlägt Intensität", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "Warum kleine Schritte gewinnen",
            "hook": "Warum kleine Schritte am Ende gewinnen",
            "pexels_queries": ["minimal desk focus", "stairs climbing light",
                               "morning routine calm", "notebook writing hands",
                               "path forest direction", "sunrise horizon calm"],
            "slides": [
                {"is_cover": True,
                 "title": ["Du brauchst keinen", "großen Sprung —", "nur den nächsten Schritt."],
                 "body": ["Warum Konsistenz gewinnt.", "Weiterwischen."]},
                {"title": ["1 % besser pro Tag"],
                 "body": ["klingt nach wenig.", "Nach einem Jahr bist du", "ein anderer Mensch."]},
                {"title": ["Der Fehler der meisten"],
                 "body": ["Sie starten zu groß", "und hören zu früh auf."]},
                {"title": ["Mach es so klein,"],
                 "body": ["dass du nicht Nein", "sagen kannst.", "Zwei Minuten reichen."]},
                {"title": ["Verpasst du einen Tag,"],
                 "body": ["ist das okay.", "Verpasse nie zwei", "hintereinander."]},
                {"title": ["Dranbleiben"],
                 "body": ["ist die Superkraft,", "über die niemand spricht.", "Speicher dir das."]},
            ],
            "caption": ("Disziplin ist nicht hart zu sich selbst zu sein.\n\n"
                        "Disziplin ist, sich selbst nicht im Stich zu lassen.\n\n"
                        "Speicher dir den Post für die Tage, an denen die "
                        "Motivation fehlt."),
            "story_text": ["NEUER POST", "Kleine Schritte", "gewinnen", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "discipline focus calm",
            "quote": {"text": "Du wirst nie das Niveau deiner Ziele erreichen. "
                              "Du fällst auf das Niveau deiner Systeme.",
                      "author": "Mindset"},
            "tips": {"title": "System statt Willenskraft",
                     "items": ["Mach den ersten Schritt lächerlich klein.",
                               "Lege eine feste Uhrzeit fest, kein Vielleicht.",
                               "Miss Dranbleiben, nicht Perfektion."]},
        },
    },

    # ── 2 ─ Klarheit vor Tempo ───────────────────────────────────────────────
    {
        "content_pillar": "educational",
        "reel": {
            "topic": "Klarheit vor Tempo",
            "hook": "Beschäftigt sein ist nicht das Gleiche wie produktiv sein.",
            "script": [
                "Beschäftigt sein ist nicht das Gleiche wie produktiv sein.",
                "Du kannst den ganzen Tag rennen und nirgendwo ankommen.",
                "Frag dich morgens: Was ist heute das eine Wichtige?",
                "Mach das zuerst, bevor die Welt dich ablenkt.",
                "Fokus ist Nein sagen zu hundert guten Ideen.",
                "Weniger, aber richtig.",
            ],
            "pexels_video_query": "focused work desk minimal morning light",
            "caption": ("Wir verwechseln oft Bewegung mit Fortschritt.\n\n"
                        "Ein klarer Fokus pro Tag bringt dich weiter als zehn "
                        "halbe Aufgaben.\n\n"
                        "Was ist heute dein eine wichtige Sache?"),
            "story_text": ["NEUER POST", "Klarheit", "vor Tempo", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "Fokus in einer lauten Welt",
            "hook": "Wie du in einer lauten Welt fokussiert bleibst",
            "pexels_queries": ["calm minimal workspace", "single candle dark",
                               "phone face down table", "deep work laptop",
                               "quiet room window light", "mountain top clear sky"],
            "slides": [
                {"is_cover": True,
                 "title": ["Du bist nicht", "unproduktiv.", "Du bist nur", "abgelenkt."],
                 "body": ["6 Wege zu echtem Fokus.", "Weiterwischen."]},
                {"title": ["Eine Aufgabe"],
                 "body": ["zur Zeit.", "Multitasking ist", "ein teurer Mythos."]},
                {"title": ["Handy außer Sicht"],
                 "body": ["Allein der Anblick", "kostet dich Konzentration."]},
                {"title": ["Arbeite in Blöcken"],
                 "body": ["25 Minuten Fokus,", "5 Minuten Pause.", "Wiederholen."]},
                {"title": ["Schütze deinen Morgen"],
                 "body": ["Die erste Stunde", "gehört dir, nicht", "deinen Mitteilungen."]},
                {"title": ["Fokus ist trainierbar"],
                 "body": ["Jeden Tag ein bisschen.", "Speicher dir den Post."]},
            ],
            "caption": ("Aufmerksamkeit ist die neue Währung.\n\n"
                        "Wer sie schützt, kommt schneller voran als wer "
                        "ständig erreichbar ist.\n\n"
                        "Speicher dir die Tipps für deinen nächsten Arbeitstag."),
            "story_text": ["NEUER POST", "Echter Fokus", "in lauter Welt", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "calm focus minimal",
            "quote": {"text": "Es ist nicht zu wenig Zeit, die wir haben, "
                              "sondern zu viel, die wir nicht nutzen.",
                      "author": "Seneca"},
            "tips": {"title": "Fokus zurückholen",
                     "items": ["Wähle morgens nur eine Hauptaufgabe.",
                               "Schalte Mitteilungen für 90 Minuten aus.",
                               "Eine Sache fertig, bevor du wechselst."]},
        },
    },

    # ── 3 ─ Geduld und der lange Weg ─────────────────────────────────────────
    {
        "content_pillar": "emotional",
        "reel": {
            "topic": "Der Vergleich stiehlt deine Ruhe",
            "hook": "Hör auf, dein Kapitel 1 mit dem Kapitel 20 anderer zu vergleichen.",
            "script": [
                "Hör auf, dein Kapitel 1 mit dem Kapitel 20 anderer zu vergleichen.",
                "Jeder zeigt dir das Ergebnis, nie die Jahre davor.",
                "Dein Weg muss nicht aussehen wie der von jemand anderem.",
                "Vergleich dich mit dem, der du gestern warst.",
                "Ein bisschen weiter als gestern reicht völlig.",
                "Bleib auf deiner Bahn.",
            ],
            "pexels_video_query": "person alone calm reflection nature cinematic",
            "caption": ("Der schnellste Weg, deine Zufriedenheit zu verlieren, "
                        "ist der Blick auf das Leben anderer.\n\n"
                        "Dein einziger fairer Maßstab ist dein eigenes Gestern.\n\n"
                        "Worin bist du heute ein Stück weiter als letztes Jahr?"),
            "story_text": ["NEUER POST", "Vergleich", "stiehlt Ruhe", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "Geduld auf dem langen Weg",
            "hook": "Was niemand über den langen Weg sagt",
            "pexels_queries": ["long road horizon", "tree growing time lapse calm",
                               "person hiking trail", "ocean waves patience",
                               "seedling soil hands", "sunrise mountains quiet"],
            "slides": [
                {"is_cover": True,
                 "title": ["Es dauert länger,", "als du denkst.", "Und das ist", "in Ordnung."],
                 "body": ["Über Geduld und Dranbleiben.", "Weiterwischen."]},
                {"title": ["Wachstum ist unsichtbar,"],
                 "body": ["bis es plötzlich", "sichtbar wird."]},
                {"title": ["Die meisten geben auf,"],
                 "body": ["kurz bevor es", "leichter geworden wäre."]},
                {"title": ["Vertrau dem Prozess,"],
                 "body": ["auch wenn du heute", "noch nichts siehst."]},
                {"title": ["Kleine Tage zählen"],
                 "body": ["Sie sind die Bausteine,", "die niemand bemerkt."]},
                {"title": ["Bleib geduldig"],
                 "body": ["mit dir selbst.", "Speicher dir das für", "schwere Tage."]},
            ],
            "caption": ("Wir überschätzen, was in einem Monat geht, und "
                        "unterschätzen, was in einem Jahr möglich ist.\n\n"
                        "Geduld ist kein Warten. Geduld ist Dranbleiben ohne "
                        "sofortige Belohnung.\n\n"
                        "Speicher dir den Post als Erinnerung."),
            "story_text": ["NEUER POST", "Der lange Weg", "lohnt sich", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "patience calm nature",
            "quote": {"text": "Ein Fluss höhlt den Stein nicht durch Kraft, "
                              "sondern durch Beständigkeit.",
                      "author": "Sprichwort"},
            "tips": {"title": "Geduld üben",
                     "items": ["Feiere kleine Fortschritte bewusst.",
                               "Vergleiche dich nur mit deinem Gestern.",
                               "Denk in Jahren, handle in Tagen."]},
        },
    },

    # ── 4 ─ Anfangen vor Perfektion ──────────────────────────────────────────
    {
        "content_pillar": "entertaining",
        "reel": {
            "topic": "Anfangen schlägt Perfektion",
            "hook": "Der perfekte Moment kommt nie. Den gibt es nicht.",
            "script": [
                "Der perfekte Moment kommt nie. Den gibt es nicht.",
                "Du wartest auf Sicherheit, die erst durch das Tun entsteht.",
                "Eine schlechte erste Version schlägt eine perfekte Idee im Kopf.",
                "Du kannst nur korrigieren, was schon existiert.",
                "Fang unfertig an. Werd dabei besser.",
                "Heute ist ein guter Tag, um zu starten.",
            ],
            "pexels_video_query": "person starting morning determined cinematic",
            "caption": ("Perfektionismus ist oft nur Angst in einem schönen "
                        "Mantel.\n\n"
                        "Das Erste, was du baust, darf schlecht sein. Es muss "
                        "nur existieren.\n\n"
                        "Was würdest du heute starten, wenn es nicht perfekt "
                        "sein müsste?"),
            "story_text": ["NEUER POST", "Anfangen", "vor Perfektion", "Jetzt ansehen"],
        },
        "carousel": {
            "topic": "Warum du jetzt anfangen solltest",
            "hook": "Warum du nicht auf den perfekten Moment warten solltest",
            "pexels_queries": ["first step doorway light", "blank notebook pen",
                               "runner starting line", "sunrise new day calm",
                               "hands building creating", "open road journey"],
            "slides": [
                {"is_cover": True,
                 "title": ["Der perfekte", "Moment", "ist eine", "Illusion."],
                 "body": ["6 Gedanken fürs Anfangen.", "Weiterwischen."]},
                {"title": ["Klarheit kommt"],
                 "body": ["durch Handeln,", "nicht durch Nachdenken."]},
                {"title": ["Version 1"],
                 "body": ["ist besser als", "Version 0 im Kopf."]},
                {"title": ["Du darfst schlecht"],
                 "body": ["anfangen.", "Niemand startet gut."]},
                {"title": ["Jeder Profi"],
                 "body": ["war mal Anfänger,", "der trotzdem begann."]},
                {"title": ["Fang heute an"],
                 "body": ["Klein, unfertig, mutig.", "Speicher dir den Post."]},
            ],
            "caption": ("Wir warten auf den Moment, in dem wir uns bereit "
                        "fühlen. Dieser Moment kommt durch das Tun, nicht "
                        "davor.\n\n"
                        "Anfangen ist die halbe Miete — die andere Hälfte ist "
                        "Dranbleiben.\n\n"
                        "Speicher dir den Post für deinen nächsten Anlauf."),
            "story_text": ["NEUER POST", "Jetzt anfangen", "nicht perfekt", "Jetzt ansehen"],
        },
        "stories": {
            "topic": "beginning determined calm",
            "quote": {"text": "Ein Weg von tausend Meilen beginnt mit einem "
                              "einzigen Schritt.",
                      "author": "Laozi"},
            "tips": {"title": "Heute starten",
                     "items": ["Setz dir ein Ziel, das in 10 Minuten passt.",
                               "Erlaube dir eine unperfekte erste Version.",
                               "Tu es, bevor du dich bereit fühlst."]},
        },
    },
]
