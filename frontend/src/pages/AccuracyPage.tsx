import {
    IconBulb,
    IconCheck,
    IconCircleX,
} from '../components/Icons';

/**
 * Accuracy Page - Show past prediction performance
 */
export function AccuracyPage() {
    // Mock data - In production, fetch from backend
    const stats = {
        overall: 72,
        thisWeek: 78,
        thisMonth: 74,
        totalPredictions: 1247,
        recentResults: [
            { match: 'Team Spirit vs Gaimin', prediction: 'Team Spirit 68%', result: 'WIN', correct: true },
            { match: 'MOUZ vs Tundra', prediction: 'MOUZ 55%', result: 'WIN', correct: true },
            { match: 'XG vs BetBoom', prediction: 'XG 62%', result: 'LOSS', correct: false },
            { match: 'LGD vs IG', prediction: 'LGD 71%', result: 'WIN', correct: true },
            { match: 'Liquid vs Nigma', prediction: 'Liquid 58%', result: 'WIN', correct: true },
        ]
    };

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-16">
            {/* Header */}
            <div className="text-center mb-12">
                <h1 className="text-3xl sm:text-4xl font-bold text-stone-100 mb-4">
                    Prediction <span className="text-amber-500">Accuracy</span>
                </h1>
                <p className="text-stone-400 max-w-2xl mx-auto">
                    Track record of our ML predictions. We believe in transparency -
                    see exactly how well our model performs.
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
                <StatCard
                    label="This Week"
                    value={`${stats.thisWeek}%`}
                    subtext="Last 7 days"
                    highlight
                />
                <StatCard
                    label="This Month"
                    value={`${stats.thisMonth}%`}
                    subtext="Last 30 days"
                />
                <StatCard
                    label="All Time"
                    value={`${stats.overall}%`}
                    subtext="Since launch"
                />
                <StatCard
                    label="Total Predictions"
                    value={stats.totalPredictions.toLocaleString()}
                    subtext="Matches analyzed"
                />
            </div>

            {/* Accuracy Breakdown */}
            <div className="card-glass p-6 mb-12">
                <h2 className="text-xl font-semibold text-stone-200 mb-6">
                    Accuracy by Game Phase
                </h2>
                <div className="space-y-4">
                    <AccuracyBar label="Early Game (0-10 min)" value={58} />
                    <AccuracyBar label="Mid Game (10-25 min)" value={68} />
                    <AccuracyBar label="Late Game (25+ min)" value={82} />
                    <AccuracyBar label="With Clear Lead (>10k gold)" value={89} />
                </div>
                <div className="flex items-center gap-2 mt-4 text-stone-500 text-sm">
                    <IconBulb size={16} className="text-amber-500" />
                    <span>Tip: Wait for mid-game before placing bets for higher accuracy</span>
                </div>
            </div>

            {/* Recent Predictions */}
            <div className="card-glass p-6">
                <h2 className="text-xl font-semibold text-stone-200 mb-6">
                    Recent Predictions
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="text-left text-stone-500 text-sm border-b border-stone-700">
                                <th className="pb-3 font-medium">Match</th>
                                <th className="pb-3 font-medium">Our Prediction</th>
                                <th className="pb-3 font-medium">Result</th>
                            </tr>
                        </thead>
                        <tbody className="text-stone-300">
                            {stats.recentResults.map((r, i) => (
                                <tr key={i} className="border-b border-stone-800">
                                    <td className="py-3 text-sm">{r.match}</td>
                                    <td className="py-3 text-sm font-mono">{r.prediction}</td>
                                    <td className="py-3">
                                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${r.correct
                                                ? 'bg-emerald-500/20 text-emerald-400'
                                                : 'bg-rose-500/20 text-rose-400'
                                            }`}>
                                            {r.correct
                                                ? <IconCheck size={12} />
                                                : <IconCircleX size={12} />
                                            }
                                            {r.result}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Note */}
            <div className="mt-8 text-center">
                <p className="text-stone-500 text-sm">
                    Data updates every hour. Historical accuracy does not guarantee future results.
                </p>
            </div>
        </div>
    );
}

function StatCard({ label, value, subtext, highlight }: {
    label: string;
    value: string;
    subtext: string;
    highlight?: boolean;
}) {
    return (
        <div className={`card-glass p-6 text-center ${highlight ? 'border-amber-500/30' : ''}`}>
            <div className="text-stone-500 text-xs uppercase tracking-wider mb-2">{label}</div>
            <div className={`font-mono text-3xl font-bold mb-1 ${highlight ? 'text-amber-500' : 'text-stone-100'}`}>
                {value}
            </div>
            <div className="text-stone-600 text-xs">{subtext}</div>
        </div>
    );
}

function AccuracyBar({ label, value }: { label: string; value: number }) {
    return (
        <div>
            <div className="flex justify-between mb-1">
                <span className="text-stone-400 text-sm">{label}</span>
                <span className={`font-mono text-sm font-medium ${value >= 75 ? 'text-emerald-400' : value >= 60 ? 'text-amber-400' : 'text-stone-400'
                    }`}>
                    {value}%
                </span>
            </div>
            <div className="h-2 rounded-full bg-stone-800 overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${value >= 75
                            ? 'bg-gradient-to-r from-emerald-600 to-emerald-500'
                            : value >= 60
                                ? 'bg-gradient-to-r from-amber-600 to-amber-500'
                                : 'bg-gradient-to-r from-stone-600 to-stone-500'
                        }`}
                    style={{ width: `${value}%` }}
                />
            </div>
        </div>
    );
}

export default AccuracyPage;
