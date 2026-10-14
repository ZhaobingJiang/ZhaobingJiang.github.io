'use strict';
/* Static (browser-side) edition of the 2-D Stokes surrogate demo.
 *
 * The Python reference service (FastBEM_StokesDL/web_app.py) is mirrored 1:1:
 *   pre-processing  geometry mask + wall-distance channel        (data.py, bem_runner.py)
 *   inference       field U-Net + 5-seed force ensemble          (ONNX Runtime Web / WASM)
 *   rendering       viridis speed map + quiver arrows + obstacles (matplotlib look-alike)
 *
 * Nothing leaves the browser: both ONNX graphs are fetched once from ./models and
 * evaluated locally with the single-threaded SIMD WASM backend.
 */

const NX = 112, NY = 28, LX = 4.0, H = 1.0;
const SIZE_MIN = 0.02, SIZE_MAX = 0.30, MARGIN = 0.015;
const TRAIN_SLOTS = 3;
const QUIVER_STEP = 6;          // matplotlib quiver [::6]
const VMIN = 0.0, VMAX = 1.5;   // |u| color range, same as the reference renderer

const $ = (id) => document.getElementById(id);

let META = null;
let XS = [], YS = [], WDF = null, CMAP = null;
let sessU = null, sessF = null;
let ready = false, busy = false, debTimer = 0;
let shapes = [];
let lastResult = null;          // {u, v, mask, entries, ms} of the latest prediction

/* ------------------------------------------------------------------ boot */
/* First load ships ~12 MB (10.5 MB ORT-WASM runtime + 1.6 MB models). GitHub
 * Pages serves it at tens of KB/s with only a 10-min cache, so whenever
 * jsDelivr is reachable both parts come from the CDN (immutable 1-yr cache for
 * the npm-hosted runtime, 7-d cache for the repo-hosted models) and the
 * in-repo lib/ + models/ copies act as the offline fallback. */
const ORT_CDN = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17.1/dist/';
const MOD_CDN = 'https://cdn.jsdelivr.net/gh/ZhaobingJiang/ZhaobingJiang.github.io@main/' +
                'softwares/stokes/models/';

async function cdnReachable(url, timeoutMs) {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), timeoutMs);
    const r = await fetch(url, { method: 'HEAD', signal: ctl.signal, cache: 'no-store' });
    clearTimeout(t);
    return r.ok;
  } catch (e) { return false; }
}

(async function boot() {
  try {
    const [ortOk, modOk] = await Promise.all([
      cdnReachable(ORT_CDN + 'ort-wasm-simd.wasm', 8000),
      /* the gh CDN may need a few seconds to pull the file from GitHub on a
       * cold edge node, so give it a longer budget than the npm one */
      cdnReachable(MOD_CDN + 'meta.json', 12000),
    ]);
    const MBASE = modOk ? MOD_CDN : 'models/';

    META = await (await fetch(MBASE + 'meta.json')).json();
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
      ort.InferenceSession.create(MBASE + 'unet.onnx', so),
      ort.InferenceSession.create(MBASE + 'force.onnx', so),
    ]);

    ready = true;
    renderBadges();
    $('veil').classList.add('hide');
    $('btnPredict').disabled = false;

    shapes = [{ kind: 'circle', x: 2.0, y: 0.5, a: 0.10, b: 0.10 }];
    renderShapes();
    await predict();
  } catch (e) {
    $('veil').textContent = '模型加载失败：' + e.message;
  }
})();

/* ------------------------------------------------- pre-processing (data.py) */
function shapesMask() {
  const mk = new Float32Array(NY * NX);
  for (let i = 0; i < NY; i++) {
    const y = YS[i];
    for (let j = 0; j < NX; j++) {
      const x = XS[j];
      let m = 1.0;
      for (const s of shapes) {
        const dx = (x - s.x) / s.a, dy = (y - s.y) / s.b;
        if (dx * dx + dy * dy <= 1.0) { m = 0.0; break; }
      }
      mk[i * NX + j] = m;
    }
  }
  return mk;
}

function forceFeatures() {
  const c = new Float32Array(14);
  const order = shapes.map((s, k) => k).sort((a, b) => shapes[a].x - shapes[b].x);
  for (let i = 0; i < Math.min(TRAIN_SLOTS, order.length); i++) {
    const s = shapes[order[i]];
    c[4 * i] = s.x; c[4 * i + 1] = s.y; c[4 * i + 2] = s.a; c[4 * i + 3] = s.b;
  }
  c[12] = shapes.length;
  c[13] = shapes.reduce((t, s) => t + Math.PI * s.a * s.b, 0);
  return c;
}

/* -------------------------------------------------------------- inference */
async function predict() {
  if (!ready || busy) return;
  busy = true;
  $('btnPredict').disabled = true;
  try {
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
    const order = shapes.map((s, k) => k).sort((a, b) => shapes[a].x - shapes[b].x);
    const entries = [];
    for (let i = 0; i < Math.min(TRAIN_SLOTS, order.length); i++)
      entries.push({ idx: order[i], fx: f6[2 * i], fy: f6[2 * i + 1] });

    lastResult = { u, v, mask, entries, ms };
    drawField(u, v, mask);
    renderForceTable(entries);
    $('tInf').textContent = ms.toFixed(1) + ' ms';
    $('distWarn').style.display = inDistribution() ? 'none' : 'inline';
  } catch (e) {
    $('tInf').textContent = '预测失败：' + e.message;
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
function drawField(u, v, mask) {
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
  for (const s of shapes) {
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

function renderForceTable(entries) {
  const tb = $('forceBody');
  tb.innerHTML = '';
  if (!shapes.length) {
    $('forceTab').style.display = 'none';
    return;
  }
  let sumFx = 0, sumFy = 0;
  entries.forEach((en) => {
    const s = shapes[en.idx];
    const name = s.kind === 'circle'
      ? `圆 r = ${s.a.toFixed(3)}`
      : `椭圆 a = ${s.a.toFixed(3)}, b = ${s.b.toFixed(3)}`;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>#${en.idx + 1} · ${name}</td>` +
      `<td>${en.fx.toFixed(3)}</td><td>${en.fy.toFixed(3)}</td>`;
    tb.appendChild(tr);
    sumFx += en.fx; sumFy += en.fy;
  });
  const tr = document.createElement('tr');
  tr.className = 'sumrow';
  tr.innerHTML = `<td>合力（${entries.length} 个障碍物）</td>` +
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

/* ----------------------------------------------------------------- UI */
function clampShape(s) {
  s.a = Math.min(SIZE_MAX, Math.max(SIZE_MIN, s.a));
  if (s.kind === 'circle') s.b = s.a;
  else s.b = Math.min(SIZE_MAX, Math.max(SIZE_MIN, s.b));
  s.x = Math.min(LX - s.a - MARGIN, Math.max(s.a + MARGIN, s.x));
  s.y = Math.min(H - s.b - MARGIN, Math.max(s.b + MARGIN, s.y));
}

function inDistribution() {
  if (shapes.length < 1 || shapes.length > TRAIN_SLOTS) return false;
  const eps = 1e-9;
  for (const s of shapes) {
    if (s.kind === 'circle') {
      if (s.a < 0.05 - eps || s.a > 0.13 + eps) return false;
    } else if (s.a < 0.06 - eps || s.a > 0.13 + eps || s.b < 0.05 - eps || s.b > 0.11 + eps) {
      return false;
    }
    if (s.x < 0.4 || s.x > 3.6 || s.y < 0.05 || s.y > 0.95) return false;
  }
  return true;
}

function makeSlider(card, idx, labelTxt, min, max, step, get, set) {
  const row = document.createElement('div');
  row.className = 'srow';
  const lab = document.createElement('label');
  lab.textContent = labelTxt;
  const rng = document.createElement('input');
  rng.type = 'range'; rng.min = min; rng.max = max; rng.step = step;
  rng.value = get();
  const val = document.createElement('span');
  val.className = 'v';
  val.textContent = get().toFixed(3);
  rng.addEventListener('input', () => {
    set(parseFloat(rng.value));
    clampShape(shapes[idx]);
    rng.value = get();                        // snap back when clamped at the boundary
    val.textContent = get().toFixed(3);
    schedulePredict();
  });
  rng.addEventListener('change', () => {          // slider released: re-sync all cards
    renderShapes();
    schedulePredict(0);
  });
  row.appendChild(lab); row.appendChild(rng); row.appendChild(val);
  card.appendChild(row);
  return { rng, val };
}

function renderShapes() {
  const list = $('shapeList');
  list.innerHTML = '';
  shapes.forEach((s, i) => {
    const card = document.createElement('div');
    card.className = 'shape-card';
    const head = document.createElement('div');
    head.className = 'sc-head';
    head.innerHTML = `<span class="sc-idx">${i + 1}</span>` +
      `<span class="sc-kind">${s.kind === 'circle' ? '圆 Circle' : '椭圆 Ellipse'}</span>`;
    const del = document.createElement('button');
    del.className = 'sc-del'; del.textContent = '✕'; del.title = '删除该障碍物';
    del.addEventListener('click', () => {
      shapes.splice(i, 1);
      renderShapes(); schedulePredict(0);
    });
    head.appendChild(del);
    card.appendChild(head);

    makeSlider(card, i, 'x', 0, LX, 0.005, () => shapes[i].x, (v) => { shapes[i].x = v; });
    makeSlider(card, i, 'y', 0, H, 0.005, () => shapes[i].y, (v) => { shapes[i].y = v; });
    if (s.kind === 'circle') {
      makeSlider(card, i, '半径 r', SIZE_MIN, SIZE_MAX, 0.005,
        () => shapes[i].a, (v) => { shapes[i].a = v; shapes[i].b = v; });
    } else {
      makeSlider(card, i, '半轴 a', SIZE_MIN, SIZE_MAX, 0.005, () => shapes[i].a, (v) => { shapes[i].a = v; });
      makeSlider(card, i, '半轴 b', SIZE_MIN, SIZE_MAX, 0.005, () => shapes[i].b, (v) => { shapes[i].b = v; });
    }
    list.appendChild(card);
  });
}

function addShape(kind) {
  const s = { kind: kind, x: 2.0, y: 0.5, a: 0.08, b: 0.08 };
  if (kind === 'ellipse') { s.a = 0.10; s.b = 0.06; }
  clampShape(s);
  shapes.push(s);
  renderShapes(); schedulePredict(0);
}

function randomize() {
  const n = 1 + Math.floor(Math.random() * TRAIN_SLOTS), out = [];
  for (let t = 0; t < n; t++) {
    const kind = Math.random() < 0.7 ? 'circle' : 'ellipse';
    const s = { kind: kind, x: 0, y: 0, a: 0, b: 0 };
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
  if (!out.length) return;
  shapes = out;
  renderShapes(); schedulePredict(0);
}

/* -------------------------------------------------------------- wiring */
$('btnPredict').addEventListener('click', () => predict());
$('btnCircle').addEventListener('click', () => addShape('circle'));
$('btnEllipse').addEventListener('click', () => addShape('ellipse'));
$('btnRandom').addEventListener('click', randomize);
$('btnClear').addEventListener('click', () => { shapes = []; renderShapes(); schedulePredict(0); });

/* test hook for the automated screenshot/consistency checks */
window.__demo = {
  predict: predict,
  randomize: randomize,
  getShapes: () => shapes,
  setShapes: (s) => { shapes = s; renderShapes(); schedulePredict(0); },
  last: () => lastResult,
  features: forceFeatures,
  mask: shapesMask,
  ready: () => ready,
};
