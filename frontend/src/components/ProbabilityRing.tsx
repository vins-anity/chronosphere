import React from 'react';

interface ProbabilityRingProps {
    probability: number; // 0-1
    label?: string;
    size?: number;
    strokeWidth?: number;
    teamColor?: 'radiant' | 'dire';
}

/**
 * Circular probability display with animated fill.
 * Uses SVG for smooth rendering.
 */
export const ProbabilityRing: React.FC<ProbabilityRingProps> = ({
    probability,
    label = 'Win Probability',
    size = 200,
    strokeWidth = 12,
    teamColor = 'radiant',
}) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = Math.min(1, Math.max(0, probability));
    const offset = circumference - progress * circumference;

    // Color based on team and value
    const getColor = () => {
        if (teamColor === 'radiant') {
            if (probability >= 0.6) return '#4ade80'; // Green - winning
            if (probability >= 0.4) return '#f59e0b'; // Amber - even
            return '#f87171'; // Red - losing
        } else {
            if (probability <= 0.4) return '#4ade80';
            if (probability <= 0.6) return '#f59e0b';
            return '#f87171';
        }
    };

    const color = getColor();
    const percentage = (probability * 100).toFixed(1);

    return (
        <div className="flex flex-col items-center gap-2">
            <svg
                width={size}
                height={size}
                className="transform -rotate-90"
                style={{ filter: `drop-shadow(0 0 12px ${color}40)` }}
            >
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="rgba(120, 113, 108, 0.2)"
                    strokeWidth={strokeWidth}
                />
                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    style={{ transition: 'stroke-dashoffset 0.5s ease-out, stroke 0.3s ease' }}
                />
                {/* Center text */}
                <text
                    x="50%"
                    y="50%"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className="font-mono"
                    style={{
                        transform: 'rotate(90deg)',
                        transformOrigin: 'center',
                        fontSize: size * 0.18,
                        fontWeight: 600,
                        fill: '#fafaf9',
                    }}
                >
                    {percentage}%
                </text>
            </svg>
            <span className="text-caption text-stone-400">{label}</span>
        </div>
    );
};

export default ProbabilityRing;
