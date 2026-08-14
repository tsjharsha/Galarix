class AudioKinetics {
  constructor() {
    this.ctx = null;
    this.oscillator = null;
    this.gainNode = null;
    this.initialized = false;
  }

  init() {
    if (this.initialized) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
      this.initialized = true;
    } catch (e) {
      console.warn("Web Audio API not supported", e);
    }
  }

  // A deep, vibrating ambient hum that signifies the AI tensor engine is running
  startEngineHum() {
    this.init();
    if (!this.ctx) return;
    
    // Resume context if suspended (browser autoplay policies)
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }

    if (this.oscillator) {
      this.stopEngineHum();
    }

    this.oscillator = this.ctx.createOscillator();
    this.gainNode = this.ctx.createGain();

    // Use a low sine wave mixed with triangle for a techy "purr"
    this.oscillator.type = 'triangle';
    this.oscillator.frequency.setValueAtTime(40, this.ctx.currentTime); // 40Hz is very low bass
    
    // Slight modulation to make it sound "computational"
    this.oscillator.frequency.linearRampToValueAtTime(45, this.ctx.currentTime + 0.5);
    this.oscillator.frequency.linearRampToValueAtTime(40, this.ctx.currentTime + 1.0);

    // Fade in
    this.gainNode.gain.setValueAtTime(0, this.ctx.currentTime);
    this.gainNode.gain.linearRampToValueAtTime(0.15, this.ctx.currentTime + 0.5);

    this.oscillator.connect(this.gainNode);
    this.gainNode.connect(this.ctx.destination);
    
    this.oscillator.start();
  }

  stopEngineHum() {
    if (this.oscillator && this.gainNode) {
      // Fade out smoothly
      this.gainNode.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5);
      this.oscillator.stop(this.ctx.currentTime + 0.5);
      this.oscillator = null;
      this.gainNode = null;
    }
  }

  // A harsh, low-frequency thud/zap for a firewall rejection
  playLockdownThud() {
    this.init();
    if (!this.ctx) return;

    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(150, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(20, this.ctx.currentTime + 0.3); // Pitch drop

    gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.3); // Quick fade

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + 0.3);
  }
}

export const audioKinetics = new AudioKinetics();
