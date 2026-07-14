# Hintergrundmusik — Quellen & Lizenz

Die stimmungsabhängigen Reel-Tracks sind moderne, royaltyfreie Instrumentals von
**Pixabay** (<https://pixabay.com/music/>).

**Lizenz: Pixabay Content License**
<https://pixabay.com/service/license-summary/>
Frei für kommerzielle Nutzung, **keine Namensnennung erforderlich**. Deshalb hängt die
Pipeline auch keinen Musik-Credit an die Captions (anders als bei der früheren
CC-BY-Quelle). Erlaubt ist die Nutzung als Hintergrundmusik im Video; nicht erlaubt
wäre der Weiterverkauf der Tracks als solche.

| Datei | Stimmung (content_pillar) | Pixabay-Track (Artist) |
|---|---|---|
| `bg_educational.mp3`  | educational (ruhig/fokussiert)  | "Calm Ambient Dreamscape" (morgan-ambient), ID 529861 |
| `bg_entertaining.mp3` | entertaining (treibend/positiv) | "Upbeat Motivational / Corporate" (The_Mountain), ID 199145 |
| `bg_emotional.mp3`    | emotional (warm/gefühlvoll)     | "Inspiring / Orchestral" (leberch), ID 511351 |

Jeder Track wurde aus einem stabilen Mittelteil des Originals auf 60 s geschnitten,
per `loudnorm` auf einheitliche Lautheit gebracht und mit kurzen Rand-Fades versehen
(loopbar unter dem Voiceover, der bei der Endmischung auf 10 % Lautstärke liegt).

## Fallback

`../bg_music.mp3` (synthetischer, lizenzfreier Am-Drone, CC0/Eigenproduktion) bleibt als
letzter Fallback im Code erhalten, falls ein Pillar-Track fehlt.
