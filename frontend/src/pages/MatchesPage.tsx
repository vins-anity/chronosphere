import { useState, useEffect } from 'react';
import { MatchCard } from '../components/MatchCard';
import {
    IconLive,
    IconClock,
    IconChartBar,
    IconAlertCircle,
    IconPlayerPlay,
    IconCalendar,
    IconRefresh,
    IconChevronLeft,
    IconChevronRight,
} from '../components/Icons';

type TabType = 'live' | 'upcoming' | 'recent';

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
    radiant_win_prob: number;
    dire_win_prob: number;
    confidence: string;
    spectators: number;
}

/**
 * Matches Page - All matches with Live/Upcoming/Recent tabs
 */
export function MatchesPage() {
    const [activeTab, setActiveTab] = useState<TabType>('live');
    const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const matchesPerPage = 12;

    useEffect(() => {
        fetchMatches();
        const interval = setInterval(fetchMatches, activeTab === 'live' ? 15000 : 60000);
        return () => clearInterval(interval);
    }, [activeTab]);

    const fetchMatches = async () => {
        try {
            setLoading(true);
            const endpoint = activeTab === 'live'
                ? '/api/v1/matches/live/pro'
                : '/api/v1/matches/live/pro'; // TODO: Add upcoming/recent endpoints

            const res = await fetch(endpoint);
            if (!res.ok) throw new Error('Failed to fetch matches');
            const data = await res.json();
            setLiveMatches(data);
            setError(null);
        } catch (e) {
            setError('Unable to fetch matches');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    // Pagination
    const totalPages = Math.ceil(liveMatches.length / matchesPerPage);
    const paginatedMatches = liveMatches.slice(
        (currentPage - 1) * matchesPerPage,
        currentPage * matchesPerPage
    );

    const getEmptyStateIcon = () => {
        switch (activeTab) {
            case 'live':
                return <IconPlayerPlay size={40} className="text-stone-500" />;
            case 'upcoming':
                return <IconCalendar size={40} className="text-stone-500" />;
            case 'recent':
                return <IconChartBar size={40} className="text-stone-500" />;
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-stone-100 mb-2">Matches</h1>
                <p className="text-stone-400">
                    Real-time predictions for professional Dota 2 matches
                </p>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
                <TabButton
                    active={activeTab === 'live'}
                    onClick={() => { setActiveTab('live'); setCurrentPage(1); }}
                    count={activeTab === 'live' ? liveMatches.length : undefined}
                    icon={<span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                >
                    Live
                </TabButton>
                <TabButton
                    active={activeTab === 'upcoming'}
                    onClick={() => { setActiveTab('upcoming'); setCurrentPage(1); }}
                    icon={<IconClock size={16} />}
                >
                    Upcoming
                </TabButton>
                <TabButton
                    active={activeTab === 'recent'}
                    onClick={() => { setActiveTab('recent'); setCurrentPage(1); }}
                    icon={<IconChartBar size={16} />}
                >
                    Recent
                </TabButton>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex justify-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent" />
                </div>
            )}

            {/* Error */}
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

            {/* Empty State */}
            {!loading && !error && liveMatches.length === 0 && (
                <div className="text-center py-16">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-stone-800 flex items-center justify-center">
                        {getEmptyStateIcon()}
                    </div>
                    <h2 className="text-2xl font-semibold text-stone-200 mb-2">
                        No {activeTab === 'live' ? 'Live' : activeTab === 'upcoming' ? 'Upcoming' : 'Recent'} Matches
                    </h2>
                    <p className="text-stone-400">
                        {activeTab === 'live'
                            ? 'Check back soon for live predictions'
                            : activeTab === 'upcoming'
                                ? 'No matches scheduled in the next 24 hours'
                                : 'No recent match data available'}
                    </p>
                </div>
            )}

            {/* Match Grid */}
            {!loading && !error && paginatedMatches.length > 0 && (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
                        {paginatedMatches.map(match => (
                            <MatchCard key={match.match_id} match={match} />
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex justify-center items-center gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="inline-flex items-center gap-1 px-4 py-2 rounded-lg bg-stone-800 text-stone-300 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <IconChevronLeft size={16} />
                                Previous
                            </button>

                            <div className="flex items-center gap-1 px-4">
                                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                    <button
                                        key={page}
                                        onClick={() => setCurrentPage(page)}
                                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${page === currentPage
                                                ? 'bg-amber-500 text-stone-900'
                                                : 'bg-stone-800 text-stone-300 hover:bg-stone-700'
                                            }`}
                                    >
                                        {page}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="inline-flex items-center gap-1 px-4 py-2 rounded-lg bg-stone-800 text-stone-300 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                Next
                                <IconChevronRight size={16} />
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

function TabButton({
    children,
    active,
    onClick,
    count,
    icon,
}: {
    children: React.ReactNode;
    active: boolean;
    onClick: () => void;
    count?: number;
    icon?: React.ReactNode;
}) {
    return (
        <button
            onClick={onClick}
            className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${active
                    ? 'bg-amber-500 text-stone-900'
                    : 'bg-stone-800 text-stone-300 hover:bg-stone-700'
                }`}
        >
            {icon}
            {children}
            {count !== undefined && count > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${active
                        ? 'bg-stone-900/30 text-stone-900'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                    {count}
                </span>
            )}
        </button>
    );
}
