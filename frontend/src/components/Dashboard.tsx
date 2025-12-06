import React from 'react';
import { ProbabilityRing } from './ProbabilityRing';
import { MispricingGauge } from './MispricingGauge';
import { StatCard } from './StatCard';
import { MatchBadge, ConnectionStatus } from './MatchBadge';
import { GameState } from '../store/useAppStore';

// Icons as simple SVG components
const GoldIcon = () => (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.736 6.979C9.208 6.193 9.696 6 10 6c.304 0 .792.193 1.264.979a1 1 0 001.715-1.029C12.279 4.784 11.232 4 10 4s-2.279.784-2.979 1.95c-.285.475-.507 1-.67 1.55H6a1 1 0 000 2h.013a9.358 9.358 0 000 1H6a1 1 0 100 2h.351c.163.55.385 1.075.67 1.55C7.721 15.216 8.768 16 10 16s2.279-.784 2.979-1.95a1 1 0 10-1.715-1.029c-.472.786-.96.979-1.264.979-.304 0-.792-.193-1.264-.979a4.265 4.265 0 01-.264-.521H10a1 1 0 100-2H8.017a7.36 7.36 0 010-1H10a1 1 0 100-2H8.472a4.265 4.265 0 01.264-.521z" clipRule="evenodd" fillRule="evenodd" />
    </svg>
);

const TrendIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
);

const ChartIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
);

const ClockIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

interface DashboardProps {
    gameState: GameState | null;
    connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

/**
 * Main dashboard layout for Chronosphere.
 */
export const Dashboard: React.FC<DashboardProps> = ({
    gameState,
    connectionStatus,
}) => {
    // Format game time as MM:SS
    const formatTime = (seconds: number) => {
        const mins = Math.floor(Math.abs(seconds) / 60);
        const secs = Math.abs(seconds) % 60;
        const sign = seconds < 0 ? '-' : '';
        return `${sign}${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Format gold with K suffix
    const formatGold = (gold: number) => {
        const absGold = Math.abs(gold);
        if (absGold >= 1000) {
            return `${gold >= 0 ? '+' : ''}${(gold / 1000).toFixed(1)}k`;
        }
        return `${gold >= 0 ? '+' : ''}${gold}`;
    };

    // Get velocity trend
    const getVelocityTrend = (velocity: number): 'up' | 'down' | 'neutral' => {
        if (velocity > 10) return 'up';
        if (velocity < -10) return 'down';
        return 'neutral';
    };

    // Default state when no game data
    const defaultState: GameState = {
        type: 'update',
        match_id: null,
        is_verified: false,
        game_time: 0,
        gold_diff: 0,
        xp_diff: 0,
        networth_velocity: 0,
        model_win_probability: 0.5,
        market_implied_probability: 0.5,
        market_odds_radiant: 1.9,
        mispricing_index: 0,
        draft_radiant_score: 0.5,
        series_score_diff: 0,
        is_mock_odds: true,
    };

    const state = gameState || defaultState;
    const hasData = gameState !== null;

    return (
        <div className="min-h-screen bg-stone-900 p-4 md:p-6 lg:p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <h1 className="text-2xl md:text-3xl font-semibold text-stone-100">
                            <span className="text-amber-500">Chrono</span>sphere
                        </h1>
                        <MatchBadge
                            isVerified={state.is_verified}
                            isMockOdds={state.is_mock_odds}
                            matchId={state.match_id}
                        />
                    </div>
                    <ConnectionStatus status={connectionStatus} />
                </header>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Main Prediction */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Hero Card - Win Probability */}
                        <div className="card-glass p-6 md:p-8">
                            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                                {/* Model Prediction */}
                                <div className="flex flex-col items-center">
                                    <ProbabilityRing
                                        probability={state.model_win_probability}
                                        label="AI Prediction"
                                        size={180}
                                        teamColor="radiant"
                                    />
                                </div>

                                {/* VS Divider */}
                                <div className="hidden md:flex flex-col items-center gap-2">
                                    <span className="text-caption text-stone-500">VS</span>
                                    <div className="w-px h-24 bg-gradient-to-b from-transparent via-stone-600 to-transparent" />
                                </div>

                                {/* Market Odds */}
                                <div className="flex flex-col items-center">
                                    <ProbabilityRing
                                        probability={state.market_implied_probability}
                                        label="Market Odds"
                                        size={180}
                                        teamColor="radiant"
                                    />
                                </div>
                            </div>

                            {/* Mispricing Gauge */}
                            <div className="mt-8 pt-6 border-t border-stone-700/50">
                                <h3 className="text-title text-stone-300 mb-4 text-center">Value Signal</h3>
                                <MispricingGauge mispricing={state.mispricing_index} />
                            </div>
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <StatCard
                                label="Game Time"
                                value={formatTime(state.game_time)}
                                icon={<ClockIcon />}
                            />
                            <StatCard
                                label="Gold Diff"
                                value={formatGold(state.gold_diff)}
                                trend={state.gold_diff > 0 ? 'up' : state.gold_diff < 0 ? 'down' : 'neutral'}
                                icon={<GoldIcon />}
                            />
                            <StatCard
                                label="Velocity"
                                value={`${state.networth_velocity >= 0 ? '+' : ''}${state.networth_velocity.toFixed(0)}`}
                                unit="/s"
                                trend={getVelocityTrend(state.networth_velocity)}
                                icon={<TrendIcon />}
                            />
                            <StatCard
                                label="Draft Score"
                                value={(state.draft_radiant_score * 100).toFixed(0)}
                                unit="%"
                                subValue="Radiant"
                                icon={<ChartIcon />}
                            />
                        </div>
                    </div>

                    {/* Right Column - Details */}
                    <div className="space-y-6">
                        {/* Market Details */}
                        <div className="card-glass p-5">
                            <h3 className="text-title text-stone-300 mb-4">Market Details</h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-stone-400">Radiant Odds</span>
                                    <span className="font-mono text-lg text-stone-100">
                                        {state.market_odds_radiant.toFixed(2)}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-stone-400">Implied Prob</span>
                                    <span className="font-mono text-lg text-stone-100">
                                        {(state.market_implied_probability * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-stone-400">Model Prob</span>
                                    <span className="font-mono text-lg text-amber-400">
                                        {(state.model_win_probability * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="border-t border-stone-700/50 pt-4 flex justify-between items-center">
                                    <span className="text-stone-400 font-medium">Edge</span>
                                    <span className={`font-mono text-xl font-semibold ${state.mispricing_index > 0 ? 'text-emerald-400' :
                                            state.mispricing_index < 0 ? 'text-rose-400' : 'text-stone-400'
                                        }`}>
                                        {state.mispricing_index >= 0 ? '+' : ''}
                                        {(state.mispricing_index * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Series Info */}
                        {state.series_score_diff !== 0 && (
                            <div className="card-glass p-5">
                                <h3 className="text-title text-stone-300 mb-4">Series Status</h3>
                                <div className="text-center">
                                    <span className={`font-mono text-2xl font-bold ${state.series_score_diff > 0 ? 'text-emerald-400' : 'text-rose-400'
                                        }`}>
                                        {state.series_score_diff > 0 ? '+' : ''}{state.series_score_diff}
                                    </span>
                                    <p className="text-stone-500 text-sm mt-1">
                                        {state.series_score_diff > 0 ? 'Radiant leads' : 'Dire leads'}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* How to Interpret */}
                        <div className="card-glass p-5">
                            <h3 className="text-title text-stone-300 mb-3">How to Read</h3>
                            <ul className="space-y-2 text-sm text-stone-400">
                                <li className="flex items-start gap-2">
                                    <span className="text-emerald-400">●</span>
                                    <span><strong className="text-stone-300">Positive Edge:</strong> Model thinks Radiant is undervalued</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-rose-400">●</span>
                                    <span><strong className="text-stone-300">Negative Edge:</strong> Model thinks Radiant is overvalued</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-amber-400">●</span>
                                    <span><strong className="text-stone-300">&gt;10% Edge:</strong> Significant opportunity</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="text-center text-xs text-stone-600 pt-4">
                    {!hasData && (
                        <p className="text-amber-500/70 mb-2">
                            Waiting for game data. Start spectating a match to see live predictions.
                        </p>
                    )}
                    <p>Chronosphere v2.0 • Contextual Alpha Engine</p>
                </footer>
            </div>
        </div>
    );
};

export default Dashboard;
