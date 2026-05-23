export const ACCESS_DENIED_CSS = `
  @keyframes ad-fade-up {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes ad-shield-pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.25); }
    60%     { box-shadow: 0 0 0 18px rgba(239,68,68,0); }
  }
  @keyframes ad-float {
    0%,100% { transform: translateY(0); }
    50%     { transform: translateY(-8px); }
  }
  .ad-card {
    width: 100%;
    max-width: 500px;
    background: #fff;
    border-radius: 24px;
    border: 1px solid #FEE2E2;
    box-shadow: 0 24px 64px rgba(239,68,68,0.1), 0 4px 16px rgba(0,0,0,0.05);
    padding: 3rem 2.5rem;
    text-align: center;
    animation: ad-fade-up 0.5s ease-out both;
  }
  .ad-shield-wrap {
    width: 96px; height: 96px;
    margin: 0 auto 1.75rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #FEE2E2, #FECACA);
    border: 3px solid #FCA5A5;
    display: flex; align-items: center; justify-content: center;
    animation: ad-shield-pulse 2.5s ease-in-out infinite, ad-float 4s ease-in-out infinite;
  }
  .ad-btn-primary {
    flex: 1; padding: 0.875rem 1.25rem;
    font-size: 0.9375rem; font-weight: 600;
    background: linear-gradient(135deg, #EF4444, #DC2626);
    color: #fff; border: none; border-radius: 10px;
    cursor: pointer; transition: all 0.2s; font-family: inherit;
  }
  .ad-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(239,68,68,0.38);
  }
  .ad-btn-primary:active { transform: translateY(0); }
  .ad-btn-secondary {
    flex: 1; padding: 0.875rem 1.25rem;
    font-size: 0.9375rem; font-weight: 600;
    background: transparent; color: #6B7280;
    border: 1.5px solid #E5E7EB; border-radius: 10px;
    cursor: pointer; transition: all 0.2s; font-family: inherit;
  }
  .ad-btn-secondary:hover {
    border-color: #9CA3AF; color: #374151; background: #F9FAFB;
  }
`;

