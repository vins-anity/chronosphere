import React from 'react';

interface MatchBadgeProps {
    isVerified: boolean;
    isMockOdds: boolean;
    matchId?: string | null;
}

/**
 * Badge showing match verification and data source status.
 */
export const MatchBadge: React.FC<MatchBadgeProps> = ({
    isVerified,
    isMockOdds,
    matchId,
}) => {
    if (!matchId) {
        return (
            <div className="badge-mock">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Waiting for Match</span>
            </div>
        );
    }

    if (isVerified) {
        return (
            <div className="badge-verified">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Pro Match Verified</span>
            </div>
        );
    }

    if (isMockOdds) {
        return (
            <div className="badge-mock">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Dev Mode (Mock Odds)</span>
            </div>
        );
    }

    return (
        <div className="badge-unverified">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Unverified Source</span>
        </div>
    );
};

interface ConnectionStatusProps {
    status: 'connected' | 'disconnected' | 'connecting';
}

/**
 * Live connection status indicator.
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ status }) => {
    const getStatusConfig = () => {
        switch (status) {
            case 'connected':
                return { color: 'bg-emerald-500', label: 'Live', pulse: true };
            case 'connecting':
                return { color: 'bg-amber-500', label: 'Connecting...', pulse: true };
            case 'disconnected':
                return { color: 'bg-rose-500', label: 'Offline', pulse: false };
        }
    };

    const config = getStatusConfig();

    return (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-stone-800/50 rounded-full">
            <div className={`w-2 h-2 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-xs font-medium text-stone-300">{config.label}</span>
        </div>
    );
};

export { MatchBadge as default };
