export const LOGIN_CSS = `
  @keyframes lr-blob {
    0%,100% { transform: translate(0,0) scale(1); }
    33%      { transform: translate(40px,-55px) scale(1.08); }
    66%      { transform: translate(-28px,32px) scale(0.93); }
  }
  @keyframes lr-fade-up {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes lr-spin { to { transform: rotate(360deg); } }
  @keyframes lr-icon-pop {
    0%   { transform: scale(0.7) rotate(-8deg); opacity: 0; }
    60%  { transform: scale(1.12) rotate(3deg); opacity: 1; }
    100% { transform: scale(1) rotate(0); opacity: 1; }
  }
  .lr-root { display: flex; min-height: 100vh; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
  .lr-left {
    width: 46%;
    background: linear-gradient(148deg, #ECE9FF 0%, #E4DEFF 45%, #EBE8FF 100%);
    position: relative; overflow: hidden;
    display: flex; flex-direction: column; padding: 2.5rem 3rem;
  }
  .lr-blob { position: absolute; border-radius: 50%; filter: blur(72px); pointer-events: none; }
  .lr-blob-1 { width: 380px; height: 380px; background: radial-gradient(circle, rgba(112,104,184,0.3), rgba(96,88,172,0.1)); top: -110px; right: -90px; animation: lr-blob 11s ease-in-out infinite; }
  .lr-blob-2 { width: 300px; height: 300px; background: radial-gradient(circle, rgba(148,128,218,0.22), rgba(120,100,204,0.07)); bottom: -90px; left: -60px; animation: lr-blob 14s ease-in-out infinite reverse; }
  .lr-blob-3 { width: 200px; height: 200px; background: radial-gradient(circle, rgba(180,168,236,0.18), transparent); top: 48%; left: 35%; animation: lr-blob 9s ease-in-out infinite; animation-delay: -4s; }
  .lr-left-content { position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; }
  .lr-brand-logo { width: 46px; height: 46px; border-radius: 13px; background: linear-gradient(135deg, #8880CC, #6E68B4); display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 20px rgba(110,104,180,0.35); animation: lr-icon-pop 0.6s cubic-bezier(.34,1.56,.64,1) both; }
  .lr-feature-icon { width: 42px; height: 42px; border-radius: 11px; background: rgba(107,101,168,0.1); border: 1px solid rgba(107,101,168,0.2); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .lr-right { flex: 1; display: flex; align-items: center; justify-content: center; background: #FFFEFF; padding: 2.5rem 3.5rem; }
  .lr-form-wrap { width: 100%; max-width: 400px; animation: lr-fade-up 0.5s ease-out 0.1s both; }
  .lr-phone-field { display: flex; align-items: stretch; border: 1.5px solid #E4E0F4; border-radius: 10px; background: #FAF8FF; transition: border-color 0.2s, box-shadow 0.2s, background 0.2s; min-height: 48px; overflow: visible; }
  .lr-phone-field:focus-within { border-color: #8880CC; box-shadow: 0 0 0 3px rgba(136,128,204,0.15); background: #fff; }
  .lr-phone-field.has-error { border-color: #D96070 !important; box-shadow: 0 0 0 3px rgba(217,96,112,0.1) !important; }
  .lr-phone-field .PhoneInput { display: contents; }
  .lr-phone-field .PhoneInputCountry { align-self: stretch; display: flex; align-items: stretch; flex-shrink: 0; }
  .lr-phone-field .PhoneInputInput { flex: 1; padding: 0 0.9rem; font-size: 0.9375rem; font-family: inherit; border: none; outline: none; background: transparent; color: #2D2A50; }
  .lr-phone-field .PhoneInputInput::placeholder { color: #B0ACCC; }
  .lr-phone-field .PhoneInputInput:disabled { opacity: 0.5; }
  .lr-btn { width: 100%; padding: 0.9rem; font-size: 1rem; font-weight: 700; font-family: inherit; background: linear-gradient(135deg, #7068B8 0%, #9078C4 100%); color: #fff; border: none; border-radius: 10px; cursor: pointer; letter-spacing: 0.01em; transition: transform 0.18s, box-shadow 0.18s; }
  .lr-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(112,104,184,0.32); }
  .lr-btn:active:not(:disabled) { transform: translateY(0); }
  .lr-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
  .lr-step-dot  { width: 8px; height: 8px; border-radius: 50%; }
  .lr-step-line { flex: 1; height: 2px; border-radius: 1px; }
  @media (max-width: 820px) {
    .lr-left  { display: none; }
    .lr-right { background: linear-gradient(145deg, #EDE9FF 0%, #F3F1FF 100%); min-height: 100vh; padding: 2rem 1.5rem; }
  }
`;

