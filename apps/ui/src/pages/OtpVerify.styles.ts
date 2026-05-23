export const OTP_VERIFY_CSS = `
  @keyframes ov-fade-up {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes ov-spin { to { transform: rotate(360deg); } }
  @keyframes ov-shake {
    0%,100% { transform: translateX(0); }
    15%     { transform: translateX(-7px); }
    30%     { transform: translateX(7px); }
    45%     { transform: translateX(-5px); }
    60%     { transform: translateX(5px); }
    75%     { transform: translateX(-2px); }
    90%     { transform: translateX(2px); }
  }
  @keyframes ov-pop {
    0%   { transform: scale(0.85); }
    55%  { transform: scale(1.08); }
    100% { transform: scale(1); }
  }
  .ov-page { min-height: 100vh; background: linear-gradient(145deg, #F0EEFF 0%, #EAE8FF 50%, #F2F0FF 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 1.5rem; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
  .ov-card { background: #fff; border-radius: 24px; box-shadow: 0 20px 60px rgba(107,101,168,0.12), 0 4px 16px rgba(0,0,0,0.05); padding: 2.75rem 2.25rem 2.25rem; width: 100%; max-width: 440px; animation: ov-fade-up 0.45s ease-out both; }
  .ov-otp-box { width: 54px; height: 64px; text-align: center; font-size: 1.625rem; font-weight: 800; border: 2px solid #E4E0F4; border-radius: 14px; outline: none; transition: border-color 0.15s, box-shadow 0.15s, background 0.15s, transform 0.1s; cursor: text; font-family: 'Inter', system-ui, monospace; background: #FAF8FF; color: #2D2A50; }
  .ov-otp-box:focus { border-color: #8880CC; box-shadow: 0 0 0 3px rgba(136,128,204,0.15); background: #fff; transform: scale(1.04); }
  .ov-otp-box.filled { border-color: #8880CC; background: #EDE9FF; color: #6560A8; animation: ov-pop 0.25s cubic-bezier(.34,1.56,.64,1) both; }
  .ov-otp-box.error { border-color: #D96070 !important; background: #FEF0F2 !important; color: #B84560 !important; }
  .ov-otp-row { display: flex; gap: 0.625rem; }
  .ov-otp-row.shake { animation: ov-shake 0.45s ease-out; }
  .ov-btn { width: 100%; padding: 0.9rem; font-size: 1rem; font-weight: 700; font-family: inherit; background: linear-gradient(135deg, #7068B8 0%, #9078C4 100%); color: #fff; border: none; border-radius: 10px; cursor: pointer; letter-spacing: 0.01em; transition: transform 0.18s, box-shadow 0.18s, opacity 0.18s; }
  .ov-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(112,104,184,0.32); }
  .ov-btn:active:not(:disabled) { transform: translateY(0); }
  .ov-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .ov-resend-btn { background: none; border: none; padding: 0; font-size: 0.875rem; font-weight: 600; color: #7068B8; cursor: pointer; font-family: inherit; transition: opacity 0.15s; }
  .ov-resend-btn:hover:not(:disabled) { opacity: 0.75; }
  .ov-resend-btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .ov-back-btn { background: none; border: none; padding: 0; font-size: 0.875rem; color: #A09CC4; cursor: pointer; font-family: inherit; transition: color 0.15s; }
  .ov-back-btn:hover { color: #7A788E; }
  .ov-step-dot { width: 8px; height: 8px; border-radius: 50%; transition: background 0.3s; }
  .ov-step-line { flex: 1; height: 2px; border-radius: 1px; }
`;

