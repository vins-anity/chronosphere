import { useState } from 'react';
import {
    IconChartBar,
    IconBrain,
    IconRobot,
    IconShield,
    IconDatabase,
    IconBolt,
    IconClock,
    IconTarget,
    IconChevronDown,
    IconTrendingUp,
    IconUsersGroup,
    IconArrowRight,
} from '../components/Icons';

/**
 * About Page - Trust-building with methodology explanation
 */
export function AboutPage() {
    return (
        <div className="min-h-screen">
            {/* Hero */}
            <section className="relative overflow-hidden py-16 sm:py-24">
                <div className="absolute inset-0 bg-gradient-to-b from-amber-500/5 via-transparent to-transparent pointer-events-none" />
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-4xl sm:text-5xl font-bold text-stone-100 mb-6">
                        AI-Powered <span className="text-amber-500">Predictions</span>
                    </h1>
                    <p className="text-xl text-stone-400 max-w-2xl mx-auto">
                        Chronosphere combines machine learning, real-time data, and AI analysis
                        to help you make informed betting decisions on Dota 2 matches.
                    </p>
                </div>
            </section>

            {/* How It Works */}
            <section className="py-16 border-t border-stone-800">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-stone-100 text-center mb-12">
                        How It Works
                    </h2>

                    <div className="grid md:grid-cols-3 gap-8 mb-12">
                        <StepCard
                            number="1"
                            icon={<IconDatabase size={28} className="text-amber-500" />}
                            title="Data Collection"
                            description="We aggregate real-time data from multiple professional esports sources to build a complete picture of each match."
                        />
                        <StepCard
                            number="2"
                            icon={<IconBrain size={28} className="text-amber-500" />}
                            title="ML Analysis"
                            description="Our proprietary machine learning model processes dozens of signals to generate calibrated win probabilities."
                        />
                        <StepCard
                            number="3"
                            icon={<IconRobot size={28} className="text-amber-500" />}
                            title="AI Insights"
                            description="Advanced AI explains the prediction in plain language, highlighting key factors you should consider."
                        />
                    </div>

                    {/* Data Flow */}
                    <div className="card-glass p-8">
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
                            <DataSource icon={<IconBolt size={20} />} name="Live Data" desc="Real-time match state" />
                            <IconArrowRight className="text-amber-500 hidden sm:block" size={20} />
                            <DataSource icon={<IconUsersGroup size={20} />} name="Historical Data" desc="Team & player stats" />
                            <IconArrowRight className="text-amber-500 hidden sm:block" size={20} />
                            <DataSource icon={<IconBrain size={20} />} name="ML Engine" desc="Win probability" />
                            <IconArrowRight className="text-amber-500 hidden sm:block" size={20} />
                            <DataSource icon={<IconRobot size={20} />} name="AI Layer" desc="Natural insights" />
                        </div>
                    </div>
                </div>
            </section>

            {/* Why Trust Us */}
            <section className="py-16 bg-stone-900/50 border-t border-stone-800">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-stone-100 text-center mb-12">
                        Why Trust Our Predictions
                    </h2>

                    <div className="space-y-6">
                        <TechDetail
                            icon={<IconShield size={24} className="text-amber-500" />}
                            title="Proprietary ML Model"
                            description="Our prediction engine is built on years of Dota 2 data analysis. We've engineered a custom model specifically optimized for esports betting scenarios."
                        />
                        <TechDetail
                            icon={<IconChartBar size={24} className="text-amber-500" />}
                            title="Multi-Signal Analysis"
                            description="We don't rely on just one or two stats. Our system analyzes dozens of factors simultaneously - from live game state to historical performance patterns."
                        />
                        <TechDetail
                            icon={<IconTarget size={24} className="text-amber-500" />}
                            title="Calibrated Probabilities"
                            description="When we say 70% win probability, we mean it. Our predictions are calibrated against historical outcomes to ensure accuracy you can trust."
                        />
                        <TechDetail
                            icon={<IconClock size={24} className="text-amber-500" />}
                            title="Real-Time Updates"
                            description="Predictions update every 15 seconds during live matches. As the game evolves, so does our analysis."
                        />
                    </div>
                </div>
            </section>

            {/* Data Sources */}
            <section className="py-16 border-t border-stone-800">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-stone-100 text-center mb-12">
                        Our Data Sources
                    </h2>

                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        <SourceCard
                            icon={<IconBolt size={28} className="text-amber-500" />}
                            name="Live Match API"
                            description="Official game data providing real-time match state, player stats, and networth data."
                        />
                        <SourceCard
                            icon={<IconTrendingUp size={28} className="text-amber-500" />}
                            name="Historical Stats"
                            description="Team statistics, match history, and player performance data from community APIs."
                        />
                        <SourceCard
                            icon={<IconUsersGroup size={28} className="text-amber-500" />}
                            name="Esports Data"
                            description="Professional esports data including league info, tournament brackets, and team metadata."
                        />
                        <SourceCard
                            icon={<IconRobot size={28} className="text-amber-500" />}
                            name="AI Analysis"
                            description="Advanced language model providing natural language analysis and insights."
                        />
                    </div>
                </div>
            </section>

            {/* FAQ */}
            <section className="py-16 bg-stone-900/50 border-t border-stone-800">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-stone-100 text-center mb-12">
                        Frequently Asked Questions
                    </h2>

                    <div className="space-y-4">
                        <FAQItem
                            question="How accurate are your predictions?"
                            answer="Our model's accuracy varies by game phase. Early game predictions (0-10 min) are less reliable (~55-60% accuracy) as the game state is still forming. Mid-game (15-25 min) predictions reach 65-70% accuracy, and late-game predictions with clear leads can exceed 80% accuracy. We recommend waiting for mid-game before placing bets."
                        />
                        <FAQItem
                            question="Do you guarantee wins?"
                            answer="No. Dota 2 is inherently unpredictable and comebacks happen. Our predictions are probabilities, not certainties. A 70% win probability means the team is expected to win 7 out of 10 similar situations - but the other 3 happen too. Only bet what you can afford to lose."
                        />
                        <FAQItem
                            question="What is an 'Edge Signal'?"
                            answer="An edge signal indicates when our prediction significantly differs from typical betting odds. 'STRONG VALUE' (65%+ probability) suggests high confidence in our prediction. 'LEAN' (55-65%) indicates a slight advantage. 'SKIP' means the game is too close to recommend a bet."
                        />
                        <FAQItem
                            question="Why use AI analysis on top of ML?"
                            answer="The ML model outputs a probability, but doesn't explain why. The AI analyst interprets the raw data and features to provide human-readable context - like explaining that a team's carry has been dominating, or warning that the enemy has a strong late-game lineup."
                        />
                        <FAQItem
                            question="Is this legal?"
                            answer="Chronosphere provides predictions and analysis - we don't facilitate gambling directly. Betting laws vary by jurisdiction. It's your responsibility to ensure you're complying with local laws. We don't condone underage or problem gambling."
                        />
                    </div>
                </div>
            </section>

            {/* Disclaimer */}
            <section className="py-8 border-t border-stone-800">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <p className="text-stone-500 text-sm">
                        ⚠️ <strong>Disclaimer:</strong> Chronosphere predictions are for informational purposes only.
                        They are not gambling advice. Past performance does not guarantee future results.
                        Please gamble responsibly.
                    </p>
                </div>
            </section>
        </div>
    );
}

function StepCard({ number, icon, title, description }: {
    number: string;
    icon: React.ReactNode;
    title: string;
    description: string;
}) {
    return (
        <div className="card-glass p-6 text-center relative">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center text-stone-900 font-bold text-sm">
                {number}
            </div>
            <div className="w-14 h-14 mx-auto mb-4 mt-2 rounded-xl bg-amber-500/10 flex items-center justify-center">
                {icon}
            </div>
            <h3 className="text-lg font-semibold text-stone-100 mb-2">{title}</h3>
            <p className="text-stone-400 text-sm">{description}</p>
        </div>
    );
}

function DataSource({ icon, name, desc }: { icon: React.ReactNode; name: string; desc: string }) {
    return (
        <div className="text-center flex flex-col items-center">
            <div className="w-10 h-10 rounded-lg bg-stone-800 flex items-center justify-center mb-2 text-stone-400">
                {icon}
            </div>
            <div className="text-stone-200 font-medium text-sm">{name}</div>
            <div className="text-stone-500 text-xs">{desc}</div>
        </div>
    );
}

function TechDetail({ icon, title, description }: {
    icon: React.ReactNode;
    title: string;
    description: string
}) {
    return (
        <div className="card-glass p-6 flex gap-4">
            <div className="w-12 h-12 shrink-0 rounded-xl bg-amber-500/10 flex items-center justify-center">
                {icon}
            </div>
            <div>
                <h3 className="text-lg font-semibold text-stone-100 mb-1">{title}</h3>
                <p className="text-stone-400">{description}</p>
            </div>
        </div>
    );
}

function SourceCard({ icon, name, description }: {
    icon: React.ReactNode;
    name: string;
    description: string
}) {
    return (
        <div className="card-glass p-6 text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-amber-500/10 flex items-center justify-center">
                {icon}
            </div>
            <h3 className="text-lg font-semibold text-stone-100 mb-2">{name}</h3>
            <p className="text-stone-400 text-sm">{description}</p>
        </div>
    );
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
    const [open, setOpen] = useState(false);

    return (
        <div className="card-glass overflow-hidden">
            <button
                onClick={() => setOpen(!open)}
                className="w-full p-4 flex items-center justify-between text-left"
            >
                <span className="font-medium text-stone-200">{question}</span>
                <IconChevronDown
                    size={20}
                    className={`text-amber-500 transition-transform ${open ? 'rotate-180' : ''}`}
                />
            </button>
            {open && (
                <div className="px-4 pb-4 text-stone-400 text-sm animate-fade-in">
                    {answer}
                </div>
            )}
        </div>
    );
}

export default AboutPage;
