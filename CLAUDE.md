WE SHALL NEVER MODIFY THE POKER_KNIGHTNG MODULE OR SUBFOLDER. IT IS STRICTLY READ ONLY, WE MAY ONLY IMPORT IT.

this is a python project.
all work shall be conducted in a venv for consistency.
this project is called 'Camelot' , it's written by github user hildolfr.
This will be a daemon , web front-end, and REST API to expose the poker_knightng module to outside services and web-use.
the poker_knightng module is the one and only way to solve a poker problem.
the poker_knightng module is also available at github.com/hildolfr/poker_knightng if you want to pull it remotely.
if you are confused about the capabilities or API of that module, please read the code or corresponding documents (especially apiNGv2.md).

apiNGv2.md is our poker_knightNG reference. It's important that all code that communicates to the poker solver (poker_knightng) conforms to the api described in this.

game card suite shall always be represented as unicode, card ranks shall always be represented by number or single letter prefix -- if this is ambiguous refer to the API documentation for poker_knightng.
a proposed or represented poker game shall never be invalid, if it is we shall err and notify the user and log the event. 
We play poker with a single deck, so there will never be any repeated cards in a single game.
We play texas hold'em.
It's common to have upwards of 7 players at a table, but we should accomodate even small 1v1 duels.

we shall have a focus on readability and information density. 
we shall work towards optimization for mobile or tablet platforms.
webUI must be visually interesting and entertaining. Web users must enjoy using it.
we will eventually have a card game playable by a user within the web UI, as well as module status and a poker 'calculator' for allowing users to input the conditions of a game to see the expected statistical results.

We will work on things in the following order:

1) web UI and base functionalities
2) REST API
3) testing suite that will present poker_knightng with valid games and record statistics about the results, this system will be activated via the webui, as well as using the webui as a means to display stats about the previously ran games.
4) human-playable poker demo game on the webui with similar stat systems from the webui machine testing suite implemented in step 3.

We will formulate all of our plans in a TODO.md file that we shall keep in the project root.
We will save all of our progress in a CHANGELOG.md file we shall keep in the project root.
When we need to make complicated plans we will create a time/dated document in the plans/ folder with an appropriate name. We will use this file as a checklist to continue progress on specific tasks. When the tasks are done the file shall be put into the archives/plans/ folder

## Bug Reporting System
Users can submit bug reports during gameplay using the bug report button (🐛) at the bottom right of the game screen.
Bug reports are logged with special markers and also saved to a dedicated daily rotating log file.

### Log Files Structure
- `logs/poker_game.log` - Main game log (rotates at 10MB, keeps 5 backups)
- `logs/bug_reports.log` - Dedicated bug reports (rotates daily, keeps 30 days)
- Rotated files appear as `.log.1`, `.log.2`, etc.

### Searching for Bug Reports

To search for user bug reports in the main logs:
```bash
grep -A10 -B2 "USER_BUG_REPORT_START" logs/poker_game.log*
```

To view only bug reports from the dedicated log:
```bash
cat logs/bug_reports.log*
```

Or to find all bug reports with context:
```bash
grep -E "USER_BUG_REPORT_(START|END)" logs/poker_game.log*
```

Bug reports include timestamp, game state, user description, and relevant game context.

### Log Rotation
- Game logs: Rotate at 10MB, keep 5 backup files (50MB total)
- Bug reports: Rotate daily at midnight, keep 30 days
- Old timestamped logs can be cleaned with: `python cleanup_old_logs.py`

if we need to write a debug test or something otherwise temporary and not part of our actual testing suite it shall be done in tests/debug to keep things tidy.

when we make temporary files or tests we will make a big effort to clean up after ourselves, we do not want to leave temporary files everywhere.