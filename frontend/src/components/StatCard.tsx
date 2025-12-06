import React from 'react';

interface StatCardProps {
    label: string;
    value: string | number;
    unit?: string;
    trend?: 'up' | 'down' | 'neutral';
    subValue?: string;
    icon?: React.ReactNode;
}

/**
 * Compact stat display card for dashboard grid.
 */
export const StatCard: React.FC<StatCardProps> = ({
    label,
    value,
    unit,
    trend = 'neutral',
    subValue,
    icon,
}) => {
    const getTrendColor = () => {
        switch (trend) {
            case 'up': return 'text-emerald-400';
            case 'down': return 'text-rose-400';
            default: return 'text-stone-300';
        }
    };

    const getTrendIcon = () => {
        switch (trend) {
            case 'up': return '↑';
            case 'down': return '↓';
            default: return null;
        }
    };

    return (
        <div className="stat-item group">
            <div className="flex items-center justify-between">
                <span className="stat-label">{label}</span>
                {icon && <span className="text-stone-500 group-hover:text-amber-500 transition-colors">{icon}</span>}
            </div>
            <div className="flex items-baseline gap-1">
                <span className={`stat-value ${getTrendColor()}`}>
                    {typeof value === 'number' ? value.toLocaleString() : value}
                </span>
                {unit && <span className="text-sm text-stone-500">{unit}</span>}
                {getTrendIcon() && (
                    <span className={`text-sm ${getTrendColor()}`}>{getTrendIcon()}</span>
                )}
            </div>
            {subValue && (
                <span className="text-xs text-stone-500">{subValue}</span>
            )}
        </div>
    );
};

export default StatCard;
