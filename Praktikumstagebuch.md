# Praktikumstagebuch - _Implementierung eines Lösungsverfahrens für Mancala (Kalah) mit Alpha-Beta-Pruning_

Autor: Jannis Martensen
---

## 1) Themenbeschreibung

Mancala in der Kalah-Variante ist ein zweispielerisches Brettspiel, bei dem es darum geht, möglichst viele Spielsteine
in das eigene „Haus“ (Store) zu bringen.
Das Spielbrett besteht typischerweise aus zwei Reihen mit jeweils sechs Mulden pro Spieler sowie je einem Haus an den
Enden.
Ein Spieler wählt in seinem Zug eine Mulde seiner Reihe, nimmt alle darin enthaltenen Steine auf und verteilt sie eins
nach dem anderen gegen den Uhrzeigersinn in die folgenden Mulden und
ins eigene Haus (das Haus des Gegners wird beim Verteilen ausgelassen).
Besondere Regeln sind:

- Wer den letzten Stein in sein eigenes Haus legt, erhält einen weiteren Zug
- Landet der letzte Stein in einer bisher leeren Mulde auf der eigenen Seite, so werden die gegenüberliegenden Steine
  des Gegners zusammen mit dem letzten Stein eingefangen und ins eigene Haus gelegt.

Das Spiel endet, sobald alle Mulden einer Seite leer sind; verbleibende Steine werden in die Häuser übertragen und
derjenige mit den meisten Steinen gewinnt.
Das Ziel dieses Praktikums ist die Entwicklung eines Bots, der die Kalah-Variante von Mancala spielen kann.
Als zugrundeliegendes Suchverfahren wird Alpha-Beta-Pruning eingesetzt, eine optimierte Version der Minimax-Suche, die
Teile des Spielbaums ausschließt und so die Suche effizienter macht.
Der Agent soll über eine heuristische Bewertungsfunktion verfügen und in seiner Suchtiefe konfigurierbar sein.
Wichtige Teilziele sind eine korrekte Regelimplementierung, die zuverlässige Generierung legaler Züge,
eine robuste Bewertungsfunktion und eine Evaluationsstrategie, mit der sich Spielstärke gegen Rechenaufwand analysieren
lässt.

---

## 2) Umsetzung

*Leider konnte sich kein/e Teampartner\*in finden, daher habe ausschließlich ich die Aufgaben bearbeitet*

### Arbeitsschritte:

#### 1. Spiellogik

- Grundlegende Mancala-Regeln implementiert (Steinverteilung, Captures, Extra-Zug, Spielende)
- Modell bewusst UI-unabhängig gehalten
- Mehrfaches Testen und Nachschärfen der `Mancala`-Klasse
- Möglichkeit anderer Spielmodi (z. B. unterschiedliche Muldenanzahlen oder Steine pro mulde)

#### 2. Benutzeroberfläche (UI)

- Darstellung der Mulden, Steine und Spielerzustände mit Pygame
- Event-Handling klar getrennt von der Game-Engine
- Animation und Effekte um Züge deutlicher zu machen. Züge passieren nicht direkt, sondern als kleine Animation
- Möglichkeit für Spieler-Gegen-Spieler, Spieler-Gegen-KI und KI-gegen-KI Spiele
- Problemstellen:
    - Das Layout des Boards richtig darstellen (Übersetzung modell auf UI). Die obere Reihe war falsch herum → Layout
      angepasst
    - Unklare Hervorhebung aktiver Spieler → Aktiver Spieler wird farblich hervorgehoben
    - Performance-Probleme durch Nutzung von time.sleep im Gameloop, welches zu freezes geführt hat → Spiellogik in separatem Thread ausgelagert

#### 3. Alpha-Beta-Pruning-Algorithmus

- Klassisches Minimax mit Alpha-Beta-Pruning
- Evaluationsfunktion basiert auf (Sortiert von wichtig nach weniger wichtig):
    - Endzuständen (Win/Loss)
    - Steinen im Store
    - Differenz der Mulden (Anzahl Steine pro Spieler die nicht im Store liegen)

- Besonderheit: Extra-Züge erhöhen die Suchtiefe nicht, da der Spieler weiterhin am Zug ist

- Performance-Probleme durch tiefe Rekursion → optimiert durch weniger Objektkopien
- Ziel: **stabiler, spielbarer KI-Gegner**

#### 4. Simulationsskript

- Automatisches Ausführen mehrerer von KI-gegen-KI-Partien
- Vergleich verschiedener Suchtiefen
- Loggen der Ergebnisse für statistische Auswertung

---

## 3) Experimente / Ergebnisse

### Experiment 1: Simulation verschiedener Suchtiefen

**Ziel:** Überprüfen, wie sich unterschiedliche Suchtiefen auf die Spielstärke und Rechenzeit der KI auswirken.

### Vorgehen

- Nutzung des Simulationsskripts
- Pro Tiefe: **100 Spiele**
- Tiefenbereiche: 3–8

### Ergebnisse



| Anzahl Spiele | Tiefe | Laufzeit  | Winrate Player 0 (%) | Winrate Player 1 (%) |
|---------------|-------|-----------|----------------------|----------------------|
| 100           | 1     | 0.10s     | 100                  | 0                    |
| 100           | 2     | 1.67s     | 100                  | 0                    |
| 100           | 3     | 3.43s     | 100                  | 0                    |
| 100           | 4     | 14.27s    | 100                  | 0                    |
| 100           | 5     | 75.71s    | 100                  | 0                    |
| 100           | 6     | 118.65s   | 100                  | 0                    |
| 100           | 7     | 701.1s`*` | 100                  | 0                    |
| 100           | 8     | 3051s`**` | 100                  | 0                    |
`* Hochgerechnet von 10 Spielen` `** Hochgerechnet von 1 Spiel`  
_Die Berechnung wurden auf einem MacBook mit M3-Chip durchgeführt. Sie dienen nur als grobe Orientierung/Relative Werte und können je nach Hardware variieren._  

_Hochrechnung sind ungenau und sollen ausschließlich darstellen, das ab einer gewissen Tiefe der Algorithmus zu langsam wird_
### Erkenntnisse

- **Player 0 gewinnt immer**, unabhängig von der Tiefe.
    - Hintergrund: *Mancala Kalah ist ein gelöstes Spiel*. Der startende Spieler hat bei perfektem Spiel stets einen
      Vorteil und wird immer gewinnen.
- Ab **Suchtiefe 7–8** wird Alpha-Beta trotz Pruning extrem langsam.
    - Grund: exponentielles Wachstum des Suchbaums

---

### Experiment 2: Mensch vs. KI
**Ziel:** Einschätzen, wie gut sich die KI gegen tatsächliche Spieler schlägt.

### Beobachtungen
- Mensch spielte immer als **Player 0**, dadurch bei perfektem Spiel immer ein gewinn möglich
- Die KI zeigte komplexe, teils schwer nachvollziehbare Züge (Wie eine komplette runde drehen, um dann einen Steal zu machen) die einem Menschen vielleicht entgangen wären.
- Menschen können Mancala selten perfekt spielen — notwendig, um als P0 garantiert zu gewinnen.
- Ergebnis: **Die KI gewinnt oft**, obwohl der Mensch rechnerisch im Vorteil sein sollte
- (Vielleicht war ich auch einfach nur schlecht im Mancala spielen)

---

## 4) Zusammenfassung und Ausblick

### Zusammenfassung
Das Projekt zeigt, wie sich eine vollständige Mancala-(Kalah-)Implementierung inklusive Engine, UI, KI und Simulationen technisch umsetzen lässt.  
Die wichtigsten Erkenntnisse:

- Die Spiellogik ließ sich robust implementieren, inklusive aller Spezialregeln wie Captures und Extra-Züge.  
- Die Pygame-UI funktioniert stabil und ermöglicht Mensch-vs-KI, KI-vs-KI und Mensch-vs-Mensch Spiele. Animationen machten das Spiel verständlicher und runder.  
- Die Alpha-Beta-KI spielt stark und zuverlässig, allerdings mit spürbaren Performance-Grenzen ab Suchtiefe > 7.  
- Die Simulationen haben bestätigt, dass **Kalah ein gelöstes Spiel** ist und Player 0 bei optimalem Spiel *immer* gewinnt — unabhängig von der Suchtiefe.  
- Im Mensch-vs-KI-Vergleich zeigte sich, dass die KI auch abseits maximaler Suchtiefe bereits sehr starke, kaum nachvollziehbare Strategien nutzt.

Insgesamt hat die Kombination aus Spiellogik, KI und UI ein vollständiges, funktionales Mancala-System ergeben, das sowohl spielerisch als auch technisch überzeugt.

---

### Ausblick
Für weitere Arbeit bieten sich mehrere Richtungen an:

- **Alternative Varianten wie „Mancala Oware“**  
  Oware ist deutlich komplexer, *nicht* gelöst und hat weltweit kulturelle Bedeutung (z. B. in Ghana, auf den Kapverden und in der Karibik).  
  Ein KI-Agent für Oware wäre technisch anspruchsvoller und interessanter, da kein perfektes Spiel bekannt ist. Player 0 kann also nicht immer gewinnen nur weil er anfängt


- **Andere heuristische Bewertungsfunktionen**  
  Ideen:
  - Bonus für Zugfolgen, die Extra-Turns erzeugen  
  - Erkennung von Steal-Setups  
  - Mobilität (Anzahl legaler Züge)  
  - Stabilere Midgame-Heuristiken statt nur Stores + Mulden-Differenz


- **Performance-Optimierung**  
  - Effizienteres Board-Encoding
  - Move-Ordering zur besseren Alpha-Beta-Abschneidung
  - Parallele Simulationen
  - Transposition Tables
  - Iterative Deepening
  - Endgame-Datenbanken für bekannte Positionen


- **Alternative KI-Ansätze**  
  - Monte-Carlo Tree Search (MCTS)  
  - Reinforcement Learning (falls man Oware nutzt)


Diese Erweiterungen würden das Projekt deutlich spannender machen und erlauben, von einem gelösten Spiel wie Kalah hin zu einer komplexeren, offenen Problemstellung wie Oware zu wechseln.



---

## 5) Quellen


[1] *Mancala*. In: **Wikipedia**.  
URL: https://de.wikipedia.org/wiki/Mancala  
(Zugriff am: *14.11.2025*).

[2] *Kalah*. In: **Wikipedia**.  
URL: https://de.wikipedia.org/wiki/Kalah  
(Zugriff am: *12.11.2025*).

[3] Stelldinger, P. (2025). *Künstliche Intelligenz*.  
Vorlesungsfolien der Vorlesung **„Künstliche Intelligenz“**, HAW Hamburg,  
*Sommersemester 2025*

[4] *Pygame Documentation*.  
URL: https://www.pygame.org/docs/  
(Zugriff am: *15.11.2025*).

[5] Irving, Geoffrey; Donkers, Jeroen; Uiterwijk, Jos : *Solving Kalah*
URL: https://naml.us/paper/irving2000_kalah.pdf
(Zugriff am: *10.11.2025*).

