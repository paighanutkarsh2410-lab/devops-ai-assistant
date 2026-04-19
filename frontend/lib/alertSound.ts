/**
 * Browser-based alert sounds using Web Audio API.
 * No external sound files needed — generates tones programmatically.
 */

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioCtx;
}

function playTone(frequency: number, duration: number, type: OscillatorType = 'sine', volume: number = 0.3) {
  const ctx = getAudioContext();
  if (!ctx) return;

  // Resume context if suspended (browser autoplay policy)
  if (ctx.state === 'suspended') ctx.resume();

  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = type;
  osc.frequency.setValueAtTime(frequency, ctx.currentTime);

  // Fade in and out to avoid clicks
  gain.gain.setValueAtTime(0, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.05);
  gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration);

  osc.connect(gain);
  gain.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + duration);
}

/** Critical alarm — urgent two-tone siren, repeats 3 times */
export function playCriticalAlarm() {
  const ctx = getAudioContext();
  if (!ctx) return;
  if (ctx.state === 'suspended') ctx.resume();

  for (let i = 0; i < 3; i++) {
    const offset = i * 0.6;
    setTimeout(() => {
      playTone(880, 0.25, 'square', 0.2);  // High A
      setTimeout(() => playTone(660, 0.25, 'square', 0.2), 250);  // Lower E
    }, offset * 1000);
  }
}

/** High severity alert — two short beeps */
export function playHighAlert() {
  playTone(740, 0.15, 'sine', 0.25);
  setTimeout(() => playTone(740, 0.15, 'sine', 0.25), 200);
}

/** Medium severity — single soft chime */
export function playMediumAlert() {
  playTone(520, 0.3, 'sine', 0.15);
}

/** Play alert based on severity level */
export function playAlertForSeverity(severity: string) {
  switch (severity) {
    case 'critical':
      playCriticalAlarm();
      break;
    case 'high':
      playHighAlert();
      break;
    case 'medium':
      playMediumAlert();
      break;
    // 'low' — no sound
  }
}
