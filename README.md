**Insights Capture Clone**

A match insights visualizer for League of Legends, inspired by Overwolf's Insights Capture tool. 

**About**  

This is a tool for players who want a deeper understanding of their performance and team dynamics across games. It utilizes Riot's Live Client API to automatically record and capture detects kills, deaths, 
and assists, and other critical events throughout the game, for post-game review. 

**Setup** (Windows)

1. Install Python 3.11+, Node.js, [OBS Studio](https://obsproject.com/) (default install folder) and
   [ffmpeg](https://ffmpeg.org/) (`ffmpeg` must work in a terminal, i.e. be on PATH).
2. Python packages, in a venv inside this folder (Electron uses `venv\Scripts\python.exe` when it exists):
   ```
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```
3. Electron: `npm install`
4. OBS:
   - Tools → WebSocket Server Settings: enable the server, port `4455`, set a password.
   - Create a scene named exactly `leaguegame` with a Game Capture source for League.
5. Create `.env` in this folder (it is gitignored):
   ```
   OBS_PASSWORD=your-obs-websocket-password
   RIOT_KEY=your-riot-api-key
   ```

**Run**

`npm start` opens the app and starts the Python server; its output shows in the same terminal.
While the app is open it records every game by itself: OBS starts recording when League's game
window opens (the loading screen) and stops when it closes. Each game's kill list is saved in
`games/` next to the path of its video, and the newest game loads in the app once it is saved.
The status in the top bar shows what the recorder is doing.
Developer tools: View → Toggle Developer Tools (Ctrl+Shift+I).
