// Renderer: talks to the Flask server on 127.0.0.1:5000 and shows the
// recorded game with its key moments on a timeline.

const API = 'http://127.0.0.1:5000';
const LEAD_IN = 5; // seconds shown before an event when jumping to it

const vod = document.getElementById('vod');
const track = document.getElementById('track');

let sessionState = 'idle'; // idle | active | stopping | loading | ready | error
let startPending = false;  // the long /start-recording request is still open
let timelineEvents = [];
let seeking = false;

const STATUS_TEXT = {
  idle: 'Idle',
  active: 'Session active',
  stopping: 'Stopping…',
  loading: 'Loading video…',
  ready: 'Ready',
  error: 'Error',
};

const STATUS_HINT = {
  idle: 'Press Start, then launch a game',
  active: 'Waiting for a game, or recording it',
  stopping: 'Stopping OBS and compressing the video',
  loading: '',
  ready: '',
  error: '',
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

function eventLabel(event) {
  if (event.type === 'multikill') return MULTIKILL_NAMES[event.kills] || `${event.kills}× kill`;
  return 'Kill';
}

function eventDetail(event) {
  return event.type === 'kill' ? event.victim : '';
}

function setState(state, hint) {
  sessionState = state;
  document.getElementById('status').dataset.state = state;
  document.getElementById('status-text').textContent = STATUS_TEXT[state];
  document.getElementById('status-hint').textContent = hint ?? STATUS_HINT[state];

  const button = document.getElementById('recordBtn');
  const active = state === 'active' || state === 'stopping';
  button.classList.toggle('is-active', active);
  button.disabled = state === 'stopping' || state === 'loading';
  document.getElementById('recordLabel').textContent =
    state === 'stopping' ? 'Stopping…' : active ? 'Stop' : 'Start';
}

// ---- recording --------------------------------------------------------------

function toggleRecording() {
  if (sessionState === 'active') stopRecording();
  else startRecording();
}

async function stopRecording() {
  setState('stopping');
  try {
    await fetch(`${API}/start-recording?recording=false`);
  } catch (error) {
    console.error('Error stopping', error);
  }
  // normally the open start request finishes the job and loads the video;
  // if this page has none (e.g. it was reloaded mid-session), go back to idle
  if (!startPending) setState('idle');
}

async function startRecording() {
  setState('active');
  startPending = true;
  try {
    // this request stays open until the game (or the session) ends
    const response = await fetch(`${API}/start-recording?recording=true`);
    const data = await response.json();
    console.log('timeline data !', data);
    // only a finished recording returns a list of events; errors and
    // "Already recording" come back as an object
    if (Array.isArray(data)) {
      getVideo(data);
    } else if (data.text === 'Already recording') {
      setState('active', 'A session started earlier is still running');
    } else if (data.error) {
      setState('error', data.error);
    } else {
      setState('idle', data.status || data.text);
    }
  } catch (error) {
    console.error('Error starting recording', error);
    setState('error', 'Could not reach the recorder. Is the Python server running?');
  } finally {
    startPending = false;
  }
}

async function getVideo(timelineData) {
  setState('loading');
  timelineEvents = [...timelineData].sort((a, b) => a.vod_time - b.vod_time);
  renderEventList();
  try {
    const response = await fetch(`${API}/get-video`);
    const data = await response.json();
    if (typeof data !== 'string') throw new Error(data.text || 'no video path');
    const videoPath = `file:///${data.replace(/\\/g, '/')}`;
    console.log(videoPath);

    document.getElementById('vod-source').src = videoPath;
    vod.load(); // 'loadedmetadata' below finishes the job
  } catch (error) {
    console.error('Error fetching data: ', error);
    setState('error', 'The game was recorded, but its video could not be found');
  }
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
    empty.textContent = sessionState === 'idle'
      ? 'Kills from your game will be listed here.'
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
  const n = timelineEvents.length;
  setState('ready', `${n} key moment${n === 1 ? '' : 's'}`);
});
vod.addEventListener('timeupdate', updateProgress);
vod.addEventListener('play', () => setPlaying(true));
vod.addEventListener('pause', () => setPlaying(false));
document.getElementById('vod-source').addEventListener('error', () => {
  setState('error', 'The video file could not be played');
});

setState('idle');
renderEventList();

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
