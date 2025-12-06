import { Link } from 'react-router-dom';

interface Match {
    match_id: string;
    league_name: string;
    radiant_team: string;
    dire_team: string;
    game_time?: number;
    game_time_formatted?: string;
    radiant_score?: number;
    dire_score?: number;
    gold_diff?: number;
    radiant_win_prob: number;
    dire_win_prob: number;
    confidence?: string;
    spectators?: number;
}

interface MatchCardProps {
    match: Match;
    compact?: boolean;
}

/**
 * Match Card Component - Compact card for match lists
 */
export function MatchCard({ match }: MatchCardProps) {
    const radiantProb = Math.round(match.radiant_win_prob * 100);
    const direProb = Math.round(match.dire_win_prob * 100);

    // Determine bet signal
    const getBetSignal = () => {
        if (radiantProb >= 65) return { icon: '🟢', text: 'RADIANT VALUE', color: 'emerald' };
        if (direProb >= 65) return { icon: '🟢', text: 'DIRE VALUE', color: 'emerald' };
        if (radiantProb >= 55) return { icon: '🟡', text: 'LEAN', color: 'amber' };
        if (direProb >= 55) return { icon: '🟡', text: 'LEAN', color: 'amber' };
        return { icon: '⚪', text: 'SKIP', color: 'stone' };
    };

    const signal = getBetSignal();
    const isLive = match.game_time !== undefined && match.game_time > 0;

    return (
        <Link
            to={`/matches/${match.match_id}`}
            className="card-glass block p-4 hover:border-amber-500/40 transition-all group"
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <span className="text-stone-500 text-xs truncate max-w-[60%]">
                    {match.league_name}
                </span>
                {isLive ? (
                    <div className="flex items-center gap-1.5">
                        <span className="live-dot" style={{ width: '6px', height: '6px' }} />
                        <span className="text-emerald-400 text-xs font-medium">LIVE</span>
                    </div>
                ) : (
                    <span className="text-stone-600 text-xs">UPCOMING</span>
                )}
            </div>

            {/* Teams */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-stone-200 font-medium text-sm truncate max-w-[70%]">
                        {match.radiant_team}
                    </span>
                    {isLive && (
                        <span className="text-emerald-400 font-mono text-sm">
                            {match.radiant_score}
                        </span>
                    )}
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-stone-200 font-medium text-sm truncate max-w-[70%]">
                        {match.dire_team}
                    </span>
                    {isLive && (
                        <span className="text-rose-400 font-mono text-sm">
                            {match.dire_score}
                        </span>
                    )}
                </div>
            </div>

            {/* Probability Bar */}
            <div className="mb-3">
                <div className="h-2 rounded-full overflow-hidden bg-stone-800 flex">
                    <div
                        className="bg-gradient-to-r from-emerald-600 to-emerald-500 transition-all duration-300"
                        style={{ width: `${radiantProb}%` }}
                    />
                    <div
                        className="bg-gradient-to-l from-rose-600 to-rose-500 flex-1"
                    />
                </div>
                <div className="flex justify-between mt-1.5">
                    <span className="text-emerald-400 font-mono text-xs">{radiantProb}%</span>
                    <span className="text-rose-400 font-mono text-xs">{direProb}%</span>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-3 border-t border-stone-800">
                <div className="flex items-center gap-1.5">
                    <span className={`text-sm ${signal.color === 'emerald'
                        ? 'text-emerald-400'
                        : signal.color === 'amber'
                            ? 'text-amber-400'
                            : 'text-stone-500'
                        }`}>
                        {signal.icon} {signal.text}
                    </span>
                </div>
                {match.spectators !== undefined && match.spectators > 0 && (
                    <span className="text-stone-500 text-xs">
                        👁 {match.spectators >= 1000
                            ? `${(match.spectators / 1000).toFixed(1)}k`
                            : match.spectators}
                    </span>
                )}
            </div>
        </Link>
    );
}

export default MatchCard;
