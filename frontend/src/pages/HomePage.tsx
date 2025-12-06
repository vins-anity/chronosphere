import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MatchCard } from '../components/MatchCard';
import { FeaturedMatch } from '../components/FeaturedMatch';
import {
    IconChartBar,
    IconBrain,
    IconRobot,
    IconTarget,
    IconAlertCircle,
    IconPlayerPlay,
    IconArrowRight,
    IconRefresh
} from '../components/Icons';

interface LiveMatch {
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

/**
 * Smart Landing Page
 * - Shows featured live match if available
 * - Falls back to upcoming matches
 * - Trust indicator banner
 */
export function HomePage() {
    const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchMatches();
        const interval = setInterval(fetchMatches, 15000);
        return () => clearInterval(interval);
    }, []);

    const fetchMatches = async () => {
        try {
            const res = await fetch('/api/v1/matches/live/pro');
            if (!res.ok) throw new Error('Failed to fetch matches');
            const data = await res.json();
            setLiveMatches(data);
            setError(null);
        } catch (e) {
            setError('Unable to fetch live matches');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const sortedMatches = [...liveMatches].sort((a, b) => b.spectators - a.spectators);
    const featuredMatch = sortedMatches[0];
    const otherMatches = sortedMatches.slice(1, 7);

    return (
        <div className="min-h-screen">
            {/* Hero Section */}
            <section className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-amber-500/5 via-transparent to-transparent pointer-events-none" />

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-16">
                    {/* Tagline */}
                    <div className="text-center mb-8 sm:mb-12">
                        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-stone-100 mb-4">
                            AI-Powered <span className="text-amber-500">Dota 2</span> Predictions
                        </h1>
                        <p className="text-stone-400 text-lg sm:text-xl max-w-2xl mx-auto">
                            Make confident betting decisions with machine learning insights and real-time analysis
                        </p>
                    </div>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex justify-center py-20">
                            <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent" />
                        </div>
                    )}

                    {/* Error State */}
                    {error && !loading && (
                        <div className="text-center py-16">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-rose-500/20 flex items-center justify-center">
                                <IconAlertCircle size={32} className="text-rose-400" />
                            </div>
                            <p className="text-stone-400 text-lg mb-4">{error}</p>
                            <button
                                onClick={fetchMatches}
                                className="inline-flex items-center gap-2 px-6 py-2 bg-amber-500 hover:bg-amber-600 text-stone-900 font-medium rounded-lg transition-colors"
                            >
                                <IconRefresh size={18} />
                                Retry
                            </button>
                        </div>
                    )}

                    {/* Live Matches */}
                    {!loading && !error && liveMatches.length > 0 && (
                        <>
                            <div className="mb-8">
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="live-dot" />
                                    <span className="text-emerald-400 font-medium text-sm uppercase tracking-wider">
                                        Featured Live Match
                                    </span>
                                </div>
                                <FeaturedMatch match={featuredMatch} />
                            </div>

                            {otherMatches.length > 0 && (
                                <div className="mt-12">
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-xl font-semibold text-stone-200">
                                            Other Live Matches
                                        </h2>
                                        <Link
                                            to="/matches"
                                            className="inline-flex items-center gap-1 text-amber-500 hover:text-amber-400 text-sm font-medium transition-colors"
                                        >
                                            View All
                                            <IconArrowRight size={16} />
                                        </Link>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {otherMatches.map(match => (
                                            <MatchCard key={match.match_id} match={match} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}

                    {/* No Live Matches */}
                    {!loading && !error && liveMatches.length === 0 && (
                        <div className="text-center py-16">
                            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-stone-800 flex items-center justify-center">
                                <IconPlayerPlay size={40} className="text-stone-500" />
                            </div>
                            <h2 className="text-2xl font-semibold text-stone-200 mb-2">
                                No Live Matches Right Now
                            </h2>
                            <p className="text-stone-400 mb-8">
                                Check back soon for live predictions or view upcoming matches
                            </p>
                            <Link
                                to="/matches"
                                className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-stone-900 font-medium rounded-lg transition-colors"
                            >
                                View Upcoming Matches
                                <IconArrowRight size={20} />
                            </Link>
                        </div>
                    )}
                </div>
            </section>

            {/* Trust Banner */}
            <section className="border-t border-stone-800 bg-stone-900/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                                <IconTarget size={24} className="text-amber-500" />
                            </div>
                            <div>
                                <p className="text-stone-200 font-medium">
                                    Powered by Machine Learning
                                </p>
                                <p className="text-stone-400 text-sm">
                                    Proprietary model trained on 50,000+ professional matches
                                </p>
                            </div>
                        </div>
                        <Link
                            to="/accuracy"
                            className="inline-flex items-center gap-1 text-amber-500 hover:text-amber-400 text-sm font-medium transition-colors"
                        >
                            View Accuracy Stats
                            <IconArrowRight size={16} />
                        </Link>
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section className="py-16 sm:py-24">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-2xl sm:text-3xl font-bold text-stone-100 text-center mb-12">
                        How Chronosphere Works
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={<IconChartBar size={32} className="text-amber-500" />}
                            title="Real-Time Data"
                            description="We aggregate live match data from multiple professional esports sources every 15 seconds"
                        />
                        <FeatureCard
                            icon={<IconBrain size={32} className="text-amber-500" />}
                            title="ML Prediction"
                            description="Our proprietary model analyzes dozens of signals to calculate win probabilities"
                        />
                        <FeatureCard
                            icon={<IconRobot size={32} className="text-amber-500" />}
                            title="AI Analysis"
                            description="Advanced AI provides natural language insights explaining the prediction"
                        />
                    </div>
                    <div className="text-center mt-12">
                        <Link
                            to="/about"
                            className="inline-flex items-center gap-2 px-6 py-3 border border-amber-500 text-amber-500 hover:bg-amber-500 hover:text-stone-900 font-medium rounded-lg transition-all"
                        >
                            Learn More About Our Methodology
                            <IconArrowRight size={20} />
                        </Link>
                    </div>
                </div>
            </section>
        </div>
    );
}

function FeatureCard({ icon, title, description }: {
    icon: React.ReactNode;
    title: string;
    description: string
}) {
    return (
        <div className="card-glass p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-amber-500/10 flex items-center justify-center">
                {icon}
            </div>
            <h3 className="text-lg font-semibold text-stone-100 mb-2">{title}</h3>
            <p className="text-stone-400 text-sm">{description}</p>
        </div>
    );
}
