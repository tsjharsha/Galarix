import React, { useEffect, useRef } from 'react';

const FINANCIAL_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ%$£€¥".split("");
const DATA_STRINGS = [
  "TXN_APPROVED", "RISK_0.02", "AUTH_REQ", "SWIFT_PAY",
  "IBAN_VAL", "KYC_PASS", "LIM_EXC", "FRAUD_0"
];

function DataStreamMatrix() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas to full screen
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Matrix logic
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = [];
    const charType = []; // 0 for single char, 1 for string

    for (let x = 0; x < columns; x++) {
      drops[x] = 1;
      charType[x] = Math.random() > 0.8 ? 1 : 0;
    }

    const draw = () => {
      // Translucent black to create fading trail effect
      ctx.fillStyle = 'rgba(15, 23, 42, 0.15)'; // Slate-900 with alpha
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Tech cyan/brand color for the text
      ctx.fillStyle = '#0ea5e9'; // Tailwind sky-500
      ctx.font = `${fontSize}px "JetBrains Mono", monospace`;
      
      // Make text glow slightly
      ctx.shadowBlur = 5;
      ctx.shadowColor = '#38bdf8';

      for (let i = 0; i < drops.length; i++) {
        let text = "";
        if (charType[i] === 1) {
          text = DATA_STRINGS[Math.floor(Math.random() * DATA_STRINGS.length)];
        } else {
          text = FINANCIAL_CHARS[Math.floor(Math.random() * FINANCIAL_CHARS.length)];
        }

        const x = i * fontSize;
        const y = drops[i] * fontSize;

        ctx.fillText(text, x, y);

        // Reset drop randomly if it hits bottom
        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
          charType[i] = Math.random() > 0.8 ? 1 : 0;
        }

        // Move drop down
        drops[i]++;
      }
    };

    const intervalId = setInterval(draw, 33); // ~30fps

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none opacity-40 mix-blend-screen transition-opacity duration-1000 ease-in-out">
      <canvas ref={canvasRef} className="absolute inset-0" />
      {/* Heavy vignette to blend the edges */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-slate-900/50 to-slate-900"></div>
    </div>
  );
}

export default DataStreamMatrix;
