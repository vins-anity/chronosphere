import { Link } from 'react-router-dom';

interface Match {
    match_id: string;
    league_name: string;
    radiant_team: string;
    dire_team: string;
    game_time: number;
    game_time_formatted: string;
    radiant_score: number;
    dire_score: number;
    gold_diff: number;
    radiant_win_prob: number;
    dire_win_prob: number;
    confidence: string;
    spectators: number;
}

interface FeaturedMatchProps {
    match: Match;
}

/**
 * Featured Match Component - Large hero card for the main live match
 */
export function FeaturedMatch({ match }: FeaturedMatchProps) {
    const radiantProb = Math.round(match.radiant_win_prob * 100);
    const direProb = Math.round(match.dire_win_prob * 100);

    // Determine bet signal
    const getBetSignal = () => {
        if (radiantProb >= 65) return { text: 'RADIANT VALUE', color: 'emerald', side: 'radiant' };
        if (direProb >= 65) return { text: 'DIRE VALUE', color: 'emerald', side: 'dire' };
        if (radiantProb >= 55) return { text: 'LEAN RADIANT', color: 'amber', side: 'radiant' };
        if (direProb >= 55) return { text: 'LEAN DIRE', color: 'amber', side: 'dire' };
        return { text: 'CLOSE MATCH', color: 'stone', side: 'none' };
    };

    const signal = getBetSignal();

    return (
        <div className="card-glass p-6 sm:p-8">
            {/* League & Status */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-6">
                <div className="flex items-center gap-2">
                    <span className="text-stone-400 text-sm">{match.league_name}</span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="live-dot" />
                        <span className="text-emerald-400 text-sm font-medium">LIVE</span>
                    </div>
                    <span className="text-stone-500 text-sm">
                        👁 {match.spectators.toLocaleString()} viewers
                    </span>
                </div>
            </div>

            {/* Teams */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-8">
                {/* Radiant */}
                <div className="flex-1 text-center sm:text-left">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 rounded-full mb-2">
                        <span className="text-emerald-400 text-xs font-medium">RADIANT</span>
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-bold text-stone-100">
                        {match.radiant_team}
                    </h3>
                </div>

                {/* VS & Score */}
                <div className="text-center shrink-0">
                    <div className="text-stone-500 text-sm mb-1">{match.game_time_formatted}</div>
                    <div className="text-3xl font-bold">
                        <span className="text-emerald-400">{match.radiant_score}</span>
                        <span className="text-stone-600 mx-2">-</span>
                        <span className="text-rose-400">{match.dire_score}</span>
                    </div>
                    <div className="text-stone-500 text-xs mt-1">
                        Gold: {match.gold_diff > 0 ? '+' : ''}{match.gold_diff.toLocaleString()}
                    </div>
                </div>

                {/* Dire */}
                <div className="flex-1 text-center sm:text-right">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-rose-500/10 rounded-full mb-2">
                        <span className="text-rose-400 text-xs font-medium">DIRE</span>
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-bold text-stone-100">
                        {match.dire_team}
                    </h3>
                </div>
            </div>

            {/* Win Probability Bar */}
            <div className="mb-6">
                <div className="flex justify-between mb-2">
                    <span className="text-emerald-400 font-mono font-bold text-xl">{radiantProb}%</span>
                    <span className="text-rose-400 font-mono font-bold text-xl">{direProb}%</span>
                </div>
                <div className="h-4 rounded-full overflow-hidden bg-stone-800 relative">
                    <div
                        className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-emerald-600 to-emerald-500 transition-all duration-500"
                        style={{ width: `${radiantProb}%` }}
                    />
                    <div
                        className="absolute right-0 top-0 bottom-0 bg-gradient-to-l from-rose-600 to-rose-500 transition-all duration-500"
                        style={{ width: `${direProb}%` }}
                    />
                </div>
                <div className="flex justify-between mt-2">
                    <span className="text-stone-500 text-sm">{match.radiant_team}</span>
                    <span className="text-stone-500 text-sm">{match.dire_team}</span>
                </div>
            </div>

            {/* Bet Signal */}
            <div className={`p-4 rounded-lg border ${signal.color === 'emerald'
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : signal.color === 'amber'
                        ? 'bg-amber-500/10 border-amber-500/30'
                        : 'bg-stone-800 border-stone-700'
                }`}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className={`text-2xl ${signal.color === 'emerald' ? 'text-emerald-400' : signal.color === 'amber' ? 'text-amber-400' : 'text-stone-400'}`}>
                            {signal.color === 'emerald' ? '🟢' : signal.color === 'amber' ? '🟡' : '⚪'}
                        </span>
                        <div>
                            <span className={`font-bold ${signal.color === 'emerald'
                                    ? 'text-emerald-400'
                                    : signal.color === 'amber'
                                        ? 'text-amber-400'
                                        : 'text-stone-400'
                                }`}>
                                {signal.text}
                            </span>
                            <p className="text-stone-400 text-sm">
                                {signal.color === 'emerald'
                                    ? 'Strong prediction - Consider betting'
                                    : signal.color === 'amber'
                                        ? 'Slight edge detected'
                                        : 'Game too close to call'}
                            </p>
                        </div>
                    </div>
                    <Link
                        to={`/matches/${match.match_id}`}
                        className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-stone-900 font-medium rounded-lg transition-colors text-sm sm:text-base"
                    >
                        View Details →
                    </Link>
                </div>
            </div>
        </div>
    );
}
