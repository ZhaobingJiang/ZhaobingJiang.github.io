'use strict';
/* Static (browser-side) edition of the 2-D Stokes surrogate demo.
 *
 * The interface and behaviour mirror the local reference service
 * (FastBEM_StokesDL/web_app.py) 1:1: live geometry canvas, per-shape cards with
 * enable/delete + clamped sliders, overlap rejection, random scene from the
 * training distribution, held-out test-case picker and the same field / force
 * read-outs.  The two server-side features - the on-demand FastBEM re-solve and
 * the rolling retraining loop - are noted on the page as local-edition only.
 *
 * Pipeline (identical maths to data.py / bem_runner.py):
 *   pre-processing  geometry mask + wall-distance channel
 *   inference       field U-Net + 5-seed force ensemble  (ONNX Runtime Web / WASM)
 *   rendering       viridis speed map + quiver arrows + obstacles
 *
 * Nothing leaves the browser: the runtime comes from the jsDelivr npm mirror
 * (upstream copy as fallback) and both ONNX graphs race the jsDelivr repo mirror
 * against the in-repo copies, evaluated with the single-threaded SIMD backend.
 */

const NX = 112, NY = 28, LX = 4.0, H = 1.0;
const SIZE_MIN = 0.02, SIZE_MAX = 0.30, MARGIN = 0.015;
const TRAIN_SLOTS = 3, MAX_SHAPES = 16;
const MIN_R = 0.9;              // the same per-pair clearance factor the service enforces
const QUIVER_STEP = 6;          // matplotlib quiver [::6]
const VMIN = 0.0, VMAX = 1.5;   // |u| color range, same as the reference renderer

const $ = (id) => document.getElementById(id);

let META = null;
let XS = [], YS = [], WDF = null, CMAP = null;
let sessU = null, sessF = null;
let ready = false, busy = false, debTimer = 0;
let shapes = [{ on: true, kind: 'circle', x: 2.0, y: 0.5, a: 0.10, b: 0.10 }];
const CATALOG = {};
let lastResult = null;          // {u, v, mask, entries, ms} of the latest prediction

/* ------------------------------------------------------------------ boot */
/* First load ships ~12 MB (10.5 MB ORT-WASM runtime + 1.6 MB models). GitHub
 * Pages serves it at tens of KB/s with only a 10-min cache, so the runtime is
 * fetched from the jsDelivr npm mirror whenever it answers, and the models race
 * the jsDelivr repo mirror against the in-repo copies (see fetchRace). */
const ORT_CDN = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17.1/dist/';
/* Pin the repo CDN to a specific commit: a floating @main reference is
 * re-resolved on every push, which invalidates the jsDelivr edge cache and can
 * leave a cold node fetching from GitHub for a minute. Bump the hash whenever
 * the ONNX assets under models/ change. */
const MOD_CDN = 'https://cdn.jsdelivr.net/gh/ZhaobingJiang/ZhaobingJiang.github.io@b865b56/' +
                'softwares/stokes/models/';

function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = src; s.async = false;
    s.onload = () => res(src);
    s.onerror = () => rej(new Error('script load failed: ' + src));
    document.head.appendChild(s);
  });
}

/* ONNX Runtime itself: npm CDN first (immutable, ~0.5 s), upstream copy as the
 * fallback so the page still works when jsDelivr is unreachable. */
async function ensureORT() {
  if (window.ort) return;
  try { await loadScript(ORT_CDN + 'ort.min.js'); } catch (e) { /* fall back */ }
  if (!window.ort) await loadScript('lib/ort.min.js');
  if (!window.ort) throw new Error('ONNX Runtime 加载失败（CDN 与本地副本均不可用）');
}

async function cdnReachable(url, timeoutMs) {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), timeoutMs);
    const r = await fetch(url, { method: 'HEAD', signal: ctl.signal, cache: 'no-store' });
    clearTimeout(t);
    return r.ok;
  } catch (e) { return false; }
}

/* The models race the CDN against the in-repo copies: whichever source
 * delivers first wins and the loser is aborted. A warm jsDelivr edge answers
 * in ~1 s; a cold edge may take a minute (it pulls from GitHub first), in
 * which case the GitHub Pages copy simply wins instead - the CDN is an
 * accelerator, never a single point of failure. */
async function fetchRace(name) {
  const cA = new AbortController(), cL = new AbortController();
  const get = async (base, ac, other) => {
    const r = await fetch(base + name, { signal: ac.signal });
    if (!r.ok) throw new Error(base + ' -> HTTP ' + r.status);
    const buf = await r.arrayBuffer();
    other.abort();                          // this source won the race
    return buf;
  };
  return await Promise.any([
    get(MOD_CDN, cA, cL),
    get('models/', cL, cA),
  ]);
}

async function loadModel(name, so) {
  return await ort.InferenceSession.create(new Uint8Array(await fetchRace(name)), so);
}

(async function boot() {
  try {
    await ensureORT();
    const [ortOk, metaBuf] = await Promise.all([
      cdnReachable(ORT_CDN + 'ort-wasm-simd.wasm', 8000),
      fetchRace('meta.json'),
    ]);
    META = JSON.parse(new TextDecoder().decode(metaBuf));
    const m = META.model;
    XS = m.x; YS = m.y;
    WDF = new Float32Array(NY * NX);              // flatten the 28x112 wall-distance field
    for (let i = 0; i < NY; i++)
      for (let j = 0; j < NX; j++) WDF[i * NX + j] = m.wall_distance[i][j];
    CMAP = META.colormap.viridis256;

    ort.env.logLevel = 'error';
    ort.env.wasm.wasmPaths = ortOk ? ORT_CDN : new URL('lib/', location.href).href;
    ort.env.wasm.numThreads = 1;                  // no COOP/COEP on GitHub Pages
    const so = { executionProviders: ['wasm'], graphOptimizationLevel: 'all' };
    [sessU, sessF] = await Promise.all([
      loadModel('unet.onnx', so),
      loadModel('force.onnx', so),
    ]);

    ready = true;
    renderBadges();
    renderModelInfo();
    $('veil').classList.add('hide');
    $('btnPredict').disabled = false;

    renderShapes();                               // draws the geometry canvas too
    loadCases();                                  // held-out catalogue (small, local)
    await predict();
  } catch (e) {
    $('veil').textContent = '模型加载失败：' + e.message;
  }
})();

/* ------------------------------------------------- pre-processing (data.py) */
function activeShapes() {
  return shapes.filter((s) => s.on);
}

function shapesMask() {
  const act = activeShapes();
  const mk = new Float32Array(NY * NX);
  for (let i = 0; i < NY; i++) {
    const y = YS[i];
    for (let j = 0; j < NX; j++) {
      const x = XS[j];
      let m = 1.0;
      for (const s of act) {
        const dx = (x - s.x) / s.a, dy = (y - s.y) / s.b;
        if (dx * dx + dy * dy <= 1.0) { m = 0.0; break; }
      }
      mk[i * NX + j] = m;
    }
  }
  return mk;
}

function forceFeatures() {
  const act = activeShapes();
  const c = new Float32Array(14);
  const order = act.map((s, k) => k).sort((a, b) => act[a].x - act[b].x);
  for (let i = 0; i < Math.min(TRAIN_SLOTS, order.length); i++) {
    const s = act[order[i]];
    c[4 * i] = s.x; c[4 * i + 1] = s.y; c[4 * i + 2] = s.a; c[4 * i + 3] = s.b;
  }
  c[12] = act.length;
  c[13] = act.reduce((t, s) => t + Math.PI * s.a * s.b, 0);
  return c;
}

/* True iff the geometry lies inside the training family (same rule as web_app.py). */
function inDistribution() {
  const act = activeShapes();
  if (act.length < 1 || act.length > TRAIN_SLOTS) return false;
  const eps = 1e-9;
  for (const s of act) {
    if (s.kind === 'circle') {
      if (s.a < 0.05 - eps || s.a > 0.13 + eps) return false;
    } else if (s.a < 0.06 - eps || s.a > 0.13 + eps || s.b < 0.05 - eps || s.b > 0.11 + eps) {
      return false;
    }
    if (s.x < 0.4 || s.x > 3.6 || s.y < 0.05 || s.y > 0.95) return false;
  }
  return true;
}

/* -------------------------------------------------------------- inference */
async function predict() {
  if (!ready || busy) return;
  busy = true;
  $('btnPredict').disabled = true;
  $('tInf').textContent = '…';
  try {
    const act = activeShapes();
    const mask = shapesMask();
    const inp = new Float32Array(2 * NY * NX);
    inp.set(mask, 0);
    inp.set(WDF, NY * NX);

    const t0 = performance.now();
    const ru = await sessU.run({ input: new ort.Tensor('float32', inp, [1, 2, NY, NX]) });
    const rf = await sessF.run({ feat: new ort.Tensor('float32', forceFeatures(), [1, 14]) });
    const ms = performance.now() - t0;

    const uv = ru.uv.data, N = NY * NX;
    const u = new Float32Array(N), v = new Float32Array(N);
    for (let i = 0; i < N; i++) { u[i] = uv[i] * mask[i]; v[i] = uv[N + i] * mask[i]; }

    const f6 = rf.forces.data;                    // (x-sorted slots) x (fx, fy)
    const order = act.map((s, k) => k).sort((a, b) => act[a].x - act[b].x);
    const entries = [];
    for (let i = 0; i < Math.min(TRAIN_SLOTS, order.length); i++)
      entries.push({ idx: order[i], fx: f6[2 * i], fy: f6[2 * i + 1] });

    lastResult = { u, v, mask, entries, ms };
    drawField(act, u, v, mask);
    renderForceTable(act, entries);
    $('tInf').textContent = ms.toFixed(1) + ' ms';
    $('nf').textContent = act.length + ' 个';
    if (inDistribution()) hideWarn();
    else if (act.length > TRAIN_SLOTS) showWarn('当前有 ' + act.length + ' 个形状：训练集为 1–3 个圆 / 椭圆的组合，多出的形状不受力网络覆盖，流场结果为外推估计。');
    else showWarn('当前几何超出代理模型训练分布（训练集为 1–3 个圆 / 椭圆的随机组合，尺寸与位置有限定范围），代理结果为外推、误差可能偏大。');
  } catch (e) {
    $('tInf').textContent = '预测失败：' + e.message;
    showWarn('预测失败：' + e.message, true);
  } finally {
    busy = false;
    $('btnPredict').disabled = false;
  }
}

function schedulePredict(delay) {
  clearTimeout(debTimer);
  debTimer = setTimeout(predict, delay == null ? 180 : delay);
}

/* ------------------------------------------------------------- rendering */
function drawField(act, u, v, mask) {
  const cv = $('field'), ctx = cv.getContext('2d');
  const PX = 16, PY = 16, PW = 1120, PH = 280;        // plot rect (4:1)
  const CBX = PX + PW + 18, CBW = 18;                 // colorbar
  const sx = PW / LX, sy = PH / H;                    // px per unit (both 280)
  const toPxX = (x) => PX + x * sx;
  const toPxY = (y) => PY + (H - y) * sy;             // canvas y grows downwards

  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, cv.width, cv.height);

  /* speed field: block colours, bilinearly upscaled (112 x 28 -> plot rect) */
  const off = document.createElement('canvas');
  off.width = NX; off.height = NY;
  const oc = off.getContext('2d');
  const img = oc.createImageData(NX, NY);
  for (let i = 0; i < NY; i++) {
    for (let j = 0; j < NX; j++) {
      const k = i * NX + j, o = 4 * k;
      if (mask[k] < 0.5) { img.data[o] = img.data[o + 1] = img.data[o + 2] = 255; img.data[o + 3] = 255; continue; }
      const s = Math.hypot(u[k], v[k]);
      let t = (s - VMIN) / (VMAX - VMIN);
      t = t < 0 ? 0 : (t > 1 ? 1 : t);
      const c = CMAP[Math.round(t * 255)];
      img.data[o] = c[0]; img.data[o + 1] = c[1]; img.data[o + 2] = c[2]; img.data[o + 3] = 255;
    }
  }
  oc.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(off, 0, 0, NX, NY, PX, PY, PW, PH);

  /* quiver arrows (white, len = |u|/12 in data units, same as matplotlib scale=12) */
  ctx.strokeStyle = 'rgba(255,255,255,0.92)';
  ctx.fillStyle = 'rgba(255,255,255,0.92)';
  ctx.lineWidth = 1.2;
  for (let i = 0; i < NY; i += QUIVER_STEP) {
    for (let j = 0; j < NX; j += QUIVER_STEP) {
      const k = i * NX + j;
      if (mask[k] < 0.5) continue;
      const x0 = toPxX(XS[j]), y0 = toPxY(YS[i]);
      const dx = u[k] / 12 * sx, dy = -v[k] / 12 * sy;
      const len = Math.hypot(dx, dy);
      if (len < 2.5) continue;
      const x1 = x0 + dx, y1 = y0 + dy;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      const ang = Math.atan2(dy, dx);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x1 - 5 * Math.cos(ang - 0.42), y1 - 5 * Math.sin(ang - 0.42));
      ctx.lineTo(x1 - 5 * Math.cos(ang + 0.42), y1 - 5 * Math.sin(ang + 0.42));
      ctx.closePath(); ctx.fill();
    }
  }

  /* obstacles: black fill, thin white edge for crispness */
  for (const s of act) {
    ctx.beginPath();
    ctx.ellipse(toPxX(s.x), toPxY(s.y), s.a * sx, s.b * sy, 0, 0, 2 * Math.PI);
    ctx.fillStyle = '#000';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  /* channel frame */
  ctx.strokeStyle = '#c9d4dd';
  ctx.lineWidth = 1;
  ctx.strokeRect(PX - 0.5, PY - 0.5, PW + 1, PH + 1);

  /* colorbar */
  const bar = document.createElement('canvas');
  bar.width = 1; bar.height = 256;
  const bc = bar.getContext('2d');
  const bimg = bc.createImageData(1, 256);
  for (let k = 0; k < 256; k++) {
    const c = CMAP[255 - k];                       // top = max
    bimg.data[4 * k] = c[0]; bimg.data[4 * k + 1] = c[1]; bimg.data[4 * k + 2] = c[2]; bimg.data[4 * k + 3] = 255;
  }
  bc.putImageData(bimg, 0, 0);
  ctx.drawImage(bar, 0, 0, 1, 256, CBX, PY, CBW, PH);
  ctx.strokeStyle = '#c9d4dd';
  ctx.strokeRect(CBX - 0.5, PY - 0.5, CBW + 1, PH + 1);

  ctx.fillStyle = '#8a8a8a';
  ctx.font = '12px "Helvetica Neue", Arial, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('|u| (m/s)', CBX - 6, PY - 6);
  ctx.textAlign = 'right';
  ctx.fillText(VMAX.toFixed(1), CBX - 4, PY + 6);
  ctx.fillText(VMIN.toFixed(1), CBX - 4, PY + PH + 4 + 6);
}

function renderForceTable(act, entries) {
  const tb = $('forceBody');
  tb.innerHTML = '';
  if (!act.length) {
    $('forceTab').style.display = 'none';
    showWarn('空通道（无形状）：无受力可报。');
    return;
  }
  let sumFx = 0, sumFy = 0;
  entries.forEach((en) => {
    const s = act[en.idx];
    const name = s.kind === 'circle'
      ? `圆 r = ${s.a.toFixed(3)}`
      : `椭圆 a = ${s.a.toFixed(3)}, b = ${s.b.toFixed(3)}`;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>#${en.idx + 1} · ${name}</td>` +
      `<td>(${s.x.toFixed(2)}, ${s.y.toFixed(2)})</td>` +
      `<td>${en.fx.toFixed(3)}</td><td>${en.fy.toFixed(3)}</td>`;
    tb.appendChild(tr);
    sumFx += en.fx; sumFy += en.fy;
  });
  const tr = document.createElement('tr');
  tr.className = 'sumrow';
  tr.innerHTML = `<td colspan="2">合力（${entries.length} 个障碍物）</td>` +
    `<td>${sumFx.toFixed(3)}</td><td>${sumFy.toFixed(3)}</td>`;
  tb.appendChild(tr);
  $('forceTab').style.display = '';
}

function renderBadges() {
  const m = META.metrics;
  const fd = (100 * m.field_relL2_median).toFixed(2);
  const fg = m.force_total_drag_rel_median == null ? '—'
    : (100 * m.force_total_drag_rel_median).toFixed(2);
  $('badges').innerHTML =
    `<span class="badge">流场误差中位 <b>${fd}%</b>（留出测试集）</span>` +
    `<span class="badge">总阻力误差中位 <b>${fg}%</b></span>` +
    `<span class="badge">训练算例 <b>${m.store_train}</b> 组（FastBEM 计算）</span>` +
    `<span class="badge">第 <b>${m.round}</b> 轮滚动训练模型</span>`;
  $('mField').textContent = fd + '%';
  $('mDrag').textContent = fg + '%';
  $('nEns').textContent = m.force_n_models || 5;
}

/* Same four read-outs as the local edition's case-store panel, filled with the
 * published model's fixed metadata (retraining runs on the local service). */
function renderModelInfo() {
  const m = META.metrics;
  $('stTotal').textContent = `${m.store_train} 例（含留出基准 ${m.store_bench} 例）`;
  $('stRounds').textContent = `第 ${m.round} 轮（滚动训练）`;
  $('stTest').textContent = `${m.n_test} 例（不参与训练）`;
}

/* ------------------------------------------------------- geometry canvas */
/* Live 4:1 channel preview, same drawing as the local edition: walls,
 * parabolic-profile hints at inlet/outlet and every enabled obstacle. */
function drawGeometry() {
  const cv = $('geom'), ctx = cv.getContext('2d');
  const CW = cv.width, CVH = cv.height, pad = 16;   // CVH: avoid shadowing the global H
  const chH = CVH - 2 * pad, chW = chH * LX;        // channel drawn at true 4:1 aspect
  const x0 = (CW - chW) / 2, y0 = pad, x1 = x0 + chW, y1 = y0 + chH;
  ctx.clearRect(0, 0, CW, CVH);
  ctx.strokeStyle = '#4a5a78'; ctx.lineWidth = 2;
  ctx.strokeRect(x0, y0, chW, chH);                 // walls
  ctx.strokeStyle = '#3d8f6a'; ctx.lineWidth = 1.5; // parabolic-profile hint at both ends
  [x0 + 30, x1 - 30].forEach((px, end) => {
    for (let t = 0.25; t <= 0.751; t += 0.25) {
      const ay = y0 + chH * t, len = 12 + 12 * Math.sin(Math.PI * t);
      ctx.beginPath();
      if (end === 0) { ctx.moveTo(px - len, ay); ctx.lineTo(px, ay); }
      else { ctx.moveTo(px, ay); ctx.lineTo(px + len, ay); }
      ctx.stroke();
    }
  });
  shapes.forEach((s) => {
    if (!s.on) return;
    const px = x0 + (s.x / LX) * chW, py = y1 - (s.y / H) * chH,
          prx = (s.a / H) * chH, pry = (s.b / H) * chH;
    ctx.beginPath();
    if (s.kind === 'ellipse') ctx.ellipse(px, py, prx, pry, 0, 0, Math.PI * 2);
    else ctx.arc(px, py, prx, 0, Math.PI * 2);
    ctx.fillStyle = '#dfe7f2'; ctx.fill();
    ctx.strokeStyle = '#8fa7c9'; ctx.lineWidth = 1; ctx.stroke();
  });
  ctx.fillStyle = '#8296ad'; ctx.font = '12px "Microsoft YaHei",sans-serif';
  ctx.fillText('x=0', x0, y1 + 14); ctx.fillText('x=4 m', x1 - 38, y1 + 14);
}

/* ---------------------------------------------------------------------- UI */
function showWarn(t, isErr) {
  const w = $('warn');
  w.textContent = t;
  w.className = 'warn' + (isErr ? ' err' : '');
  w.style.display = 'block';
}

function hideWarn() {
  $('warn').style.display = 'none';
}

/* Every edit stays inside the channel (same clamping the service enforces). */
function clampShape(s) {
  s.a = Math.min(SIZE_MAX, Math.max(SIZE_MIN, s.a));
  if (s.kind === 'circle') s.b = s.a;
  else s.b = Math.min(SIZE_MAX, Math.max(SIZE_MIN, s.b));
  s.x = Math.min(LX - s.a - MARGIN, Math.max(s.a + MARGIN, s.x));
  s.y = Math.min(H - s.b - MARGIN, Math.max(s.b + MARGIN, s.y));
}

function overlapsAny(s, skip) {
  for (let j = 0; j < shapes.length; j++) {
    if (j === skip || !shapes[j].on) continue;
    const t = shapes[j];
    if (Math.hypot(s.x - t.x, s.y - t.y) < MIN_R * (Math.min(s.a, s.b) + Math.min(t.a, t.b)) + 1e-6)
      return true;
  }
  return false;
}

/* Slider drag must NOT rebuild the DOM (re-creating inputs interrupts the drag):
 * state, readouts and the geometry canvas update in place; the slider itself is
 * written back when a value was clamped or an overlapping edit was rejected. */
function setShape(i, k, v) {
  const s = shapes[i];
  if (!s) return;
  v = parseFloat(v);
  if (!isFinite(v)) return;
  const old = s[k];
  s[k] = v;
  clampShape(s);
  if (overlapsAny(s, i)) { s[k] = old; clampShape(s); }   // reject an edit that would overlap
  syncShapeUI(i);
  drawGeometry();
}

function toggleShape(i, on) {
  shapes[i].on = on;
  const card = $('shapeList').children[i];          // dim the card without rebuilding it
  if (card) card.classList.toggle('off', !on);
  drawGeometry();
  schedulePredict(0);
}

function delShape(i) {
  shapes.splice(i, 1);
  hideWarn();
  renderShapes();
  schedulePredict(0);
}

function addShape(kind) {
  if (activeShapes().length >= MAX_SHAPES) {
    showWarn('最多支持 ' + MAX_SHAPES + ' 个形状');
    return;
  }
  const s = { on: true, kind: kind, x: 0, y: 0,
              a: kind === 'circle' ? 0.08 : 0.12,
              b: kind === 'circle' ? 0.08 : 0.07 };
  let placed = false;
  for (let k = 0; k < 120 && !placed; k++) {
    s.x = +(s.a + MARGIN + Math.random() * (LX - 2 * s.a - 2 * MARGIN)).toFixed(3);
    s.y = +(s.b + MARGIN + Math.random() * (H - 2 * s.b - 2 * MARGIN)).toFixed(3);
    placed = !overlapsAny(s, -1);
  }
  if (!placed) {
    showWarn('通道内已无足够空间放置新形状，请先删除或缩小现有形状');
    return;
  }
  hideWarn();
  shapes.push(s);
  renderShapes();
  schedulePredict(0);
}

/* One card per shape: enable checkbox, type tag, delete button and the sliders
 * (x / y / radius or semi-axes) whose ranges follow the current size. */
function rowsHTML(i) {
  const s = shapes[i];
  const defs = [['x', 'x 位置'], ['y', 'y 位置']].concat(
    s.kind === 'circle' ? [['a', '半径 r']] : [['a', '半轴 a'], ['b', '半轴 b']]);
  return defs.map(([k, label]) => {
    let mn, mx;
    if (k === 'a' || k === 'b') { mn = SIZE_MIN; mx = SIZE_MAX; }
    else if (k === 'x') { mn = s.a + MARGIN; mx = LX - s.a - MARGIN; }
    else { mn = s.b + MARGIN; mx = H - s.b - MARGIN; }
    return `<div class="srow"><label>${label}</label>
      <input type="range" id="in-${i}-${k}" min="${mn.toFixed(4)}" max="${mx.toFixed(4)}" step="0.005"
             value="${s[k]}" oninput="setShape(${i},'${k}',this.value)"
             onchange="afterEdit()">
      <span class="v" id="val-${i}-${k}">${s[k].toFixed(3)}</span></div>`;
  }).join('');
}

function renderShapes() {
  const box = $('shapeList');
  box.innerHTML = '';
  shapes.forEach((s, i) => {
    const card = document.createElement('div');
    card.className = 'shape-card' + (s.on ? '' : ' off');
    card.innerHTML = `<div class="sc-head">
        <input type="checkbox" id="on-${i}" ${s.on ? 'checked' : ''}
               onchange="toggleShape(${i}, this.checked)">
        <span class="sc-kind">${s.kind === 'circle' ? '圆' : '椭圆'} ${i + 1}</span>
        <button class="sc-del" onclick="delShape(${i})" title="删除该障碍物">✕ 删除</button>
      </div>${rowsHTML(i)}`;
    box.appendChild(card);
  });
  drawGeometry();
  const n = activeShapes().length;
  $('nf').textContent = n + ' 个';
}

function syncShapeUI(i) {
  const s = shapes[i];
  if (!s) return;
  ['x', 'y', 'a', 'b'].forEach((k) => {
    const inp = $(`in-${i}-${k}`), val = $(`val-${i}-${k}`);
    if (inp && Math.abs(parseFloat(inp.value) - s[k]) > 1e-12) inp.value = s[k];
    if (val) val.textContent = s[k].toFixed(3);
  });
}

/* Slider released: rebuild the cards (refreshes the dynamic slider ranges) and
 * re-run the prediction in the background. */
function afterEdit() {
  renderShapes();
  schedulePredict(0);
}

/* Random scene drawn from the same distribution the training set uses
 * (1..3 circles/ellipses, 70/30, sizes and placement mirrored by the sampler). */
function randomize() {
  const n = 1 + Math.floor(Math.random() * TRAIN_SLOTS), out = [];
  for (let t = 0; t < n; t++) {
    const kind = Math.random() < 0.7 ? 'circle' : 'ellipse';
    const s = { on: true, kind: kind, x: 0, y: 0, a: 0, b: 0 };
    if (kind === 'circle') s.a = s.b = +(0.05 + Math.random() * 0.08).toFixed(4);
    else { s.a = +(0.06 + Math.random() * 0.07).toFixed(4); s.b = +(0.05 + Math.random() * 0.06).toFixed(4); }
    const rmax = Math.max(s.a, s.b);
    let placed = false;
    for (let k = 0; k < 300 && !placed; k++) {
      s.x = +(0.5 + s.a + Math.random() * (LX - 1 - 2 * s.a)).toFixed(4);
      s.y = +(s.b + 0.12 + Math.random() * (H - 2 * s.b - 0.24)).toFixed(4);
      placed = !out.some((o) => Math.hypot(s.x - o.x, s.y - o.y) < 1.35 * (rmax + Math.max(o.a, o.b)));
    }
    if (placed) out.push(s);
  }
  if (!out.length) { showWarn('随机放置失败，请重试'); return; }
  shapes = out;
  hideWarn();
  renderShapes();
  schedulePredict(0);
}

/* --------------------------------------------------- held-out test cases */
async function loadCases() {
  const sel = $('caseSel');
  try {
    const r = await fetch('cases.json');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    sel.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = ''; ph.textContent = '— 留出测试算例（' + j.length + ' 个）—';   // default: free geometry
    sel.appendChild(ph);
    j.forEach((c) => {
      CATALOG[c.name] = c;
      const o = document.createElement('option');
      o.value = c.name;
      o.textContent = `${c.name}（${c.cyls.length} 圆，M=${c.M}）`;
      sel.appendChild(o);
    });
  } catch (e) {
    sel.innerHTML = '<option value="">— 算例目录加载失败 —</option>';
  }
}

async function loadCase(name) {
  if (!name || busy) return;
  const c = CATALOG[name];
  if (!c) return;
  shapes = c.cyls.map((cy) => ({ on: true, kind: 'circle', x: +cy[0].toFixed(4),
                                 y: +cy[1].toFixed(4), a: +cy[2].toFixed(4), b: +cy[2].toFixed(4) }));
  shapes.forEach(clampShape);
  hideWarn();
  renderShapes();
  await predict();
}

/* -------------------------------------------------------------- wiring */
$('btnPredict').addEventListener('click', () => predict());
$('btnCircle').addEventListener('click', () => addShape('circle'));
$('btnEllipse').addEventListener('click', () => addShape('ellipse'));
$('btnRandom').addEventListener('click', randomize);
$('btnClear').addEventListener('click', () => { shapes = []; renderShapes(); schedulePredict(0); });
$('caseSel').addEventListener('change', function () { loadCase(this.value); });

/* test hook for the automated screenshot/consistency checks */
window.__demo = {
  predict: predict,
  randomize: randomize,
  addShape: addShape,
  toggleShape: toggleShape,
  delShape: delShape,
  loadCase: loadCase,
  getShapes: () => shapes,
  setShapes: (s) => { shapes = s; renderShapes(); schedulePredict(0); },
  last: () => lastResult,
  features: forceFeatures,
  mask: shapesMask,
  geomDataUrl: () => $('geom').toDataURL(),
  ready: () => ready,
};
