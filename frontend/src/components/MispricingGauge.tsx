import React from 'react';

interface MispricingGaugeProps {
    mispricing: number; // -1 to 1 (model prob - market prob)
    showLabels?: boolean;
}

/**
 * Horizontal gauge showing divergence between model and market.
 * Positive = Model thinks Radiant is undervalued
 * Negative = Model thinks Radiant is overvalued
 */
export const MispricingGauge: React.FC<MispricingGaugeProps> = ({
    mispricing,
    showLabels = true,
}) => {
    const clampedValue = Math.max(-1, Math.min(1, mispricing));
    const percentage = Math.abs(clampedValue * 50); // 0-50% of half-width
    const isPositive = clampedValue >= 0;

    // Significance thresholds
    const isSignificant = Math.abs(clampedValue) >= 0.1;
    const isHighlySignificant = Math.abs(clampedValue) >= 0.2;

    const getLabel = () => {
        if (Math.abs(clampedValue) < 0.05) return 'Fairly Priced';
        if (isPositive) {
            return isHighlySignificant ? 'Strong Buy Signal' : 'Undervalued';
        } else {
            return isHighlySignificant ? 'Strong Sell Signal' : 'Overvalued';
        }
    };

    return (
        <div className="w-full space-y-2">
            {showLabels && (
                <div className="flex justify-between text-xs text-stone-500">
                    <span>Overvalued</span>
                    <span className="font-medium text-stone-300">{getLabel()}</span>
                    <span>Undervalued</span>
                </div>
            )}

            {/* Gauge container */}
            <div className="relative w-full h-4 bg-stone-800/50 rounded-full overflow-hidden">
                {/* Center line */}
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-stone-600 transform -translate-x-1/2 z-10" />

                {/* Fill bar */}
                <div
                    className={`absolute top-0 bottom-0 transition-all duration-300 ${isPositive
                            ? 'left-1/2 bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-r-full'
                            : 'right-1/2 bg-gradient-to-l from-rose-500 to-rose-400 rounded-l-full'
                        }`}
                    style={{ width: `${percentage}%` }}
                />

                {/* Glow effect for significant values */}
                {isSignificant && (
                    <div
                        className={`absolute top-0 bottom-0 transition-all duration-300 blur-sm ${isPositive
                                ? 'left-1/2 bg-emerald-500/50 rounded-r-full'
                                : 'right-1/2 bg-rose-500/50 rounded-l-full'
                            }`}
                        style={{ width: `${percentage}%` }}
                    />
                )}
            </div>

            {/* Value display */}
            <div className="flex justify-center">
                <span
                    className={`font-mono text-lg font-semibold ${isPositive ? 'text-emerald-400' : 'text-rose-400'
                        } ${Math.abs(clampedValue) < 0.02 ? 'text-stone-400' : ''}`}
                >
                    {clampedValue >= 0 ? '+' : ''}{(clampedValue * 100).toFixed(1)}%
                </span>
            </div>
        </div>
    );
};

export default MispricingGauge;
