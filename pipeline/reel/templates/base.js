// Shared helpers for every Reel template. A template defines:
//   window.DURATION, window.SHOTS (layer ids + start times), window.applySpec(sp), window.render(t)
// and pushes its sound cues with cue(type, time, gain) so sfx.py can follow the picture.
const $ = id => document.getElementById(id);
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), prog = (t, a, b) => clamp((t - a) / (b - a));
const eo = x => 1 - Math.pow(1 - x, 3), eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const back = x => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
window.SFX = []; const cue = (type, t, gain = 1) => window.SFX.push([type, +t.toFixed(3), gain]);
window.CLIP_FPS = 30; window.CLIP_FRAMES = 0;

function slam(el, t, a, d = 0.28) {   // big type punches in
  if (t < a) { el.style.opacity = 0; return; }
  const p = prog(t, a, a + d); el.style.opacity = clamp(p * 4);
  const s = 1.7 - 0.7 * back(p), sh = (1 - p) * 14 * Math.sin(t * 90);
  el.style.transform = `translate(${sh}px,0) scale(${s})`;
}
function rise(el, t, a, d = 0.35, dist = 90) { if (t < a) { el.style.opacity = 0; return; } const p = eo(prog(t, a, a + d)); el.style.opacity = p; el.style.transform = `translateY(${(1 - p) * dist}px)`; }
function out(el, t, a, d = 0.18) { if (t < a) return; const p = eo(prog(t, a, a + d)); el.style.opacity = 1 - p; el.style.transform = `translateY(${-160 * p}px)`; }
function pop(el, t, a, d = 0.35) { if (t < a) { el.style.opacity = 0; return; } const p = prog(t, a, a + d); el.style.opacity = clamp(p * 3); el.style.transform = `scale(${0.5 + 0.5 * back(p)})`; }
const textW = el => { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect().width; };
function fit(id, max) { const el = $(id); let f = parseFloat(el.style.fontSize) || parseFloat(getComputedStyle(el).fontSize); el.style.transform = 'none'; while (textW(el) > max && f > 50) { f -= 4; el.style.fontSize = f + 'px'; } }
const set = (id, v) => { if (v !== undefined && v !== null) $(id).textContent = v; };

async function showClip(t, start, img, zoomIn = true) {   // AI scene clip, frame-accurate
  const ct = Math.max(0, t - start); const fi = Math.min(window.CLIP_FRAMES - 1, Math.floor(ct * window.CLIP_FPS));
  if (window.CLIP_FRAMES < 1) return;
  const src = 'clipframes/' + String(fi + 1).padStart(4, '0') + '.png';
  if (img.getAttribute('src') !== src) { img.src = src; await img.decode().catch(() => {}); }
  if (zoomIn) img.style.transform = `scale(${1.12 - 0.12 * eo(prog(t, start, start + 0.6))})`;
}
function layers(t) {   // show the active shot, flash white on each cut
  const S = window.SHOTS; let idx = 0; S.forEach((s, i) => { if (t >= s[1]) idx = i; });
  S.forEach((s, i) => $(s[0]).style.visibility = i === idx ? 'visible' : 'hidden');
  const cuts = S.map(s => s[1]).filter(x => x > 0 && x <= t); const last = cuts.pop();
  $('flash').style.opacity = last !== undefined ? 0.55 * clamp(1 - (t - last) / 0.12) : 0;
  return S[idx][0];
}
function endCard(t, a, B) {   // shared end card: logo + line + pulsing CTA + badges + legal
  pop($('e_logo'), t, a + 0.02); pop($('e_sub'), t, a + B, 0.3); pop($('e_pill'), t, a + 2 * B, 0.35);
  pop($('e_badges'), t, a + 3 * B, 0.3); pop($('e_legal'), t, a + 3 * B, 0.3);
  if (t > a + 2 * B + 0.4) { const k = 1 + 0.05 * Math.max(0, Math.cos(((t - a) / B) * Math.PI * 2)); $('e_pill').style.transform = `scale(${k})`; }
}
function endCues(a, B) { cue('whoosh', a - 0.22, 0.8); cue('ding', a + 0.04, 0.8); cue('pop', a + B, 0.6); cue('pop', a + 2 * B, 0.9); cue('pop', a + 3 * B, 0.5); }
const END_HTML = `<div class="layer" id="END">
  <div class="endwrap" style="top:300px"><img id="e_logo" src="logo.png" style="width:320px;height:320px" alt=""></div>
  <div class="endwrap" style="top:700px"><div id="e_sub" style="font-weight:800;font-size:84px">אתם בבית. הרכב עובר</div></div>
  <div class="endwrap" style="top:920px"><div class="pill" id="e_pill">הורידו את עבר</div></div>
  <div class="endwrap" style="top:1120px"><div class="badges" id="e_badges"><img src="badge-googleplay.png" alt=""><img src="badge-appstore.png" alt=""></div></div>
  <div class="endwrap" style="top:1290px"><div class="legal" id="e_legal">*השירות זמין ברחובות והסביבה בלבד. בכפוף לתנאי השירות.</div></div>
</div><img class="logo" id="logo" src="logo.png" alt=""><div id="flash"></div>`;
document.addEventListener('DOMContentLoaded', () => document.body.insertAdjacentHTML('beforeend', END_HTML));
window.seek = async t => { await window.render(t); return true; };
