(function () {
'use strict';
const D = window.M49;
const ROM = Uint8Array.from(atob(D.rom), c => c.charCodeAt(0));
const rb = a => ROM[a - 0x8000];
const rw = a => rb(a) | (rb(a + 1) << 8);
const PAL = D.pal.map(h => [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]);
const rgb = c => 'rgb(' + PAL[c & 0xFF].join(',') + ')';
const REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const b64u8 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const hex2 = n => '$' + (n & 0xFF).toString(16).toUpperCase().padStart(2, '0');
const hex4 = n => '$' + (n & 0xFFFF).toString(16).toUpperCase().padStart(4, '0');

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) {
    if (k === 'class') e.className = attrs[k];
    else if (k === 'text') e.textContent = attrs[k];
    else if (k === 'html') e.innerHTML = attrs[k];
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
    else e.setAttribute(k, attrs[k]);
  }
  for (const k of kids) if (k != null) e.append(k);
  return e;
}
// A canvas whose logical pixels are drawn as px x py device blocks, scaled up crisply by CSS.
function pixCanvas(w, h, px, py, cssScale) {
  const cv = el('canvas', { class: 'pix' });
  cv.width = w * px; cv.height = h * py;
  if (cssScale) cv.style.width = (w * px * cssScale) + 'px';
  const ctx = cv.getContext('2d');
  return { cv, ctx, w, h, px, py,
    fill(col) { ctx.fillStyle = col; ctx.fillRect(0, 0, cv.width, cv.height); },
    set(x, y, col) { ctx.fillStyle = col; ctx.fillRect(x * px, y * py, px, py); } };
}
// Lazy start: run fn when the figure first scrolls near the viewport (draw a still first frame immediately).
function whenVisible(node, fn) {
  if (!('IntersectionObserver' in window)) { fn(); return; }
  const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); fn(); } }, { rootMargin: '200px' });
  io.observe(node);
}
function animLoop(node, step, fps) {
  // calls step() at fps while the node is on screen
  let on = false, last = 0, raf = 0, running = !REDUCED;
  const iv = 1000 / (fps || 30);
  function tick(t) { raf = 0; if (!on || !running) return; if (t - last >= iv) { last = t; step(); } raf = requestAnimationFrame(tick); }
  const io = new IntersectionObserver(es => { on = es.some(e => e.isIntersecting); if (on && !raf) raf = requestAnimationFrame(tick); });
  io.observe(node);
  return { play() { running = true; if (on && !raf) raf = requestAnimationFrame(tick); }, pause() { running = false; }, get running() { return running; } };
}
function playButton(loop) {
  const b = el('button', { type: 'button' }); const upd = () => b.textContent = loop.running ? 'Pause' : 'Play';
  b.addEventListener('click', () => { loop.running ? loop.pause() : loop.play(); upd(); }); upd(); return b;
}

// ------------------------------------------------------------------ ROM graphics
const BOB_COL = [0x8A, 0x3A, 0x0F];
function bobLayers(frame) {
  const p = rb(0x8247 + frame) | (rb(0x8254 + frame) << 8);
  const rows = {};
  const put = (L, r, v) => { (rows[r] = rows[r] || [0, 0, 0])[L] = v; };
  for (let y = 1; y <= 20; y++) put(0, 0x1E + y, rb(p + y));
  for (let y = 1; y <= 17; y++) put(1, 0x1E + y, rb(p + 19 + y));
  for (let y = 1; y <= 17; y++) put(2, 0x24 + y, rb(p + 35 + y));
  return rows;   // keys 0x1F .. 0x35
}
// combine three player bytes with PRIOR $31 multicolour rules -> colour byte or -1
function bobPixel(b, x, only) {
  const bit = 0x80 >> x;
  const p0 = !!(b[0] & bit), p1 = !!(b[1] & bit), p2 = !!(b[2] & bit);
  if (only != null) return [p0, p1, p2][only] ? BOB_COL[only] : -1;
  if (p0 && p1) return BOB_COL[0] | BOB_COL[1];
  if (p0) return BOB_COL[0]; if (p1) return BOB_COL[1]; if (p2) return BOB_COL[2];
  return -1;
}
function drawBob(pc, frame, ox, oy, only, flip) {
  const rows = bobLayers(frame);
  for (let r = 0x1F; r <= 0x35; r++) {
    const b = rows[r] || [0, 0, 0];
    for (let x = 0; x < 8; x++) { const c = bobPixel(b, x, only); if (c >= 0) pc.set(ox + x, oy + (flip ? 0x35 - r : r - 0x1F), rgb(c)); }
  }
}
function itemShape(i) {
  const p = rw(0x84C5 + 2 * i), w = rb(p), h = rb(p + 1), pts = rb(p + 2), nb = ((w - 1) >> 2) + 1;
  const pix = [];
  for (let r = 0; r < h; r++) { const line = []; for (let b = 0; b < nb; b++) { const v = rb(p + 3 + r * nb + b); for (let k = 0; k < 4; k++) line.push((v >> (6 - 2 * k)) & 3); } pix.push(line); }
  return { w, h, pts, pix };
}
const mutRow = (state, y) => rb(0x8591 + 12 * state + y);

// ------------------------------------------------------------------ masthead Bob
(function () {
  const cv = document.getElementById('mastbob'); if (!cv) return;
  const pc = { ctx: cv.getContext('2d'), set(x, y, c) { this.ctx.fillStyle = c; this.ctx.fillRect(x * 4, y * 2, 4, 2); } };
  cv.width = 8 * 4 * 2; cv.height = 22 * 2;
  const draw = f => { pc.ctx.clearRect(0, 0, cv.width, cv.height); drawBob(pc, f, 4, 0); };
  draw(1);
  if (!REDUCED) { let f = 0; const seq = [1, 2, 3, 2]; setInterval(() => { f = (f + 1) % seq.length; draw(seq[f]); }, 180); }
})();

// ------------------------------------------------------------------ movies (sparse XOR deltas, zlib)
const movieCache = {};
async function loadMovie(name) {
  if (movieCache[name]) return movieCache[name];
  const meta = D.movies[name];
  const p = (async () => {
    const ds = new Blob([b64u8(meta.bin)]).stream().pipeThrough(new DecompressionStream('deflate'));
    const buf = new Uint8Array(await new Response(ds).arrayBuffer());
    // index frames
    const offs = []; let o = 0;
    for (let f = 0; f < meta.n; f++) { const n = buf[o] | (buf[o + 1] << 8) | (buf[o + 2] << 16) | (buf[o + 3] << 24); offs.push([o + 4, n]); o += 4 + n; }
    return { meta, buf, offs };
  })();
  movieCache[name] = p; return p;
}
function makePlayer(host, name, opts) {
  opts = opts || {};
  const meta = D.movies[name];
  if (!meta) { host.append(el('div', { class: 'note', text: 'Movie data missing.' })); return null; }
  const W = meta.w, H = meta.h;
  const cv = el('canvas', { class: 'pix' }); cv.width = W; cv.height = H;
  cv.style.width = (opts.cssw || W * 2) + 'px'; cv.style.maxWidth = '100%';
  const ctx = cv.getContext('2d');
  const img = ctx.createImageData(W, H);
  const pal = meta.pal.map(h => [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]);
  const idx = new Uint8Array(W * H);
  let cur = -1, mv = null, playing = false, speed = 1, acc = 0, lastT = 0;
  const slider = el('input', { type: 'range', min: 0, max: meta.n - 1, value: 0, 'aria-label': 'Frame' });
  const lab = el('span', { class: 'val' });
  const btn = el('button', { type: 'button', text: 'Play' });
  const sp = el('button', { type: 'button', text: 'Speed 1x' });
  function applyDelta(f) {
    const [o, n] = mv.offs[f]; const b = mv.buf; let p = o, pos = 0; const end = o + n;
    while (p < end) {
      let skip = 0, sh = 0, v; do { v = b[p++]; skip |= (v & 0x7F) << sh; sh += 7; } while (v & 0x80);
      let cnt = 0; sh = 0; do { v = b[p++]; cnt |= (v & 0x7F) << sh; sh += 7; } while (v & 0x80);
      pos += skip; for (let i = 0; i < cnt; i++) idx[pos + i] ^= b[p + i]; p += cnt; pos += cnt;
    }
  }
  function seek(f) {
    f = Math.max(0, Math.min(meta.n - 1, f | 0));
    if (!mv) return;
    if (f < cur) { while (cur > f) { applyDelta(cur); cur--; } }
    else { while (cur < f) { cur++; applyDelta(cur); } }
    const d = img.data;
    for (let i = 0, j = 0; i < idx.length; i++, j += 4) { const c = pal[idx[i]]; d[j] = c[0]; d[j + 1] = c[1]; d[j + 2] = c[2]; d[j + 3] = 255; }
    ctx.putImageData(img, 0, 0);
    slider.value = cur;
    lab.textContent = 'frame ' + (cur * (meta.step || 1) + (meta.first || 0)) + (opts.timeLabel ? '  ' + (cur / meta.fps).toFixed(1) + ' s' : '');
    if (opts.onframe) opts.onframe(cur);
  }
  function tick(t) {
    if (!playing) return;
    const dt = Math.min(100, t - (lastT || t)); lastT = t; acc += dt * speed * meta.fps / 1000;
    let k = Math.floor(acc); acc -= k;
    if (k > 0) { let f = cur + k; if (f >= meta.n) f = opts.loop === false ? meta.n - 1 : 0; seek(f); if (f === meta.n - 1 && opts.loop === false) { stop(); } }
    requestAnimationFrame(tick);
  }
  function start() { if (!mv) return; playing = true; lastT = 0; btn.textContent = 'Pause'; requestAnimationFrame(tick); }
  function stop() { playing = false; btn.textContent = 'Play'; }
  btn.addEventListener('click', () => playing ? stop() : start());
  sp.addEventListener('click', () => { speed = speed === 1 ? 0.25 : speed === 0.25 ? 4 : 1; sp.textContent = 'Speed ' + (speed === 0.25 ? '1/4' : speed) + 'x'; });
  slider.addEventListener('input', () => { stop(); seek(+slider.value); });
  // poster
  if (meta.poster) { const im = new Image(); im.onload = () => ctx.drawImage(im, 0, 0); im.src = meta.poster; }
  host.append(cv, el('div', { class: 'ctl' }, btn, sp, slider, lab));
  whenVisible(host, async () => {
    try {
      mv = await loadMovie(name); seek(opts.start || 0);
      if (opts.autoplay && !REDUCED) start();
    } catch (e) { lab.textContent = 'Could not load the movie in this browser.'; }
  });
  return { seek: f => { stop(); seek(f); }, get frame() { return cur; }, start, stop };
}

// ------------------------------------------------------------------ figures
const FIG = {};

FIG.hero = body => { makePlayer(body, 'demo', { autoplay: true, cssw: 672, timeLabel: true }); };

FIG.blockdiagram = body => {
  body.innerHTML = `<svg viewBox="0 0 860 330" width="860" style="max-width:100%;height:auto" role="img" aria-label="Block diagram of the Atari 400">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8790a3"/></marker></defs>
  <g font-size="13" fill="#d8dce6">
  <rect x="20" y="130" width="130" height="70" rx="4" fill="#1b2030" stroke="#f0905a"/><text x="85" y="160" text-anchor="middle" font-weight="700">6502</text><text x="85" y="180" text-anchor="middle" fill="#8790a3" font-size="11">1.79 MHz</text>
  <rect x="200" y="20" width="620" height="22" rx="2" fill="#262b36"/><text x="510" y="36" text-anchor="middle" fill="#8790a3" font-size="11">address and data bus (16-bit address, 8-bit data)</text>
  <line x1="85" y1="130" x2="85" y2="42" stroke="#8790a3"/><line x1="85" y1="42" x2="200" y2="31" stroke="#8790a3"/>
  <rect x="200" y="80" width="120" height="70" rx="4" fill="#1b2030" stroke="#3a4152"/><text x="260" y="108" text-anchor="middle" font-weight="700">RAM</text><text x="260" y="128" text-anchor="middle" fill="#8790a3" font-size="11">16K, $0000-$3FFF</text>
  <rect x="340" y="80" width="120" height="70" rx="4" fill="#1b2030" stroke="#3a4152"/><text x="400" y="108" text-anchor="middle" font-weight="700">Cartridge</text><text x="400" y="128" text-anchor="middle" fill="#8790a3" font-size="11">16K, $8000-$BFFF</text>
  <rect x="480" y="80" width="120" height="70" rx="4" fill="#1b2030" stroke="#3a4152"/><text x="540" y="108" text-anchor="middle" font-weight="700">OS ROM</text><text x="540" y="128" text-anchor="middle" fill="#8790a3" font-size="11">font at $E000</text>
  <rect x="200" y="210" width="140" height="80" rx="4" fill="#1b2030" stroke="#86a6ff"/><text x="270" y="238" text-anchor="middle" font-weight="700">ANTIC $D400</text><text x="270" y="258" text-anchor="middle" fill="#8790a3" font-size="11">display list, DMA,</text><text x="270" y="274" text-anchor="middle" fill="#8790a3" font-size="11">DLI + VBI (NMI)</text>
  <rect x="380" y="210" width="140" height="80" rx="4" fill="#1b2030" stroke="#86a6ff"/><text x="450" y="238" text-anchor="middle" font-weight="700">GTIA $D000</text><text x="450" y="258" text-anchor="middle" fill="#8790a3" font-size="11">colour, players,</text><text x="450" y="274" text-anchor="middle" fill="#8790a3" font-size="11">collisions, button</text>
  <rect x="560" y="210" width="120" height="80" rx="4" fill="#1b2030" stroke="#86a6ff"/><text x="620" y="238" text-anchor="middle" font-weight="700">POKEY $D200</text><text x="620" y="258" text-anchor="middle" fill="#8790a3" font-size="11">4 voices, keys,</text><text x="620" y="274" text-anchor="middle" fill="#8790a3" font-size="11">RANDOM</text>
  <rect x="700" y="210" width="120" height="80" rx="4" fill="#1b2030" stroke="#3a4152"/><text x="760" y="238" text-anchor="middle" font-weight="700">PIA $D300</text><text x="760" y="258" text-anchor="middle" fill="#8790a3" font-size="11">joysticks</text>
  <g stroke="#8790a3"><line x1="260" y1="80" x2="260" y2="42"/><line x1="400" y1="80" x2="400" y2="42"/><line x1="540" y1="80" x2="540" y2="42"/>
  <line x1="270" y1="210" x2="270" y2="175"/><line x1="270" y1="175" x2="180" y2="175"/><line x1="180" y1="175" x2="180" y2="42"/>
  <line x1="450" y1="210" x2="450" y2="175"/><line x1="620" y1="210" x2="620" y2="175"/><line x1="760" y1="210" x2="760" y2="175"/><line x1="450" y1="175" x2="760" y2="175"/><line x1="660" y1="175" x2="660" y2="42"/></g>
  <line x1="340" y1="250" x2="378" y2="250" stroke="#f0905a" marker-end="url(#ah)"/><text x="359" y="243" text-anchor="middle" fill="#f0905a" font-size="10">pixels</text>
  <path d="M200,265 C150,265 120,240 110,202" fill="none" stroke="#f0905a" stroke-dasharray="4 3" marker-end="url(#ah)"/><text x="120" y="290" fill="#f0905a" font-size="11">halts the CPU to fetch (DMA); NMIs</text>
  <rect x="380" y="300" width="140" height="22" rx="3" fill="#2a1d14"/><text x="450" y="315" text-anchor="middle" fill="#ffd9c2" font-size="11">TV picture</text>
  <line x1="450" y1="290" x2="450" y2="300" stroke="#f0905a"/>
  </g></svg>`;
};

FIG.linebudget = body => {
  const rows = [
    { name: 'Blank line (vertical blank, borders)', parts: [['refresh', 9, '#86a6ff']], note: 'ANTIC only refreshes RAM' },
    { name: 'Game screen: one line of the mine (mode E)', parts: [['display list', 1, '#c08bff'], ['bitmap, 40 bytes', 40, '#f0905a'], ['players + missiles', 5, '#6fd3a9'], ['refresh', 9, '#86a6ff']], note: 'from ANTIC’s fetch rules' },
    { name: 'Title row of lights (mode 7, HSCROL 0)', parts: [['character data, 24 bytes', 24, '#f0905a'], ['players + missiles', 5, '#6fd3a9'], ['refresh', 9, '#86a6ff']], note: 'measured in the emulator' },
    { name: 'Title row of lights (mode 7, HSCROL 10-14)', parts: [['ANTIC in total (measured)', 36, '#f0905a']], note: 'measured in the emulator' }];
  const sc = 6.4, x0 = 10, W = 114 * sc + 40;
  let s = `<svg viewBox="0 0 ${W} ${rows.length * 74 + 30}" width="${W}" style="max-width:100%;height:auto" role="img" aria-label="Cycle budget of a scan line">`;
  rows.forEach((r, i) => {
    const y = 20 + i * 74; let x = x0; let used = 0;
    s += `<text x="${x0}" y="${y - 4}" fill="#d8dce6" font-size="13">${r.name}</text><text x="${x0 + 114 * sc}" y="${y - 4}" fill="#8790a3" font-size="11" text-anchor="end">${r.note}</text>`;
    for (const [lab, n, col] of r.parts) { s += `<rect x="${x}" y="${y}" width="${n * sc}" height="26" fill="${col}" opacity="0.85"><title>${lab}: ${n} cycles</title></rect>`; x += n * sc; used += n; }
    const cpu = 114 - used;
    s += `<rect x="${x}" y="${y}" width="${cpu * sc}" height="26" fill="#2b3242" stroke="#3a4152"/><text x="${x + cpu * sc / 2}" y="${y + 17}" fill="#f4f1ea" font-size="12" text-anchor="middle">6502: ${cpu} cycles</text>`;
    s += `<text x="${x0}" y="${y + 44}" fill="#8790a3" font-size="11">ANTIC: ${r.parts.map(p => p[0] + ' ' + p[1]).join(' · ')}</text>`;
  });
  s += `</svg>`;
  body.innerHTML = s;
  body.append(el('div', { class: 'note', text: 'A scan line is 114 cycles of 1.79 MHz. ANTIC’s fetches are spread across the line, not grouped as drawn here; the bars show only how many cycles each kind takes.' }));
};

FIG.framebudget = body => {
  // 262 lines; screen layout of the game display list
  const H = 262, sy = 1.6, W = 820;
  const y = l => 10 + l * sy;
  let s = `<svg viewBox="0 0 ${W} ${H * sy + 30}" width="${W}" style="max-width:100%;height:auto" role="img" aria-label="Frame timeline">`;
  const band = (a, b, col, lab) => s += `<rect x="60" y="${y(a)}" width="160" height="${(b - a) * sy}" fill="${col}"/><text x="230" y="${y((a + b) / 2) + 4}" fill="#8790a3" font-size="11">${lab}</text>`;
  band(0, 8, '#1b2030', 'lines 0-7: top of the frame');
  band(8, 32, '#161a24', '24 blank lines');
  band(32, 40, '#2b3242', 'status line (mode 2)');
  band(40, 87, '#2a1d14', 'band 1');
  band(87, 134, '#24190f', 'band 2');
  band(134, 181, '#2a1d14', 'band 3');
  band(181, 224, '#24190f', 'band 4');
  band(224, 248, '#161a24', 'bottom border');
  band(248, 262, '#1b2030', 'vertical blank starts at line 248');
  for (let l = 0; l <= 260; l += 20) s += `<text x="52" y="${y(l) + 4}" fill="#5a6273" font-size="10" text-anchor="end">${l}</text>`;
  // handlers: DLIs at 39, 86, 133, 180 ; VBI at 248 (wraps)
  const cpuLine = 59, cpuBlank = 105;
  const marks = [[39, 'DLI 1', 592, 1212, cpuLine], [86, 'DLI 2', 256, 256, cpuLine], [133, 'DLI 3', 378, 713, cpuLine], [180, 'DLI 4', 431, 766, cpuLine]];
  for (const [l, lab, mean, max, cpl] of marks) {
    s += `<line x1="55" y1="${y(l + 1)}" x2="470" y2="${y(l + 1)}" stroke="#f0905a" stroke-dasharray="3 3"/>`;
    s += `<rect x="480" y="${y(l + 1)}" width="26" height="${max / cpl * sy}" fill="#f0905a" opacity="0.25"/><rect x="480" y="${y(l + 1)}" width="26" height="${mean / cpl * sy}" fill="#f0905a"/>`;
    s += `<text x="514" y="${y(l + 1) + 11}" fill="#f4f1ea" font-size="11">${lab}: ${mean} cycles average${max > mean ? ', ' + max + ' at most' : ''}</text>`;
  }
  const vbiLines = 3030 / cpuBlank;
  s += `<line x1="55" y1="${y(248)}" x2="470" y2="${y(248)}" stroke="#86a6ff" stroke-dasharray="3 3"/>`;
  s += `<rect x="480" y="${y(248)}" width="26" height="${(262 - 248) * sy}" fill="#86a6ff"/><rect x="480" y="${y(0)}" width="26" height="${(vbiLines - 14) * sy}" fill="#86a6ff"/>`;
  s += `<text x="514" y="${y(248) + 11}" fill="#f4f1ea" font-size="11">GAME_VBI: about 3,030 cycles</text><text x="514" y="${y(0) + 11}" fill="#8790a3" font-size="11">(runs on into the top of the next frame)</text>`;
  s += `<text x="480" y="${y(262) + 18}" fill="#8790a3" font-size="10.5">bar height = CPU time in scan lines (pale: the longest call seen)</text>`;
  s += `</svg>`;
  body.innerHTML = s;
};

FIG.stations = body => {
  const names = ['The Mine Shaft', 'The Slides', 'The Transporters', 'The Lillipads', 'Advanced Lillipads', 'Radioactive Waste', 'Advanced Transporters', 'The Lift', 'The Pulverizers', 'The Cannon'];
  const tabs = el('div', { class: 'tabs', role: 'tablist' });
  const img = el('img', { class: 'pix', alt: '', width: 336, height: 224 }); img.style.width = '672px';
  const cap = el('div', { class: 'note' });
  let cur = 0;
  const show = i => { cur = i; img.src = D.shots['st_' + (i + 1)]; img.alt = 'Station ' + (i + 1) + ', ' + names[i]; cap.textContent = 'Station ' + (i + 1) + ': ' + names[i]; [...tabs.children].forEach((b, k) => b.classList.toggle('on', k === i)); };
  names.forEach((n, i) => tabs.append(el('button', { type: 'button', text: String(i + 1), title: n, onclick: () => show(i) })));
  body.append(tabs, img, cap); show(0);
};

FIG.pointers = body => {
  const GT = ['HPOSP0/M0PF', 'HPOSP1/M1PF', 'HPOSP2/M2PF', 'HPOSP3/M3PF', 'HPOSM0/P0PF', 'HPOSM1/P1PF', 'HPOSM2/P2PF', 'HPOSM3/P3PF', 'SIZEP0/M0PL', 'SIZEP1/M1PL', 'SIZEP2/M2PL', 'SIZEP3/M3PL', 'SIZEM/P0PL', 'GRAFP0/P1PL', 'GRAFP1/P2PL', 'GRAFP2/P3PL', 'GRAFP3/TRIG0', 'GRAFM/TRIG1', 'COLPM0/TRIG2', 'COLPM1/TRIG3', 'COLPM2/PAL', 'COLPM3', 'COLPF0', 'COLPF1', 'COLPF2', 'COLPF3', 'COLBK', 'PRIOR', 'VDELAY', 'GRACTL', 'HITCLR', 'CONSOL'];
  const PK = ['AUDF1/POT0', 'AUDC1/POT1', 'AUDF2/POT2', 'AUDC2/POT3', 'AUDF3/POT4', 'AUDC3/POT5', 'AUDF4/POT6', 'AUDC4/POT7', 'AUDCTL/ALLPOT', 'STIMER/KBCODE', 'SKRES/RANDOM', 'POTGO', '(unused)', 'SEROUT/SERIN', 'IRQEN/IRQST', 'SKCTL/SKSTAT'];
  let m5200 = false, sel = 0;
  const ex = [
    { t: 'STA (pCOLPF1),Y', y: 0, x: null, zp: 0x3E, d: 'Y = 0: the pointer at $3E is used as it is.' },
    { t: 'LDA (pSKRES),Y', y: 0, x: null, zp: 0x64, d: 'A read through the SKRES pointer returns RANDOM.' },
    { t: 'STA (pHPOSM0,X)  X=6', y: null, x: 6, zp: 0x18, d: 'X is added before the pointer is read: $18 + 6 = $1E, the HPOSM3 pointer.' },
    { t: 'STA (pCOLPF1,X)  X=8', y: null, x: 8, zp: 0x3E, d: '$3E + 8 = $46: the PRIOR pointer.' },
    { t: 'STA (pAUDF3+1,X)  X=0', y: null, x: 0, zp: 0x59, d: 'The bug in LAND_CHECK: the pointer is read from $59/$5A, half of one entry and half of the next.' }];
  const mt = el('div', { class: 'tabs' }), et = el('div', { class: 'tabs' });
  const tbl = el('table'); const out = el('div', { class: 'note' });
  const tw = el('div', { class: 'tbl' }, tbl); tw.style.maxHeight = '360px';
  function zpByte(a) {
    if (a < 0x10 || a > 0x6F) return null;
    const i = (a - 0x10) >> 1, lo = !((a - 0x10) & 1);
    const gt = i < 32;
    const page = gt ? (m5200 ? 0xC0 : 0xD0) : (m5200 ? 0xE8 : 0xD2);
    const r = gt ? i : i - 32;
    return lo ? r : page;
  }
  function render() {
    [...mt.children].forEach((b, k) => b.classList.toggle('on', k === (m5200 ? 1 : 0)));
    [...et.children].forEach((b, k) => b.classList.toggle('on', k === sel));
    const e = ex[sel]; const pa = (e.zp + (e.x || 0)) & 0xFF;
    const target = zpByte(pa) | (zpByte((pa + 1) & 0xFF) << 8);
    let h = '<thead><tr><th>Zero page</th><th>Pointer</th><th>Points to</th><th>Register (write/read)</th></tr></thead><tbody>';
    for (let i = 0; i < 48; i++) {
      const a = 0x10 + 2 * i, gt = i < 32, r = gt ? i : i - 32;
      const page = gt ? (m5200 ? 0xC0 : 0xD0) : (m5200 ? 0xE8 : 0xD2);
      const nm = gt ? GT[r] : PK[r];
      const hot = (a === pa || a + 1 === pa || a === ((pa + 1) & 0xFF) - 1 + 0) ? ' class="hot"' : '';
      h += `<tr${(a === pa || a === pa - 1) ? ' class="hot"' : ''}><td>${hex2(a)}/${hex2(a + 1)}</td><td>p${nm.split('/')[0]}</td><td>${hex4(page << 8 | r)}</td><td>${nm}</td></tr>`;
    }
    tbl.innerHTML = h + '</tbody>';
    out.innerHTML = `<b class="val">${e.t}</b>: ${e.d} Pointer bytes at ${hex2(pa)} and ${hex2(pa + 1)} = ${hex2(target & 0xFF)} ${hex2(target >> 8)}, so the ${e.t.startsWith('LDA') ? 'read' : 'write'} goes to <b class="val">${hex4(target)}</b> on the ${m5200 ? '5200' : '400/800'}.`;
    const row = tbl.querySelector('tr.hot'); if (row && body.dataset.seen) row.scrollIntoView({ block: 'nearest' });
  }
  mt.append(el('button', { type: 'button', text: 'Atari 400/800', onclick: () => { m5200 = false; render(); } }), el('button', { type: 'button', text: 'Atari 5200', onclick: () => { m5200 = true; render(); } }));
  ex.forEach((e, i) => et.append(el('button', { type: 'button', text: e.t, onclick: () => { sel = i; body.dataset.seen = 1; render(); } })));
  body.append(el('div', { class: 'lab', text: 'Machine' }), mt, el('div', { class: 'lab', text: 'Instruction' }), et, out, tw);
  render();
};

FIG.dlist = body => {
  const img = el('img', { class: 'pix', alt: 'Station 1', src: D.shots.st_1 }); img.style.width = '672px';
  const wrap = el('div'); wrap.style.position = 'relative'; wrap.style.display = 'inline-block'; wrap.style.maxWidth = '100%';
  const ov = el('div'); ov.style.cssText = 'position:absolute;left:0;right:0;border-top:2px solid #f0905a;border-bottom:2px solid #f0905a;background:rgba(240,144,90,0.12);pointer-events:none;display:none';
  wrap.append(img, ov);
  // atari800 screenshot rows: scan line = row + 8 (24 lines shown above line 32)
  const sc = l => l - 8;
  const items = [
    { a: '$2000', t: '$70 $70 $70', d: '3 x 8 blank lines', l0: 8, l1: 32 },
    { a: '$2003', t: '$C2 $D8 $20', d: 'mode 2 + LMS $20D8 + DLI: status line', l0: 32, l1: 40 },
    { a: '$2006', t: '$0E x 46, $8E', d: 'mode E, bitmap lines 0-46, DLI at the end', l0: 40, l1: 87 },
    { a: '$2035', t: '$0E x 46, $8E', d: 'bitmap lines 47-93, DLI at the end (LMS $3000 on line 96)', l0: 87, l1: 134 },
    { a: '$2066', t: '$0E x 46, $8E', d: 'bitmap lines 94-140, DLI at the end', l0: 134, l1: 181 },
    { a: '$2097', t: '$0E x 43', d: 'bitmap lines 141-183', l0: 181, l1: 224 },
    { a: '$20C0', t: '$41 $00 $20', d: 'JVB $2000: wait for vertical blank, start again', l0: 224, l1: 226 }];
  const list = el('div', { class: 'tbl' }); const t = el('table');
  t.innerHTML = '<thead><tr><th>Address</th><th>Bytes</th><th>Meaning</th></tr></thead>';
  const tb = el('tbody'); t.append(tb); list.append(t);
  items.forEach(it => {
    const tr = el('tr', {}, el('td', { text: it.a }), el('td', { text: it.t }), el('td', { text: it.d }));
    const on = () => { ov.style.display = 'block'; const h = img.getBoundingClientRect().height / 224; ov.style.top = (sc(it.l0) * h) + 'px'; ov.style.height = ((it.l1 - it.l0) * h) + 'px'; [...tb.children].forEach(r => r.classList.remove('hot')); tr.classList.add('hot'); };
    tr.addEventListener('mouseenter', on); tr.addEventListener('click', on); tr.tabIndex = 0; tr.addEventListener('focus', on);
    tb.append(tr);
  });
  const row = el('div', { class: 'row' }, wrap, list); list.style.flex = '1 1 300px';
  body.append(row, el('div', { class: 'note', text: 'Addresses after $2006 are where each group of lines begins; the real list has one byte per bitmap line (three for the LMS line). Screenshot rows start 8 scan lines into the frame.' }));
};

FIG.modee = body => {
  let v = 0b01101100;
  const cols = [0x00, 0x46, 0x96, 0xD8];
  const bits = el('div'); bits.style.cssText = 'display:grid;grid-template-columns:repeat(8,44px);gap:4px;margin-bottom:10px';
  const pc = pixCanvas(4, 1, 88, 60);
  const txt = el('div', { class: 'note' });
  const names = ['background (COLBK)', 'colour 1 (COLPF0)', 'colour 2 (COLPF1)', 'colour 3 (COLPF2)'];
  function render() {
    bits.innerHTML = '';
    for (let b = 7; b >= 0; b--) {
      const on = (v >> b) & 1;
      const btn = el('button', { type: 'button', text: on ? '1' : '0', 'aria-label': 'bit ' + b, onclick: () => { v ^= (1 << b); render(); } });
      btn.style.cssText = 'height:40px;font-size:18px;' + (Math.floor((7 - b) / 2) % 2 ? 'background:#262b36' : '');
      if (on) btn.classList.add('on');
      bits.append(btn);
    }
    for (let p = 0; p < 4; p++) pc.set(p, 0, rgb(cols[(v >> (6 - 2 * p)) & 3]));
    txt.innerHTML = 'byte <b class="val">' + hex2(v) + '</b> = ' + [0, 1, 2, 3].map(p => 'pixel ' + p + ': ' + ((v >> (6 - 2 * p)) & 3) + ' ' + names[(v >> (6 - 2 * p)) & 3]).join(' · ');
  }
  body.append(bits, pc.cv, txt); render();
};

// render the station 1 bitmap with colours [bk,c1,c2,c3] into a pixCanvas
const ST1 = b64u8(D.st1.bitmap);
function drawBitmap(pc, colours, bm, grey) {
  bm = bm || ST1;
  const img = pc.ctx.createImageData(160 * pc.px, 184 * pc.py);
  const cc = colours.map(c => grey ? [((c & 0x0E) / 14 * 230) | 0, ((c & 0x0E) / 14 * 230) | 0, ((c & 0x0E) / 14 * 230) | 0] : PAL[c]);
  const d = img.data, W = 160 * pc.px;
  for (let y = 0; y < 184; y++) for (let x = 0; x < 160; x++) {
    const b = bm[y * 40 + (x >> 2)], v = (b >> (6 - 2 * (x & 3))) & 3, c = cc[v];
    for (let dy = 0; dy < pc.py; dy++) for (let dx = 0; dx < pc.px; dx++) { const j = ((y * pc.py + dy) * W + x * pc.px + dx) * 4; d[j] = c[0]; d[j + 1] = c[1]; d[j + 2] = c[2]; d[j + 3] = 255; }
  }
  pc.ctx.putImageData(img, 0, 0);
}

FIG.colours = body => {
  let reg = [0, D.st1.c[1], D.st1.c[2], D.st1.c[3]];
  const rnd = () => (Math.random() * 256) | 0;
  function startStation() {   // START_STATION, line for line
    const z = reg.slice();               // $8A..$8D
    for (let x = 3; x >= 1; x--) z[x] &= 0xF0;
    for (let cnt = 3; cnt >= 1; cnt--) {
      let hue, lum;
      outer: for (;;) { hue = rnd() & 0xF0; for (let x = 3; x >= 1; x--) if ((z[x] & 0xF0) === hue) continue outer; break; }
      outer2: for (;;) { let a = rnd() & 0x06; if (!a) continue; lum = a + 2; for (let x = 3; x >= 1; x--) if ((z[x] & 0x0F) === lum) continue outer2; break; }
      z[cnt] = hue | lum;
    }
    reg = z;
  }
  const a = pixCanvas(160, 184, 2, 1), b = pixCanvas(160, 184, 2, 1);
  a.cv.style.width = '320px'; b.cv.style.width = '320px';
  const info = el('div', { class: 'note' });
  function render() {
    drawBitmap(a, [0, reg[1], reg[2], reg[3]]); drawBitmap(b, [0, reg[1], reg[2], reg[3]], null, true);
    info.innerHTML = ['colour 1 (items) ', 'colour 2 (ladders) ', 'colour 3 (girders) '].map((n, i) => n + '<b class="val">' + hex2(reg[i + 1]) + '</b> hue ' + (reg[i + 1] >> 4) + ', luminance ' + (reg[i + 1] & 15)).join(' · ');
  }
  body.append(el('div', { class: 'row' }, el('div', {}, el('div', { class: 'lab', text: 'Colour set' }), a.cv), el('div', {}, el('div', { class: 'lab', text: 'Black-and-white set (luminance only)' }), b.cv)),
    el('div', { class: 'ctl' }, el('button', { type: 'button', text: 'Next turn: pick new colours', onclick: () => { startStation(); render(); } })), info);
  render();
};

FIG.machines = body => {
  const crops = [['st_3', 138, 26, 42, 42, 'transporter booth 4 (station 3)'], ['st_8', 196, 166, 56, 44, 'the lift: player 3 at double width (station 8)'], ['st_9', 84, 160, 192, 50, 'four pulverizer heads under their beam (station 9)'], ['st_10', 224, 160, 50, 48, 'the cannon: missiles + player 3 (station 10)'], ['st_10', 4, 100, 118, 110, 'the TNT store (station 10)']];
  const row = el('div', { class: 'row' });
  for (const [s, x, y, w, h, cap] of crops) {
    const cv = el('canvas', { class: 'pix' }); cv.width = w; cv.height = h; cv.style.width = (w * (w > 150 ? 2 : 3)) + 'px';
    const im = new Image(); im.onload = () => cv.getContext('2d').drawImage(im, x, y, w, h, 0, 0, w, h); im.src = D.shots[s];
    row.append(el('div', { class: 'sprite-tile' }, cv, el('div', { class: 'cap', text: cap })));
  }
  body.append(row);
};

FIG.bob = body => {
  const tiles = el('div', { class: 'row' });
  const names = ['player 0  COLPM0 = $8A', 'player 1  COLPM1 = $3A', 'player 2  COLPM2 = $0F', 'combined (P0|P1 = $BA)'];
  for (let k = 0; k < 4; k++) {
    const pc = pixCanvas(8, 23, 12, 6); pc.fill('#0a0c11');
    drawBob(pc, 1, 0, 1, k < 3 ? k : null);
    tiles.append(el('div', { class: 'sprite-tile' }, pc.cv, el('div', { class: 'cap', text: names[k] })));
  }
  // walk animation along a girder
  const W = 120, H = 30; const pc = pixCanvas(W, H, 4, 2);
  let x = 0, f = 0, tick = 0;
  const seqR = [1, 2, 3, 2], seqL = [4, 5, 6, 5]; let dir = 1;
  function draw() {
    pc.fill('#0a0c11');
    for (let gx = 0; gx < W; gx++) { const col = rgb(0xD8); if ((gx >> 2) % 2 === 0) { pc.set(gx, 23, col); pc.set(gx, 25, col); pc.set(gx, 27, col); } else { pc.set(gx, 24, col); pc.set(gx, 26, col); } }
    drawBob(pc, (dir > 0 ? seqR : seqL)[f], x, 2);
  }
  const loop = animLoop(body, () => { tick++; if (tick % 2 === 0) { x += dir; if (x > W - 9 || x < 1) dir = -dir; } if (tick % 6 === 0) f = (f + 1) % 4; draw(); }, 60);
  draw();
  const frames = el('div', { class: 'row' });
  const fn = ['0 standing', '1 walk R', '2 walk R', '3 walk R', '4 walk L', '5 walk L', '6 walk L', '7 climb', '8 climb', '9 ladder top', '10 ladder top', '11 jump R', '12 jump L'];
  for (let k = 1; k <= 12; k++) { const p = pixCanvas(8, 23, 6, 3); p.fill('#0a0c11'); drawBob(p, k, 0, 1); frames.append(el('div', { class: 'sprite-tile' }, p.cv, el('div', { class: 'cap', text: fn[k] }))); }
  body.append(tiles, el('div', { class: 'lab', text: 'Walking (one pixel every other frame)' }), pc.cv, el('div', { class: 'ctl' }, playButton(loop)), el('div', { class: 'lab', text: 'All twelve frames' }), frames);
};

FIG.statemachine = body => {
  const N = { G: [355, 205, 'ON A GIRDER', 'walk, stand, claim', '#f0905a'], J: [355, 30, 'JUMPING', 'frames 11-12, JUMP_ARC', '#86a6ff'], F: [660, 30, 'FALLING', '1 line per frame', '#86a6ff'],
    S: [660, 390, 'SLIDING', 'SLIDE_LEN frames', '#86a6ff'], L: [355, 390, 'ON A LADDER', 'frames 7-10', '#86a6ff'], T: [40, 205, 'TRANSPORTER', 'SPECIAL 3-7', '#86a6ff'], M: [40, 390, 'MELTING', 'SPECIAL 1, then 2 = dead', '#e05252'] };
  const box = k => { const [x, y, t, s, c] = N[k]; return `<rect x="${x}" y="${y}" width="160" height="42" rx="4" fill="#1b2030" stroke="${c}" stroke-width="1.5"/><text x="${x + 80}" y="${y + 18}" text-anchor="middle" font-weight="700" font-size="12.5" fill="#f4f1ea">${t}</text><text x="${x + 80}" y="${y + 33}" text-anchor="middle" fill="#8790a3" font-size="10.5">${s}</text>`; };
  const ar = (x1, y1, x2, y2, lab, lx, ly, anc) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#8790a3" marker-end="url(#sa)"/><text x="${lx}" y="${ly}" fill="#c9cfdb" font-size="11" text-anchor="${anc || 'start'}">${lab}</text>`;
  body.innerHTML = `<svg viewBox="0 0 860 450" width="860" style="max-width:100%;height:auto" role="img" aria-label="Bob's state machine">
  <defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8790a3"/></marker></defs>
  <g font-family="JetBrains Mono, monospace">
  <g fill="#8790a3" font-size="11"><text x="10" y="20" fill="#c9cfdb">MOVE_BOB tests, in order:</text>
  <text x="10" y="40">1  SPECIAL = 1     melting</text><text x="10" y="56">2  SPECIAL = 2     dead</text><text x="10" y="72">3  SPECIAL = 3-7   transporter</text>
  <text x="10" y="88">4  BOB_FALL       falling</text><text x="10" y="104">5  SLIDE_LEN      sliding</text><text x="10" y="120">6  at a slide top  start a slide</text>
  <text x="10" y="136">7  frame 11-12     jumping</text><text x="10" y="152">8  frame 7-10      ladder</text><text x="10" y="168">9  otherwise       on a girder</text></g>
  ${Object.keys(N).map(box).join('')}
  ${ar(405, 205, 405, 74, 'fresh button press', 398, 150, 'end')}
  ${ar(465, 74, 465, 205, 'lands on a girder', 472, 150)}
  ${ar(515, 51, 658, 51, 'past the arc, no girder', 586, 44, 'middle')}
  ${ar(515, 215, 670, 74, 'walks off an edge', 560, 120, 'end')}
  ${ar(700, 74, 515, 235, 'lands (40+ frames: dies)', 640, 175)}
  ${ar(515, 240, 680, 388, 'exactly at a slide top', 690, 250)}
  ${ar(710, 388, 515, 245, 'SLIDE_LEN runs out', 720, 300)}
  ${ar(405, 247, 405, 388, 'stick up/down at a ladder', 398, 330, 'end')}
  ${ar(465, 388, 465, 247, 'reaches the top or bottom', 472, 378)}
  ${ar(355, 218, 202, 218, 'still in a booth + digit', 278, 212, 'middle')}
  ${ar(202, 236, 355, 236, 'reformed at the new booth', 278, 254, 'middle')}
  ${ar(370, 247, 200, 392, 'mutant, hazard or timer', 270, 300, 'end')}
  </g></svg>`;
};

FIG.jump = body => {
  const arc = []; for (let i = 0; i < 32; i++) { let v = rb(0xBFBD + i); arc.push(v > 127 ? v - 256 : v); }
  const prof = [0]; let y = 0; for (let i = 0; i < 64; i++) { y += i < 32 ? arc[i] : 1; prof.push(y); }
  const W = 150, H = 70; const pc = pixCanvas(W, H, 4, 2);
  const gY = 40; let t = 0;
  const plot = el('canvas'); plot.width = 600; plot.height = 200; plot.style.maxWidth = '100%';
  const g = plot.getContext('2d');
  function drawPlot(k) {
    g.fillStyle = '#0a0c11'; g.fillRect(0, 0, 600, 200);
    g.strokeStyle = '#262b36'; g.lineWidth = 1;
    for (let i = 0; i <= 60; i += 10) { g.beginPath(); g.moveTo(30 + i * 9, 10); g.lineTo(30 + i * 9, 178); g.stroke(); g.fillStyle = '#5a6273'; g.font = '10px JetBrains Mono, monospace'; g.fillText(String(i), 26 + i * 9, 192); }
    const yy = v => 90 + v * 4;
    g.strokeStyle = '#3a4152'; g.beginPath(); g.moveTo(30, yy(0)); g.lineTo(570, yy(0)); g.stroke();
    g.fillStyle = '#8790a3'; g.fillText('take-off', 32, yy(0) - 4); g.fillText('+16 lines', 4, yy(-16) + 3);
    g.fillStyle = '#e05252'; g.fillRect(30 + 60 * 9, yy(19) - 1, 6, 3); g.fillText('19 below: fatal', 470, yy(19) - 5);
    g.strokeStyle = '#f0905a'; g.lineWidth = 2; g.beginPath();
    for (let i = 0; i <= 60; i++) { const X = 30 + i * 9, Y = yy(prof[i]); i ? g.lineTo(X, Y) : g.moveTo(X, Y); }
    g.stroke();
    g.fillStyle = '#86a6ff'; g.fillRect(30 + 21 * 9, 180, 39 * 9, 3); g.fillText('LAND_CHECK counts FALL_LEN from here', 30 + 21 * 9, 175);
    g.fillStyle = '#f4f1ea'; g.beginPath(); g.arc(30 + k * 9, yy(prof[k]), 4, 0, 7); g.fill();
    g.fillStyle = '#8790a3'; g.fillText('frames since the button', 30, 12);
  }
  function draw() {
    const k = t % 62; const i = Math.min(k, 60);
    pc.fill('#0a0c11');
    for (let x = 0; x < W; x++) { const c = rgb(0xD8); pc.set(x, gY + 21, c); pc.set(x, gY + 23, c); pc.set(x, gY + 25, c); }
    const bx = 30 + Math.floor(i / 2), by = gY + prof[i];
    drawBob(pc, 11, bx, by);
    drawPlot(i);
  }
  const loop = animLoop(body, () => { t++; draw(); }, 20);
  draw();
  const step = el('button', { type: 'button', text: 'Step', onclick: () => { loop.pause(); t++; draw(); } });
  body.append(pc.cv, plot, el('div', { class: 'ctl' }, playButton(loop), step), el('div', { class: 'note', text: 'Shown at a third of the game’s speed. The table: ' + arc.slice(0, 30).map(v => (v > 0 ? '+' : '') + v).join(' ') + ' | ' + arc.slice(30).join(' ') + ' (BOB_SIZE)' }));
};

FIG.melt = body => {
  // three player columns, rows 0..0x3F (only the part around Bob)
  let cols, moveB, done, wait;
  const BY = 0x20; // pretend BOB_Y; sprite rows BY..BY+20 ; feet line BY+0x15
  function reset() {
    cols = [new Uint8Array(0x60), new Uint8Array(0x60), new Uint8Array(0x60)];
    const rows = bobLayers(1);
    for (let r = 0x1F; r <= 0x35; r++) { const b = rows[r] || [0, 0, 0]; for (let L = 0; L < 3; L++) cols[L][BY + (r - 0x1F)] = b[L]; }
    moveB = BY; done = false; wait = 20;
  }
  const pc = pixCanvas(8, 0x30, 14, 6);
  function draw() {
    pc.fill('#0a0c11');
    for (let r = 0x10; r < 0x40; r++) for (let x = 0; x < 8; x++) { const c = bobPixel([cols[0][r], cols[1][r], cols[2][r]], x); if (c >= 0) pc.set(x, r - 0x10, rgb(c)); }
    pc.ctx.fillStyle = '#f0905a'; pc.ctx.fillRect(0, (moveB - 0x10) * 6, 8 * 14, 2);
    pc.ctx.fillStyle = '#86a6ff'; pc.ctx.fillRect(0, (BY + 0x15 - 0x10) * 6 + 5, 8 * 14, 1);
  }
  function step() {
    if (wait > 0) { wait--; return; }
    if (done) { reset(); return; }
    const feet = BY + 0x15;
    for (let L = 0; L < 3; L++) { const c = cols[L]; let y = feet; c[y] = (Math.random() * 256) | 0; while (true) { y -= 2; const v = c[y]; y++; c[y] = v; if (y === moveB) break; } }
    moveB++;
    if (moveB === BY + 0x11) { done = true; wait = 40; }
    draw();
  }
  reset(); draw();
  const loop = animLoop(body, step, 12);
  body.append(el('div', { class: 'row' }, pc.cv, el('div', { class: 'note', html: 'Orange line: MOVE_B, the top of the part that shifts. Blue line: the feet line, where a random byte enters each frame.<br>MELT_BOB runs once per frame; shown here at 12 frames a second.' })),
    el('div', { class: 'ctl' }, playButton(loop), el('button', { type: 'button', text: 'Melt again', onclick: () => { reset(); draw(); } })));
};

FIG.claim = body => {
  const bm = ST1.slice();
  const lineOf = y => y - 8;            // game y (8..191) -> bitmap row
  const rd = (bmx, xpm, y) => { const p = (xpm - 0x30) & 0xFF, r = Math.max(8, Math.min(191, y)); const b = bmx[lineOf(r) * 40 + (p >> 2)]; return (b >> (6 - 2 * (p & 3))) & 3; };
  const wr = (bmx, xp, y, c) => { const a = lineOf(y) * 40 + (xp >> 2), s = 6 - 2 * (xp & 3); bmx[a] = (bmx[a] & ~(3 << s) & 0xFF) | (c << s); };
  function claimAt(bmx, xfoot, feet, log) {    // CLAIM_AT, ported (x in P/M units)
    let x = xfoot & 0xFF, y = feet, n;
    if (rd(bmx, x, y) !== 3) { log.push('no girder under the foot'); return null; }
    y++;
    if (rd(bmx, x, y) !== 3) n = 3; else { y++; if (rd(bmx, x, y) === 3) { log.push('lines +1 and +2 are solid: already claimed'); return null; } n = 2; }
    log.push(n === 3 ? 'line +1 is background: gaps at +1, +3, +5' : 'line +1 solid, +2 background: gaps at +2, +4');
    x = (x - 1) & 0xFF;
    if (rd(bmx, x, y) !== 3) {
      let cnt = 3, edge = false;
      for (;;) { x = (x - 1) & 0xFF; if (x === 0x2F) { x = (x + 5 - cnt) & 0xFF; edge = true; break; } if (rd(bmx, x, y) === 3) break; cnt--; if (cnt === 0) { x = (x + 5) & 0xFF; break; } }
      if (edge || cnt === 0) { let g = 0; while (rd(bmx, x, y) !== 3 && g++ < 300) x = (x + 1) & 0xFF; x = (x - 5) & 0xFF; log.push('scanned right for the section edge'); }
      else log.push('found the edge to the left');
    } else log.push('the foot is on the first pixel of the section');
    x = (x + 1) & 0xFF; const px = (x - 0x30) & 0xFF; const rows = [];
    for (let r = 0; r < n; r++) { for (let k = 0; k < 4; k++) wr(bmx, (px + k) & 0xFF, y, 3); rows.push(y); y += 2; }
    return { px, rows };
  }
  const cols = [0, D.st1.c[1], D.st1.c[2], D.st1.c[3]];
  const pc = pixCanvas(160, 184, 2, 1); pc.cv.style.width = '640px'; pc.cv.style.height = 'auto'; pc.cv.style.cursor = 'crosshair';
  const zoom = pixCanvas(24, 9, 16, 12);
  const info = el('div', { class: 'note' }); const bytes = el('pre', { class: 'note' }); bytes.style.cssText = 'font-family:var(--font-mono);white-space:pre;margin:6px 0 0';
  let sections = D.st1.sections || 0, claimed = 0, last = null;
  function render() {
    drawBitmap(pc, cols, bm);
    if (last) { pc.ctx.strokeStyle = '#ffffff'; pc.ctx.lineWidth = 1; pc.ctx.strokeRect(last.px * 2 - 2.5, lineOf(last.rows[0]) - 4.5, 12, last.rows.length * 2 + 6); }
  }
  function zoomAt(px, y, before) {
    zoom.fill('#0a0c11');
    for (let yy = 0; yy < 9; yy++) for (let xx = 0; xx < 24; xx++) {
      const X = px - 10 + xx, Y = y - 1 + yy; if (X < 0 || X > 159 || Y < 8 || Y > 191) continue;
      const v = rd(before ? before : bm, X + 0x30, Y); zoom.set(xx, yy, rgb([0, cols[1], cols[2], cols[3]][v]));
    }
  }
  pc.cv.addEventListener('click', e => {
    const r = pc.cv.getBoundingClientRect();
    const px = Math.floor((e.clientX - r.left) / r.width * 160), row = Math.floor((e.clientY - r.top) / r.height * 184);
    // find the top line of a girder at or below the click, within 6 lines
    let y = row + 8, found = -1;
    for (let k = -3; k <= 6; k++) { const yy = y + k; if (yy < 9 || yy > 190) continue; if (rd(bm, px + 0x30, yy) === 3 && rd(bm, px + 0x30, yy - 1) !== 3 && rd(bm, px + 0x30, yy - 2) !== 3) { found = yy; break; } }
    const log = [];
    if (found < 0) { info.textContent = 'No girder top near there. Click on a girder.'; return; }
    const before = bm.slice();
    const res = claimAt(bm, px + 0x30, found, log);
    if (res) { claimed++; last = res; }
    render(); zoomAt(px, found, null);
    const line = lineOf(found + (res ? (res.rows[0] - found) : 1));
    const a0 = Math.max(0, (px >> 2) - 2);
    let s = 'gap row ' + (res ? res.rows[0] : found + 1) + ', bytes ' + hex4(0x2100 + line * 40 + a0) + '...\nbefore: ';
    for (let i = 0; i < 6; i++) s += hex2(before[line * 40 + a0 + i]) + ' ';
    s += '\nafter:  '; for (let i = 0; i < 6; i++) s += hex2(bm[line * 40 + a0 + i]) + ' ';
    bytes.textContent = s;
    info.innerHTML = 'Foot at x ' + hex2(px + 0x30) + ', feet line ' + found + ': ' + log.join('; ') + '. ' + (res ? '<b class="val">Claimed: SECTIONS - 1, score + 5.</b> Sections claimed here: ' + claimed + '.' : '');
  });
  render(); info.textContent = 'Click on any girder.';
  setTimeout(() => { // an example claim on the top girder
    const r = pc.cv.getBoundingClientRect(); if (!r.width) return;
    for (let y = 9; y < 191; y++) if (rd(bm, 0x30 + 60, y) === 3 && rd(bm, 0x30 + 60, y - 1) !== 3) { pc.cv.dispatchEvent(new MouseEvent('click', { clientX: r.left + 60.5 / 160 * r.width, clientY: r.top + (y - 8 + 0.5) / 184 * r.height })); break; }
  }, 0);
  body.append(el('div', { class: 'row' }, pc.cv, el('div', { style: 'flex:1 1 260px' }, el('div', { class: 'lab', text: 'Close-up after the claim' }), zoom.cv, info, bytes)),
    el('div', { class: 'ctl' }, el('button', { type: 'button', text: 'Reset the station', onclick: () => { bm.set(ST1); claimed = 0; last = null; render(); info.textContent = 'Click on any girder.'; bytes.textContent = ''; } })));
};

// station-1 frame reconstructed from harness RAM: bitmap + P/M memory + mutant records
const PM = b64u8(D.st1.pm);            // $0300-$07FF
const MUT = D.st1.mut;
function pmGroups(off) { const g = []; let s = -1; for (let r = 0; r < 256; r++) { const v = PM[off + r]; if (v && s < 0) s = r; if (!v && s >= 0) { g.push([s, r - 1]); s = -1; } } return g; }

FIG.bands = body => {
  // screen: 160 px x 224 scan lines (8..231); bitmap at scan 40.. (y+32)
  const SW = 160, SH = 232;
  const pc = pixCanvas(SW + 70, SH, 2, 1); pc.cv.style.width = ((SW + 70) * 4) + 'px';
  const cols = [0, D.st1.c[1], D.st1.c[2], D.st1.c[3]];
  const bmImg = pixCanvas(160, 184, 1, 1); drawBitmap(bmImg, cols);
  const dliScan = [39, 86, 133, 180];               // last line of status line, bitmap rows 46, 93, 140
  const bandsP3 = [], bandsM = [];
  for (let b = 0; b < 4; b++) { const r0 = MUT.slice(22 * b, 22 * b + 11), r1 = MUT.slice(22 * b + 11, 22 * b + 22); bandsP3.push(r0[0] ? { x: r0[0], c: r0[3] } : null); bandsM.push(r1[0] ? { x: r1[0], c: r1[3] } : null); }
  const gP3 = pmGroups(0x400).filter(g => g[0] > 40), gM = pmGroups(0).filter(g => g[0] > 40);
  let beam = 8;
  function bandAt(scan) { let b = 0; for (const d of dliScan) if (scan > d) b++; return b; }   // 0 = status, 1..4
  function draw() {
    const ctx = pc.ctx; ctx.fillStyle = '#05060a'; ctx.fillRect(0, 0, pc.cv.width, pc.cv.height);
    ctx.drawImage(bmImg.cv, 0, 0, 160, 184, 0, 40, 320, 184);
    // status line stand-in
    ctx.fillStyle = '#1b2030'; ctx.fillRect(0, 32, 320, 8);
    // sprites, drawn line by line using the positions in force on that line
    const upto = beam;
    for (let s = 32; s < Math.min(upto, 224); s++) {
      const b = bandAt(s); const p3 = b >= 1 ? bandsP3[b - 1] : null, m = b >= 1 ? bandsM[b - 1] : null;
      if (p3) { const v = PM[0x400 + s]; for (let x = 0; x < 8; x++) if (v & (0x80 >> x)) { ctx.fillStyle = rgb(p3.c); ctx.fillRect((p3.x - 48 + x) * 2, s, 2, 1); } }
      if (m) { const v = PM[s]; for (let x = 0; x < 8; x++) if (v & (0x80 >> x)) { ctx.fillStyle = rgb(m.c); ctx.fillRect((m.x - 48 + x) * 2, s, 2, 1); } }
      // Bob: players 0-2
      const bx = D.st1.bob[0]; for (let x = 0; x < 8; x++) { const c = bobPixel([PM[0x100 + s], PM[0x200 + s], PM[0x300 + s]], x); if (c >= 0) { ctx.fillStyle = rgb(c); ctx.fillRect((bx - 48 + x) * 2, s, 2, 1); } }
    }
    // dim the part not yet drawn
    ctx.fillStyle = 'rgba(5,6,10,0.78)'; ctx.fillRect(0, upto, 320, SH - upto);
    // DLI marks
    for (const d of dliScan) { ctx.fillStyle = upto > d ? '#f0905a' : '#5a3a28'; ctx.fillRect(0, d, 320, 1); }
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, Math.min(upto, SH - 1), 320, 1);
    // strips: missile memory and player 3 memory
    const sx1 = 330, sx2 = 390;
    for (let s = 0; s < SH; s++) {
      const vm = PM[s], vp = PM[0x400 + s];
      for (let x = 0; x < 8; x++) { if (vm & (0x80 >> x)) { ctx.fillStyle = '#c9cfdb'; ctx.fillRect(sx1 + x * 2, s, 2, 1); } if (vp & (0x80 >> x)) { ctx.fillStyle = '#c9cfdb'; ctx.fillRect(sx2 + x * 2, s, 2, 1); } }
    }
    ctx.fillStyle = '#262b36'; ctx.fillRect(sx1 - 2, 0, 1, SH); ctx.fillRect(sx2 - 2, 0, 1, SH);
    const b = bandAt(upto - 1);
    if (b >= 1) {
      const p3 = bandsP3[b - 1], m = bandsM[b - 1];
      lab.innerHTML = 'Beam at scan line ' + upto + ', band ' + b + ': player 3 at ' + (p3 ? '<b class="val">HPOSP3 = ' + hex2(p3.x) + '</b>' : 'not used') + ', missiles at ' + (m ? '<b class="val">HPOSM3 = ' + hex2(m.x) + '</b>' : 'not used') + '.';
    } else lab.textContent = 'Beam at scan line ' + upto + ': above the mine.';
  }
  const lab = el('div', { class: 'note' });
  const loop = animLoop(body, () => { beam += 2; if (beam > SH + 20) beam = 8; draw(); }, 30);
  beam = 120; draw();
  body.append(pc.cv, el('div', { class: 'row' }, el('div', { class: 'note', html: 'Right: the missile strip ($0300) and the player-3 strip ($0700) of player/missile memory, full height. Orange lines: the display-list interrupts.' })), lab, el('div', { class: 'ctl' }, playButton(loop)));
};

FIG.fifth = body => {
  const shape = []; for (let y = 0; y < 10; y++) shape.push(mutRow(0, y));
  const mcol = ['#f0905a', '#86a6ff', '#6fd3a9', '#e0c35a'];
  let s = `<svg viewBox="0 0 820 300" width="820" style="max-width:100%;height:auto" role="img" aria-label="Fifth player">`;
  s += `<text x="10" y="18" fill="#8790a3" font-size="11">missile bytes, one per line</text>`;
  for (let y = 0; y < 10; y++) for (let b = 0; b < 8; b++) {
    const on = (shape[y] >> (7 - b)) & 1, m = 3 - (b >> 1);
    s += `<rect x="${10 + b * 22}" y="${28 + y * 22}" width="20" height="20" fill="${on ? mcol[3 - m] : '#1b2030'}" stroke="#262b36"/>`;
  }
  for (let m = 0; m < 4; m++) s += `<text x="${10 + (3 - m) * 44 + 21}" y="${262}" fill="${mcol[3 - m]}" font-size="10" text-anchor="middle">M${m}</text>`;
  s += `<text x="200" y="140" fill="#8790a3" font-size="20">→</text>`;
  s += `<text x="250" y="18" fill="#8790a3" font-size="11">the four missiles, each 2 wide, placed side by side</text>`;
  for (let m = 3; m >= 0; m--) {
    const X = 250 + (3 - m) * 100;
    s += `<text x="${X + 22}" y="${262}" fill="${mcol[3 - m]}" font-size="11" text-anchor="middle">HPOSM${m} = x+${(3 - m) * 2}</text>`;
    for (let y = 0; y < 10; y++) for (let b = 0; b < 2; b++) { const on = (shape[y] >> (2 * m + 1 - b)) & 1; s += `<rect x="${X + b * 22}" y="${28 + y * 22}" width="20" height="20" fill="${on ? mcol[3 - m] : '#1b2030'}" stroke="#262b36"/>`; }
  }
  s += `<text x="250" y="288" fill="#d8dce6" font-size="12">Together: the 8-pixel row again, coloured by COLPF3 (PRIOR bit 4).</text></svg>`;
  body.innerHTML = s;
};

FIG.mutants = body => {
  const names = ['right, step 1', 'right, step 2', 'left, step 1', 'left, step 2', 'edible R 1', 'edible R 2', 'edible L 1', 'edible L 2', 'eaten: 80', 'eaten: 90'];
  const row = el('div', { class: 'row' });
  for (let k = 0; k < 10; k++) {
    const pc = pixCanvas(8, 10, 12, 6); pc.fill('#0a0c11');
    const col = k >= 4 && k < 8 ? 0xC6 : k < 4 ? 0x46 : 0x0E;
    for (let y = 0; y < 10; y++) { const v = mutRow(k, y); for (let x = 0; x < 8; x++) if (v & (0x80 >> x)) pc.set(x, y, rgb(col)); }
    row.append(el('div', { class: 'sprite-tile' }, pc.cv, el('div', { class: 'cap', text: 'state ' + k + '\n' + names[k] })));
  }
  const W = 110; const an = pixCanvas(W, 16, 4, 2); let x = 4, dir = 1, st = 0, t = 0, ed = false;
  function draw() {
    an.fill('#0a0c11'); const col = ed ? (t % 20 < 14 ? 0xC6 : 0x5A) : 0x46 + ((t >> 3) % 4) * 2;
    for (let gx = 0; gx < W; gx++) { an.set(gx, 12, rgb(0xD8)); an.set(gx, 14, rgb(0xD8)); }
    const state = (ed ? 4 : 0) + (dir > 0 ? 0 : 2) + st;
    for (let y = 0; y < 10; y++) { const v = mutRow(state, y); for (let xx = 0; xx < 8; xx++) if (v & (0x80 >> xx)) an.set(x + xx, y + 2, rgb(col)); }
  }
  const loop = animLoop(body, () => { t++; if (t % 3 === 0) { x += dir; if (x > W - 10 || x < 2) dir = -dir; } if (t % 10 === 0) st ^= 1; if (t % 240 === 0) ed = !ed; draw(); }, 30);
  draw();
  body.append(row, el('div', { class: 'lab', text: 'Patrolling, then edible' }), an.cv, el('div', { class: 'ctl' }, playButton(loop)));
};

FIG.items = body => {
  const pal = [-1, 0x46, 0x96, 0xD8];
  const names = { 1: '"100"', 2: '"200"', 3: '"300"', 4: '"400"', 5: '"500"', 11: '"1100"', 26: 'BF logo', 33: 'goblet', 34: 'TNT 3 t', 35: 'TNT 2 t', 36: 'TNT 1 t' };
  const grid = el('div'); grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:14px;align-items:end';
  for (let i = 1; i <= 36; i++) {
    const s = itemShape(i); const w = s.pix[0] ? s.pix[0].length : 4;
    const pc = pixCanvas(w, Math.max(1, s.h), 4, 2); pc.fill('#0a0c11');
    s.pix.forEach((line, y) => line.forEach((v, x) => { if (v) pc.set(x, y, rgb(pal[v])); }));
    grid.append(el('div', { class: 'sprite-tile' }, pc.cv, el('div', { class: 'cap', text: i + (names[i] ? ' ' + names[i] : '') + (i > 5 && i !== 11 ? '\n' + s.pts * 100 + ' pts' : '') })));
  }
  body.append(grid);
};

FIG.titlemovie = body => { makePlayer(body, 'title', { autoplay: true }); };
FIG.creditsmovie = body => { makePlayer(body, 'credits', { timeLabel: true, start: 400 }); };

FIG.beam = body => {
  const tr = D.ktrace['8'];
  // take the second pass (line 34): rows with y == 34 plus the LDA at the end of 33
  const cyc = { 'LDA': 2, 'STA': 4, 'ORA': 6, 'CMP': 4, 'CPX': 3, 'ASL': 5, 'DEX': 2, 'BEQ': 2, 'JMP': 3 };
  const pass = []; let started = false;
  for (let i = 0; i < tr.length; i++) {
    const [y, x, pc, ins] = tr[i];
    if (!started && y === 33 && pc === '0405') started = true;
    if (started) { pass.push({ y, x, pc, ins }); if (pass.length > 1 && pc === '0405') break; }
  }
  // absolute cycle positions relative to the start of line 34
  const pos = p => (p.y - 34) * 114 + p.x - (p.x >= 114 ? 0 : 0);
  const W = 860, sc = 6.6, X0 = 20;
  let s = `<svg viewBox="0 0 ${W} 210" width="${W}" style="max-width:100%;height:auto" role="img" aria-label="Kernel timing on one line">`;
  s += `<rect x="${X0}" y="40" width="${114 * sc}" height="34" fill="#11141b" stroke="#262b36"/>`;
  for (let c = 0; c <= 114; c += 10) s += `<line x1="${X0 + c * sc}" y1="74" x2="${X0 + c * sc}" y2="80" stroke="#3a4152"/><text x="${X0 + c * sc}" y="92" fill="#5a6273" font-size="10" text-anchor="middle">${c}</text>`;
  s += `<text x="${X0}" y="30" fill="#8790a3" font-size="11">one scan line, 114 cycles (HSCROL 8, emulator trace)</text>`;
  let stolen = 0;
  for (let i = 0; i < pass.length - 1; i++) {
    const a = pass[i], b = pass[i + 1];
    let st = (a.y - 34) * 114 + a.x, en = (b.y - 34) * 114 + b.x;
    const mn = a.ins.split(' ')[0]; const nom = cyc[mn] || 2; const got = en - st;
    const isW = mn === 'STA';
    const draw = (from, to, col) => { const f = Math.max(0, from), t2 = Math.min(114, to); if (t2 > f) s += `<rect x="${X0 + f * sc}" y="44" width="${(t2 - f) * sc - 1}" height="26" fill="${col}"/>`; };
    const colr = isW ? '#f0905a' : mn === 'ORA' || mn === 'CMP' || mn === 'CPX' || mn === 'ASL' ? '#4a5266' : '#2f4e8f';
    // wrap-around handling: map into 0..113 of line 34 and also from previous line
    const segs = [[st, st + nom, colr], [st + nom, en, '#7a1f1f']];
    for (const [f, t2, c] of segs) { draw(f, t2, c); draw(f - 114, t2 - 114, c); draw(f + 114, t2 + 114, c); }
    if (got > nom) stolen += got - nom;
    if (isW) { const wc = ((en - 1) % 114 + 114) % 114; s += `<line x1="${X0 + wc * sc}" y1="36" x2="${X0 + wc * sc}" y2="78" stroke="#ffd9c2"/><text x="${X0 + wc * sc}" y="112" fill="#ffd9c2" font-size="10" text-anchor="middle">${a.ins.split(' ')[1].replace('$D0', 'PF').replace('PF16', 'PF0').replace('PF17', 'PF1').replace('PF18', 'PF2').replace('PF19', 'PF3')}</text>`; }
  }
  s += `<rect x="${X0}" y="130" width="12" height="10" fill="#f0905a"/><text x="${X0 + 16}" y="139" fill="#c9cfdb" font-size="11">STA COLPFn (tick: the cycle the write happens)</text>`;
  s += `<rect x="${X0 + 330}" y="130" width="12" height="10" fill="#2f4e8f"/><text x="${X0 + 346}" y="139" fill="#c9cfdb" font-size="11">LDA #, DEX, BEQ, JMP</text>`;
  s += `<rect x="${X0 + 500}" y="130" width="12" height="10" fill="#4a5266"/><text x="${X0 + 516}" y="139" fill="#c9cfdb" font-size="11">padding and delay</text>`;
  s += `<rect x="${X0}" y="150" width="12" height="10" fill="#7a1f1f"/><text x="${X0 + 16}" y="159" fill="#c9cfdb" font-size="11">CPU halted while ANTIC fetches: ${stolen} cycles this pass</text>`;
  s += `<text x="${X0}" y="186" fill="#8790a3" font-size="11">Writes 1-4 (left lights' colours) fall in the first quarter of the line; writes 5-8 (right lights) in the middle.</text>`;
  s += `<text x="${X0}" y="202" fill="#8790a3" font-size="11">The emulator numbers cycles from its own reference point; the pattern repeats exactly on every line of the row.</text></svg>`;
  body.innerHTML = s;
};

FIG.demo = body => {
  // recording
  const rec = []; for (let a = 0x978C; a < 0x9818; a += 2) rec.push([rb(a), rb(a + 1)]);
  const total = rec.reduce((n, r) => n + r[1], 0);
  const meta = D.movies.demo;
  const track = el('canvas'); track.width = 900; track.height = 56; track.style.maxWidth = '100%'; track.style.width = '672px'; track.style.cursor = 'pointer';
  const tg = track.getContext('2d');
  const colOf = v => { const s = v & 15, btn = !(v & 16); if (btn) return '#f0905a'; if (s === 0x0F) return '#2b3242'; if (s === 0x07) return '#6fd3a9'; if (s === 0x0B) return '#86a6ff'; if (s === 0x0E) return '#e0c35a'; if (s === 0x0D) return '#c08bff'; return '#8790a3'; };
  const nameOf = v => { const s = v & 15, b = !(v & 16); const d = { 15: 'none', 7: 'right', 11: 'left', 14: 'up', 13: 'down', 6: 'up+right', 10: 'up+left', 5: 'down+right', 9: 'down+left' }[s] || hex2(s); return (b ? 'button + ' : '') + d; };
  const lab = el('div', { class: 'note' });
  let gframe = 0;
  function drawTrack(gf) {
    tg.fillStyle = '#0a0c11'; tg.fillRect(0, 0, 900, 56);
    let t = 0;
    for (const [v, n] of rec) { tg.fillStyle = colOf(v); tg.fillRect(t / total * 900, 8, Math.max(1, n / total * 900 - 1), 26); t += n; }
    const x = gf / total * 900; tg.fillStyle = '#ffffff'; tg.fillRect(x - 1, 2, 2, 38);
    tg.fillStyle = '#8790a3'; tg.font = '11px JetBrains Mono, monospace'; tg.fillText('DEMO_STATION1: 70 (input, frames) pairs, ' + total + ' frames', 0, 52);
    // current pair
    let acc = 0, k = 0; for (; k < rec.length; k++) { if (gf < acc + rec[k][1]) break; acc += rec[k][1]; }
    if (k < rec.length) lab.innerHTML = 'Pair ' + (k + 1) + ' of 70: <b class="val">' + hex2(rec[k][0]) + ', ' + rec[k][1] + '</b>  ' + nameOf(rec[k][0]) + ' for ' + rec[k][1] + ' frames (frame ' + (gf - acc) + ' of it).';
  }
  const player = makePlayer(body, 'demo', { onframe: f => { gframe = meta && meta.gf ? meta.gf[f] : 0; drawTrack(Math.max(0, Math.min(total - 1, gframe))); } });
  track.addEventListener('click', e => { const r = track.getBoundingClientRect(); const gf = (e.clientX - r.left) / r.width * total; if (player && meta && meta.gf) { let k = meta.gf.findIndex(v => v >= gf); if (k < 0) k = meta.gf.length - 1; player.seek(k); } });
  const legend = el('div', { class: 'note', html: '<span style="color:#6fd3a9">■</span> right <span style="color:#86a6ff">■</span> left <span style="color:#e0c35a">■</span> up <span style="color:#c08bff">■</span> down <span style="color:#f0905a">■</span> button <span style="color:#8790a3">■</span> diagonal <span style="color:#2b3242">■</span> nothing' });
  body.append(track, lab, legend);
  drawTrack(0);
};

FIG.screens = body => {
  const row = el('div', { class: 'row' });
  for (const [k, c] of [['prep', 'Prepare for station'], ['go_06', 'Game Over'], ['go_name', 'Name entry']]) {
    if (!D.shots[k]) continue;
    const im = el('img', { class: 'pix', src: D.shots[k], alt: c }); im.style.width = '336px';
    row.append(el('div', { class: 'sprite-tile' }, im, el('div', { class: 'cap', text: c })));
  }
  body.append(row);
};

// mount
document.querySelectorAll('figure.fig').forEach(f => {
  const fn = FIG[f.dataset.fig]; const b = f.querySelector('.figbody');
  if (!fn) { b.append(el('div', { class: 'note', text: '(figure ' + f.dataset.fig + ')' })); return; }
  try { fn(b); } catch (e) { b.append(el('div', { class: 'note', text: 'This figure could not be drawn: ' + e.message })); console.error(e); }
});

// ------------------------------------------------------------------ contents: highlight current chapter
(function () {
  const links = [...document.querySelectorAll('.toc a')];
  const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
  const heads = [...document.querySelectorAll('.chapter > h1, .chapter > h2')].map(h => h.id ? h : h.parentElement).filter(h => h.id);
  const chapters = [...document.querySelectorAll('section.chapter[id]')];
  const io = new IntersectionObserver(es => {
    for (const e of es) if (e.isIntersecting) {
      const id = e.target.id; const a = map.get(id); if (!a) continue;
      links.forEach(l => l.classList.remove('cur')); a.classList.add('cur');
      const li = a.closest('.toc1 > li'); document.querySelectorAll('.toc1 > li').forEach(x => x.classList.toggle('on', x === li));
    }
  }, { rootMargin: '0px 0px -75% 0px' });
  document.querySelectorAll('.chapter h2[id], section.chapter[id]').forEach(h => io.observe(h));
  if (window.innerWidth < 960) { const d = document.getElementById('tocdetails'); if (d) d.open = false; }
})();

// ------------------------------------------------------------------ listing
(function () {
  const body = document.getElementById('listing-body'), st = document.getElementById('lstat');
  const dl = document.getElementById('lsyms'); D.labels.forEach(n => dl.append(el('option', { value: n })));
  let loaded = null;
  const escH = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  function hl(line) {
    let cm = ''; const i = line.indexOf(';');
    if (i >= 0) { cm = '<span class="cm">' + escH(line.slice(i)) + '</span>'; line = line.slice(0, i); }
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*)(:)(.*)$/);
    let lab = '';
    if (m) { lab = '<span class="lb" id="L-' + m[1] + '">' + m[1] + ':</span>'; line = m[3]; }
    else { const e = line.match(/^([A-Za-z_][A-Za-z0-9_]*)(\s+=.*)$/); if (e) { lab = '<span class="lb" id="L-' + e[1] + '">' + e[1] + '</span>'; line = e[2]; } }
    const mm = line.match(/^(\s*)(\.?[a-zA-Z]{2,5})(\b.*)$/);
    if (mm) line = escH(mm[1]) + '<span class="mn">' + escH(mm[2]) + '</span>' + escH(mm[3]).replace(/(#?\$[0-9A-Fa-f]+)/g, '<span class="nm">$1</span>');
    else line = escH(line);
    return lab + line + cm;
  }
  function load() {
    if (loaded) return loaded;
    st.textContent = 'Loading…';
    loaded = fetch('data/miner2049er.txt').then(r => r.text()).then(t => {
      body.innerHTML = t.split('\n').map(hl).join('\n'); body.hidden = false; st.textContent = t.split('\n').length + ' lines';
      document.getElementById('lload').textContent = 'Listing shown';
    }).catch(() => { st.textContent = 'The listing could not be loaded.'; loaded = null; });
    return loaded;
  }
  function go(name) {
    load().then(() => { const t = document.getElementById('L-' + name); if (!t) { st.textContent = 'No label ' + name; return; } t.scrollIntoView({ block: 'center' }); t.classList.add('flash'); setTimeout(() => t.classList.remove('flash'), 2500); });
  }
  document.getElementById('lload').addEventListener('click', load);
  document.getElementById('lgo').addEventListener('click', () => go(document.getElementById('lsearch').value.trim().toUpperCase()));
  document.getElementById('lsearch').addEventListener('keydown', e => { if (e.key === 'Enter') go(e.target.value.trim().toUpperCase()); });
  document.addEventListener('click', e => { const a = e.target.closest('a.sym'); if (!a) return; e.preventDefault(); go(a.dataset.sym); });
})();
})();
