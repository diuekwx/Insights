// Renderer: polls the Flask server on 127.0.0.1:5000 for what the recorder
// is doing, and shows the newest recorded game with its key moments on a
// timeline. Recording itself is automatic (see core/detector.py).

const API = 'http://127.0.0.1:5000';
const POLL_MS = 2000; // how often to ask the server for its status
const LEAD_IN = 5;    // seconds shown before an event when jumping to it

const vod = document.getElementById('vod');
const track = document.getElementById('track');

let loadedGameId = null; // id of the game shown in the player
let connected = false;   // the server has answered at least once
let failedPolls = 0;
let timelineEvents = [];
let seeking = false;

const STATUS = {
  starting: { text: 'Starting…', hint: 'Waiting for the recorder to start' },
  watching: { text: 'Watching', hint: 'Recording starts by itself when a game loads' },
  recording: { text: 'Recording', hint: 'Kills are collected as they happen' },
  saving: { text: 'Saving…', hint: 'Stopping OBS and compressing the video' },
  error: { text: 'Recording failed', hint: '' },
  offline: { text: 'Recorder offline', hint: 'Can’t reach the Python server on port 5000' },
};

const MULTIKILL_NAMES = { 2: 'Double kill', 3: 'Triple kill', 4: 'Quadra kill', 5: 'Penta kill' };

// ---- helpers ----------------------------------------------------------------

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00';
  const sign = seconds < 0 ? '-' : '';
  let s = Math.floor(Math.abs(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  s %= 60;
  const mm = h ? String(m).padStart(2, '0') : String(m);
  return `${sign}${h ? h + ':' : ''}${mm}:${String(s).padStart(2, '0')}`;
}

function formatDate(epochSeconds) {
  return new Date(epochSeconds * 1000).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function eventLabel(event) {
  if (event.type === 'multikill') return MULTIKILL_NAMES[event.kills] || `${event.kills}× kill`;
  return 'Kill';
}

function eventDetail(event) {
  return event.type === 'kill' ? event.victim : '';
}

// ---- recorder status ----------------------------------------------------------

function showStatus(state, detail) {
  const info = STATUS[state] || { text: state, hint: '' };
  const hint = detail || info.hint;
  document.getElementById('status').dataset.state = state;
  document.getElementById('status-text').textContent = info.text;
  const hintNode = document.getElementById('status-hint');
  hintNode.textContent = hint;
  hintNode.title = hint; // full text on hover when it is cut off
}

async function poll() {
  try {
    const response = await fetch(`${API}/status`);
    const data = await response.json();
    connected = true;
    failedPolls = 0;
    showStatus(data.state, data.detail);
    // a new id means a game finished saving (or the app just opened)
    if (data.latest && data.latest !== loadedGameId) await loadLatestGame(data.latest);
  } catch (error) {
    // the server takes a moment to start with the app, so at first only call
    // it offline after ~10 s of failed polls; once it has answered, at once
    failedPolls += 1;
    showStatus(!connected && failedPolls < 5 ? 'starting' : 'offline');
  } finally {
    setTimeout(poll, POLL_MS);
  }
}

// ---- loading a game -----------------------------------------------------------

async function loadLatestGame(gameId) {
  // set first, so a game that fails to load isn't fetched again every poll
  loadedGameId = gameId;
  try {
    const response = await fetch(`${API}/latest-game`);
    if (!response.ok) throw new Error(`server answered ${response.status}`);
    const game = await response.json();
    loadedGameId = game.id;
    showGame(game);
  } catch (error) {
    console.error('Error loading game', error);
    showPlaceholder('Could not load the last game', String(error.message || error));
  }
}

function showGame(game) {
  vod.pause();
  timelineEvents = [...(game.events || [])].sort((a, b) => a.vod_time - b.vod_time);
  renderEventList();
  renderMarkers(NaN); // cleared until the new video's length is known
  document.getElementById('game-meta').textContent =
    game.finished_at ? `Game ended ${formatDate(game.finished_at)}` : '';
  document.getElementById('playButton').disabled = true;
  document.getElementById('duration').textContent = '0:00';

  if (!game.video) {
    showPlaceholder('No video for this game', 'OBS did not report a recording file.');
    return;
  }
  showPlaceholder('Loading video…', '');
  document.getElementById('vod-source').src = `file:///${game.video.replace(/\\/g, '/')}`;
  vod.load(); // 'loadedmetadata' below finishes the job
  updateProgress();
}

function showPlaceholder(title, text) {
  document.getElementById('placeholder-title').textContent = title;
  document.getElementById('placeholder-text').textContent = text;
  document.getElementById('vod-placeholder').classList.remove('hidden');
}

// ---- player -----------------------------------------------------------------

function play() {
  if (!Number.isFinite(vod.duration)) return;
  if (vod.paused) vod.play();
  else vod.pause();
}

function jumpTo(event) {
  if (!Number.isFinite(vod.duration)) return;
  vod.currentTime = Math.min(Math.max(0, event.vod_time - LEAD_IN), vod.duration);
  vod.play();
}

function setPlaying(playing) {
  const button = document.getElementById('playButton');
  button.classList.toggle('is-playing', playing);
  button.setAttribute('aria-label', playing ? 'Pause' : 'Play');
}

function updateProgress() {
  const ratio = vod.duration > 0 ? vod.currentTime / vod.duration : 0;
  document.getElementById('progress').style.width = `${ratio * 100}%`;
  document.getElementById('playhead').style.left = `${ratio * 100}%`;
  document.getElementById('current-time').textContent = formatTime(vod.currentTime);
  track.setAttribute('aria-valuenow', Math.floor(vod.currentTime));
  track.setAttribute('aria-valuetext', formatTime(vod.currentTime));
  highlightCurrent();
}

// marks the latest event at or before the playhead, in the list and on the bar
function highlightCurrent() {
  let current = -1;
  timelineEvents.forEach((event, index) => {
    if (event.vod_time <= vod.currentTime + 0.25) current = index;
  });
  document.querySelectorAll('.event-row, .marker').forEach((node) => {
    node.classList.toggle('current', Number(node.dataset.index) === current);
  });
}

// ---- timeline and events list -------------------------------------------------
// names come from the game, so they are only ever set as text, never as HTML

function renderMarkers(duration = vod.duration) {
  const layer = document.getElementById('markers');
  layer.replaceChildren();
  if (!Number.isFinite(duration) || duration <= 0) return;

  timelineEvents.forEach((event, index) => {
    // events from before the recording started have negative times
    if (event.vod_time < 0 || event.vod_time > duration) return;

    const label = `${formatTime(event.vod_time)} · ${eventLabel(event)}` +
      (event.type === 'kill' ? ` → ${event.victim}` : '');
    const marker = document.createElement('button');
    marker.className = `marker ${event.type}`;
    marker.style.left = `${(event.vod_time / duration) * 100}%`;
    marker.dataset.index = index;
    marker.dataset.label = label;
    marker.setAttribute('aria-label', label);
    marker.addEventListener('click', () => jumpTo(event));

    const pin = document.createElement('span');
    pin.className = 'pin';
    marker.append(pin);
    layer.append(marker);
  });
}

function renderEventList() {
  const list = document.getElementById('event-list');
  list.replaceChildren();
  document.getElementById('event-count').textContent = timelineEvents.length;

  if (timelineEvents.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = loadedGameId === null
      ? 'Kills from your next game will be listed here.'
      : 'No kills recorded this game.';
    list.append(empty);
    return;
  }

  timelineEvents.forEach((event, index) => {
    const row = document.createElement('button');
    row.className = `event-row ${event.type}`;
    row.dataset.index = index;
    row.addEventListener('click', () => jumpTo(event));

    const time = document.createElement('span');
    time.className = 'event-time';
    time.textContent = formatTime(event.vod_time);

    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = eventLabel(event);

    const detail = document.createElement('span');
    detail.className = 'event-detail';
    detail.textContent = eventDetail(event);
    detail.title = eventDetail(event);

    row.append(time, badge, detail);
    const item = document.createElement('li');
    item.append(row);
    list.append(item);
  });
}

// ---- seeking on the timeline ------------------------------------------------

function seekFromPointer(e) {
  if (!Number.isFinite(vod.duration)) return;
  const rect = track.getBoundingClientRect();
  const ratio = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
  vod.currentTime = ratio * vod.duration;
}

track.addEventListener('pointerdown', (e) => {
  if (e.target.closest('.marker')) return; // markers jump on click instead
  seeking = true;
  track.setPointerCapture(e.pointerId);
  seekFromPointer(e);
});
track.addEventListener('pointermove', (e) => {
  if (seeking) seekFromPointer(e);
});
track.addEventListener('pointerup', () => { seeking = false; });
track.addEventListener('pointercancel', () => { seeking = false; });
track.addEventListener('keydown', (e) => {
  if (!Number.isFinite(vod.duration)) return;
  if (e.key === 'ArrowRight') vod.currentTime = Math.min(vod.currentTime + 5, vod.duration);
  else if (e.key === 'ArrowLeft') vod.currentTime = Math.max(vod.currentTime - 5, 0);
  else return;
  e.preventDefault();
});

// ---- video events (attached once) -------------------------------------------

vod.addEventListener('loadedmetadata', () => {
  document.getElementById('vod-placeholder').classList.add('hidden');
  document.getElementById('playButton').disabled = false;
  document.getElementById('duration').textContent = formatTime(vod.duration);
  track.setAttribute('aria-valuemax', Math.floor(vod.duration));
  renderMarkers();
  updateProgress();
});
vod.addEventListener('timeupdate', updateProgress);
vod.addEventListener('play', () => setPlaying(true));
vod.addEventListener('pause', () => setPlaying(false));
document.getElementById('vod-source').addEventListener('error', () => {
  showPlaceholder('The video could not be played', 'The file may have been moved or deleted.');
});

showStatus('starting');
renderEventList();
poll();

async function getTicks(){
  try{
    const response = await fetch('http://127.0.0.1:5000/game-stats');
    const data = await response.json();
    console.log(data);
  }
  catch (error){
    console.error('Error game stats', error)
  }
}
