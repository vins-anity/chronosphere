import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

interface MatchData {
    match_id: string;
    league_name: string;
    radiant_team: string;
    dire_team: string;
    game_time: number;
    game_time_formatted: string;
    radiant_score: number;
    dire_score: number;
    gold_diff: number;
    xp_diff: number;
    radiant_win_prob: number;
    dire_win_prob: number;
    confidence: string;
    spectators: number;
}

interface AIAnalysis {
    match_id: string;
    analysis: {
        summary: string;
        key_factors: string[];
        risk_level: string;
        confidence_reasoning: string;
        momentum_analysis: string;
        betting_insight: string;
    };
    advice: {
        recommendation: string;
        suggested_side: string;
        reasoning: string;
        stake_suggestion: string;
        warnings: string[];
    };
    ml_prediction: number;
    edge_signal: string;
    is_fallback?: boolean;
}

/**
 * Match Detail Page - Core prediction page with AI analysis
 */
export function MatchDetailPage() {
    const { matchId } = useParams<{ matchId: string }>();
    const [match, setMatch] = useState<MatchData | null>(null);
    const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [analysisLoading, setAnalysisLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (matchId) {
            fetchMatch();
            const interval = setInterval(fetchMatch, 10000); // Refresh every 10s
            return () => clearInterval(interval);
        }
    }, [matchId]);

    const fetchMatch = async () => {
        try {
            const res = await fetch('/api/v1/matches/live/pro');
            if (!res.ok) throw new Error('Failed to fetch matches');
            const data = await res.json();
            const foundMatch = data.find((m: MatchData) => m.match_id === matchId);

            if (foundMatch) {
                setMatch(foundMatch);
                setError(null);
            } else {
                setError('Match not found or has ended');
            }
        } catch (e) {
            setError('Unable to fetch match data');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const fetchAnalysis = async () => {
        if (!matchId) return;

        setAnalysisLoading(true);
        try {
            const res = await fetch(`/api/v1/matches/live/pro/${matchId}/analysis`);
            if (res.ok) {
                const data = await res.json();
                setAnalysis(data);
            }
        } catch (e) {
            console.error('Failed to fetch AI analysis:', e);
        } finally {
            setAnalysisLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[60vh]">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent" />
            </div>
        );
    }

    if (error || !match) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
                <div className="text-stone-500 text-6xl mb-4">⚠️</div>
                <h2 className="text-2xl font-semibold text-stone-200 mb-2">
                    {error || 'Match not found'}
                </h2>
                <p className="text-stone-400 mb-8">
                    This match may have ended or the data is unavailable
                </p>
                <Link
                    to="/matches"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-stone-900 font-medium rounded-lg transition-colors"
                >
                    ← Back to Matches
                </Link>
            </div>
        );
    }

    const radiantProb = Math.round(match.radiant_win_prob * 100);
    const direProb = Math.round(match.dire_win_prob * 100);

    // Bet signal logic
    const getBetSignal = () => {
        if (radiantProb >= 65) return { icon: '🟢', text: 'STRONG VALUE - RADIANT', color: 'emerald', safe: true };
        if (direProb >= 65) return { icon: '🟢', text: 'STRONG VALUE - DIRE', color: 'emerald', safe: true };
        if (radiantProb >= 55) return { icon: '🟡', text: 'LEAN RADIANT', color: 'amber', safe: false };
        if (direProb >= 55) return { icon: '🟡', text: 'LEAN DIRE', color: 'amber', safe: false };
        return { icon: '⚪', text: 'CLOSE MATCH - SKIP', color: 'stone', safe: false };
    };
    const signal = getBetSignal();

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumb */}
            <Link
                to="/matches"
                className="inline-flex items-center gap-2 text-stone-400 hover:text-amber-500 mb-6 transition-colors"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Matches
            </Link>

            {/* Match Header */}
            <div className="card-glass p-6 mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                    <div>
                        <span className="text-stone-500 text-sm">{match.league_name}</span>
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
                <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
                    {/* Radiant */}
                    <div className="flex-1 text-center lg:text-left">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 rounded-full mb-2">
                            <span className="text-emerald-400 text-xs font-medium">RADIANT</span>
                        </div>
                        <h2 className="text-3xl sm:text-4xl font-bold text-stone-100 mb-2">
                            {match.radiant_team}
                        </h2>
                        <span className="text-emerald-400 font-mono text-4xl font-bold">{radiantProb}%</span>
                    </div>

                    {/* VS & Stats */}
                    <div className="text-center shrink-0 px-8">
                        <div className="text-stone-500 text-sm mb-2">{match.game_time_formatted}</div>
                        <div className="text-4xl font-bold mb-4">
                            <span className="text-emerald-400">{match.radiant_score}</span>
                            <span className="text-stone-600 mx-3">-</span>
                            <span className="text-rose-400">{match.dire_score}</span>
                        </div>
                        <div className="space-y-1 text-sm">
                            <div className="text-stone-400">
                                Gold: <span className={match.gold_diff >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                    {match.gold_diff >= 0 ? '+' : ''}{match.gold_diff.toLocaleString()}
                                </span>
                            </div>
                            <div className="text-stone-400">
                                XP: <span className={match.xp_diff >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                    {match.xp_diff >= 0 ? '+' : ''}{match.xp_diff.toLocaleString()}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Dire */}
                    <div className="flex-1 text-center lg:text-right">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-rose-500/10 rounded-full mb-2">
                            <span className="text-rose-400 text-xs font-medium">DIRE</span>
                        </div>
                        <h2 className="text-3xl sm:text-4xl font-bold text-stone-100 mb-2">
                            {match.dire_team}
                        </h2>
                        <span className="text-rose-400 font-mono text-4xl font-bold">{direProb}%</span>
                    </div>
                </div>
            </div>

            {/* Win Probability Bar */}
            <div className="card-glass p-6 mb-6">
                <h3 className="text-lg font-semibold text-stone-200 mb-4">Win Probability</h3>
                <div className="mb-4">
                    <div className="h-6 rounded-full overflow-hidden bg-stone-800 relative flex">
                        <div
                            className="bg-gradient-to-r from-emerald-600 to-emerald-500 transition-all duration-500 flex items-center justify-end"
                            style={{ width: `${radiantProb}%` }}
                        >
                            {radiantProb > 20 && (
                                <span className="text-white text-sm font-bold px-2">{radiantProb}%</span>
                            )}
                        </div>
                        <div
                            className="bg-gradient-to-l from-rose-600 to-rose-500 flex-1 flex items-center justify-start"
                        >
                            {direProb > 20 && (
                                <span className="text-white text-sm font-bold px-2">{direProb}%</span>
                            )}
                        </div>
                    </div>
                    <div className="flex justify-between mt-2">
                        <span className="text-stone-400 text-sm">{match.radiant_team}</span>
                        <span className="text-stone-400 text-sm">{match.dire_team}</span>
                    </div>
                </div>

                {/* Bet Signal */}
                <div className={`p-4 rounded-lg border ${signal.color === 'emerald'
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : signal.color === 'amber'
                        ? 'bg-amber-500/10 border-amber-500/30'
                        : 'bg-stone-800 border-stone-700'
                    }`}>
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">{signal.icon}</span>
                        <div>
                            <span className={`font-bold text-lg ${signal.color === 'emerald'
                                ? 'text-emerald-400'
                                : signal.color === 'amber'
                                    ? 'text-amber-400'
                                    : 'text-stone-400'
                                }`}>
                                {signal.text}
                            </span>
                            <p className="text-stone-400 text-sm">
                                {signal.safe
                                    ? '✓ Safe threshold reached - Consider betting'
                                    : signal.color === 'amber'
                                        ? 'Slight edge detected - Proceed with caution'
                                        : 'Game too close to recommend a bet'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* AI Analysis Section */}
            <div className="card-glass p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🤖</span>
                        <h3 className="text-lg font-semibold text-stone-200">AI Analyst</h3>
                        <span className="text-stone-500 text-xs">(Powered by Gemini)</span>
                    </div>
                    {!analysis && (
                        <button
                            onClick={fetchAnalysis}
                            disabled={analysisLoading}
                            className="px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-stone-900 font-medium rounded-lg transition-colors text-sm"
                        >
                            {analysisLoading ? 'Analyzing...' : 'Get AI Analysis'}
                        </button>
                    )}
                </div>

                {analysisLoading && (
                    <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent mx-auto mb-4" />
                            <p className="text-stone-400">Analyzing match data...</p>
                        </div>
                    </div>
                )}

                {!analysis && !analysisLoading && (
                    <div className="text-center py-8">
                        <p className="text-stone-400">
                            Click "Get AI Analysis" for detailed insights on this match
                        </p>
                    </div>
                )}

                {analysis && (
                    <div className="space-y-6">
                        {/* Summary */}
                        <div>
                            <h4 className="text-stone-300 font-medium mb-2">Summary</h4>
                            <p className="text-stone-400">{analysis.analysis.summary}</p>
                        </div>

                        {/* Key Factors */}
                        <div>
                            <h4 className="text-stone-300 font-medium mb-2">Key Factors</h4>
                            <ul className="space-y-2">
                                {analysis.analysis.key_factors.map((factor, i) => (
                                    <li key={i} className="flex items-start gap-2 text-stone-400">
                                        <span className="text-amber-500 mt-1">•</span>
                                        {factor}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Betting Insight */}
                        <div className={`p-4 rounded-lg ${analysis.advice.recommendation === 'STRONG_BET'
                            ? 'bg-emerald-500/10 border border-emerald-500/30'
                            : analysis.advice.recommendation === 'SMALL_BET'
                                ? 'bg-amber-500/10 border border-amber-500/30'
                                : 'bg-stone-800 border border-stone-700'
                            }`}>
                            <div className="flex items-center gap-2 mb-2">
                                <span className={`font-bold ${analysis.advice.recommendation === 'STRONG_BET'
                                    ? 'text-emerald-400'
                                    : analysis.advice.recommendation === 'SMALL_BET'
                                        ? 'text-amber-400'
                                        : 'text-stone-400'
                                    }`}>
                                    💡 {analysis.advice.recommendation.replace('_', ' ')}
                                    {analysis.advice.suggested_side !== 'NONE' && ` - ${analysis.advice.suggested_side}`}
                                </span>
                            </div>
                            <p className="text-stone-400 text-sm mb-2">{analysis.advice.reasoning}</p>
                            <p className="text-stone-500 text-sm">Suggested stake: {analysis.advice.stake_suggestion}</p>
                        </div>

                        {/* Warnings */}
                        {analysis.advice.warnings.length > 0 && (
                            <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30">
                                <h4 className="text-rose-400 font-medium mb-2">⚠️ Warnings</h4>
                                <ul className="space-y-1">
                                    {analysis.advice.warnings.map((warning, i) => (
                                        <li key={i} className="text-stone-400 text-sm">• {warning}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {analysis.is_fallback && (
                            <p className="text-stone-500 text-xs text-center">
                                * Using fallback analysis (AI service temporarily unavailable)
                            </p>
                        )}
                    </div>
                )}
            </div>

            {/* Live Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard
                    label="Game Time"
                    value={match.game_time_formatted}
                />
                <StatCard
                    label="Kill Score"
                    value={`${match.radiant_score} - ${match.dire_score}`}
                />
                <StatCard
                    label="Gold Diff"
                    value={`${match.gold_diff >= 0 ? '+' : ''}${(match.gold_diff / 1000).toFixed(1)}k`}
                    positive={match.gold_diff >= 0}
                />
                <StatCard
                    label="XP Diff"
                    value={`${match.xp_diff >= 0 ? '+' : ''}${(match.xp_diff / 1000).toFixed(1)}k`}
                    positive={match.xp_diff >= 0}
                />
            </div>
        </div>
    );
}

function StatCard({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
    return (
        <div className="card-glass p-4 text-center">
            <div className="text-stone-500 text-xs uppercase tracking-wider mb-1">{label}</div>
            <div className={`font-mono text-xl font-bold ${positive === true
                ? 'text-emerald-400'
                : positive === false
                    ? 'text-rose-400'
                    : 'text-stone-200'
                }`}>
                {value}
            </div>
        </div>
    );
}

export default MatchDetailPage;
