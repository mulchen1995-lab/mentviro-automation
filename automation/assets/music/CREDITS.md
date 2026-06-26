# Hintergrundmusik — Quellen & Lizenz

Die stimmungsabhängigen Reel-Tracks sind echte Instrumentals von **Kevin MacLeod**
(incompetech.com), bezogen über das Internet Archive
(<https://archive.org/details/KevinMacLeod_2019-04_Discography>).

**Lizenz: Creative Commons Attribution 4.0 (CC BY 4.0)**
<https://creativecommons.org/licenses/by/4.0/>

Die Lizenz verlangt Namensnennung dort, wo das Werk veröffentlicht wird. Das erledigt
die Pipeline automatisch: Bei jedem Reel mit einem dieser Tracks wird
`🎵 Musik: Kevin MacLeod – CC BY 4.0` an die Caption angehängt
(`MUSIC_CREDIT` in `daily_post.py`). Bewusst ohne URL — mentviro-Richtlinie erlaubt
keine Links in Captions; Autor + Lizenzname genügen für CC-BY.

| Datei | Stimmung (content_pillar) | Original-Track |
|---|---|---|
| `bg_educational.mp3`  | educational (ruhig/fokussiert)   | "Private Reflection" |
| `bg_entertaining.mp3` | entertaining (treibend/positiv)  | "Carefree" |
| `bg_emotional.mp3`    | emotional (warm/gefühlvoll)      | "Heartwarming" |

Jeder Track wurde aus einem stabilen Mittelteil des Originals auf 60 s geschnitten,
per `loudnorm` auf einheitliche Lautheit gebracht und mit kurzen Rand-Fades versehen
(loopbar unter dem Voiceover, der bei der Endmischung auf 10 % Lautstärke liegt).

## Fallback

`../bg_music.mp3` (synthetischer, lizenzfreier Am-Drone, CC0/Eigenproduktion) bleibt als
letzter Fallback im Code erhalten, falls ein Pillar-Track fehlt — dieser braucht **keine**
Namensnennung.
