WE SHALL NEVER MODIFY THE POKER_KNIGHT MODULE OR SUBFOLDER. IT IS STRICTLY READ ONLY, WE MAY ONLY IMPORT IT.

this is a python project.
all work shall be conducted in a venv for consistency.
this project is called 'Camelot' , it's written by github user hildolfr.
This will be a daemon , web front-end, and REST API to expose the poker_knight module to outside services and web-use.
the poker_knight module is the one and only way to solve a poker problem.
the poker_knight module is also available at github.com/hildolfr/poker_knight if you want to pull it remotely.
if you are confused about the capabilities or API of that module, please read the code or corresponding documents.


game card suite shall always be represented as unicode, card ranks shall always be represented by number or single letter prefix -- if this is ambiguous refer to the API documentation for poker_knight.
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
3) testing suite that will present poker_knight with valid games and record statistics about the results, this system will be activated via the webui, as well as using the webui as a means to display stats about the previously ran games.
4) human-playable poker demo game on the webui with similar stat systems from the webui machine testing suite implemented in step 3.

We will formulate all of our plans in a TODO.md file that we shall keep in the project root.
We will save all of our progress in a CHANGELOG.md file we shall keep in the project root.
When we need to make complicated plans we will create a time/dated document in the plans/ folder with an appropriate name. We will use this file as a checklist to continue progress on specific tasks. When the tasks are done the file shall be put into the archives/plans/ folder




