# Master Yi: The Wuju Bladesman

A browser game styled as a Tiger Electronics LCD handheld. Master Yi defends
the Ionian jungle from waves of dart-blowing Teemos. The entire page is the
green handheld: the game runs on the amber "LCD" screen and the physical
ability buttons show live cooldowns.

**Live site:** https://wujustyle.com (and https://d28r3plj89s9tx.cloudfront.net)

## Gameplay

Yi swings automatically at any Teemo in blade range — you position him and
spend abilities, all based on his real League of Legends kit:

| Ability | Key | Effect |
|---|---|---|
| Double Strike (passive) | — | Every 4th blow lands twice |
| Alpha Strike | Q / button | Blink untargetably through up to 4 Teemos |
| Meditate | W / button | Channel to heal, take 1/3 damage; moving cancels |
| Highlander | R / button | Speed burst; kills extend it and refund 70% of cooldowns |

Teemo fights back with blinding darts (your swings MISS), trapper Teemos plant
poison mushrooms, and every 4th wave the Swift Scout arrives as a boss.
Move with arrow keys / A,D or the on-screen D-pad. Enter starts/pauses,
M toggles sound. Hi-score persists in localStorage. Touch-friendly.

## Project layout

- `index.html` — the whole game (single self-contained file: HTML, CSS, JS, Web Audio)
- `audio/teemo-hut.mp3` — Teemo's "Hut, two, three, four!" voice line (Omega Squad,
  from the League of Legends Wiki), played occasionally while Teemos are on screen
- `deploy.sh` — uploads `index.html` and `audio/` to S3 and invalidates the CloudFront cache
- `aws/` — infrastructure reference (see below)
