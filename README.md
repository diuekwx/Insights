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
Click **start** before or during a game: recording starts when League's game window opens and
stops when the game closes (or when you click **stop**). The video and kill ticks load afterwards.
Developer tools: View → Toggle Developer Tools (Ctrl+Shift+I).
