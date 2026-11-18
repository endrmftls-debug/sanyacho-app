// Distress whistle: three loud blasts, a pause, repeat (international distress pattern).
let ctx = null;
let timer = null;

function blast(at, len) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = "square";
  o.frequency.value = 3150;
  g.gain.setValueAtTime(0, at);
  g.gain.linearRampToValueAtTime(0.9, at + 0.02);
  g.gain.setValueAtTime(0.9, at + len - 0.03);
  g.gain.linearRampToValueAtTime(0, at + len);
  o.connect(g).connect(ctx.destination);
  o.start(at);
  o.stop(at + len + 0.05);
}

function cycle() {
  const t = ctx.currentTime + 0.05;
  for (let i = 0; i < 3; i++) blast(t + i * 0.9, 0.6);
}

export function startWhistle() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
  ctx.resume();
  cycle();
  clearInterval(timer);
  timer = setInterval(cycle, 4200);
}

export function stopWhistle() {
  clearInterval(timer);
  timer = null;
  if (ctx) ctx.suspend();
}

export const whistleOn = () => timer !== null;
