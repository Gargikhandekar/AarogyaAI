export default function HeroIllustration() {
  return (
    <div className="relative w-full max-w-lg mx-auto">
      <svg viewBox="0 0 500 500" className="w-full h-auto animate-float" aria-hidden="true">
        <defs>
          <linearGradient id="heroGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#0EA5E9" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id="heroGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2563EB" />
            <stop offset="50%" stopColor="#0EA5E9" />
            <stop offset="100%" stopColor="#22C55E" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="8" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background circles */}
        <circle cx="250" cy="250" r="200" fill="url(#heroGrad1)" />
        <circle cx="250" cy="250" r="160" fill="none" stroke="#2563EB" strokeWidth="1" strokeOpacity="0.2" strokeDasharray="8 4" />

        {/* Medical cross */}
        <g transform="translate(250, 200)" filter="url(#glow)">
          <rect x="-15" y="-50" width="30" height="100" rx="8" fill="url(#heroGrad2)" />
          <rect x="-50" y="-15" width="100" height="30" rx="8" fill="url(#heroGrad2)" />
        </g>

        {/* Heartbeat line */}
        <polyline
          points="80,320 120,320 140,280 160,360 180,300 200,320 280,320 300,280 320,360 340,300 360,320 420,320"
          fill="none"
          stroke="url(#heroGrad2)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Chat bubbles */}
        <g transform="translate(120, 130)">
          <rect x="0" y="0" width="120" height="60" rx="16" fill="white" fillOpacity="0.9" />
          <rect x="15" y="18" width="70" height="8" rx="4" fill="#2563EB" fillOpacity="0.3" />
          <rect x="15" y="34" width="90" height="8" rx="4" fill="#2563EB" fillOpacity="0.2" />
        </g>

        <g transform="translate(260, 100)">
          <rect x="0" y="0" width="140" height="70" rx="16" fill="#2563EB" fillOpacity="0.15" />
          <rect x="15" y="18" width="80" height="8" rx="4" fill="#2563EB" fillOpacity="0.4" />
          <rect x="15" y="34" width="110" height="8" rx="4" fill="#2563EB" fillOpacity="0.3" />
          <rect x="15" y="50" width="60" height="8" rx="4" fill="#2563EB" fillOpacity="0.2" />
        </g>

        {/* Floating dots */}
        <circle cx="100" cy="180" r="6" fill="#22C55E" fillOpacity="0.6">
          <animate attributeName="cy" values="180;170;180" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="400" cy="200" r="8" fill="#0EA5E9" fillOpacity="0.5">
          <animate attributeName="cy" values="200;190;200" dur="4s" repeatCount="indefinite" />
        </circle>
        <circle cx="380" cy="380" r="5" fill="#2563EB" fillOpacity="0.4">
          <animate attributeName="cy" values="380;370;380" dur="3.5s" repeatCount="indefinite" />
        </circle>

        {/* AI brain icon */}
        <g transform="translate(250, 380)">
          <circle cx="0" cy="0" r="35" fill="url(#heroGrad2)" fillOpacity="0.2" />
          <text x="0" y="8" textAnchor="middle" fontSize="28" fill="#2563EB">🧠</text>
        </g>
      </svg>
    </div>
  );
}
