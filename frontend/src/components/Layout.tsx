import { Outlet, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { IconMenu2, IconX, IconHeart } from './Icons';

/**
 * Main Layout Component
 * - Sticky header with navigation
 * - Mobile hamburger menu
 * - Footer with links and donation
 */
export function Layout() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [liveCount, setLiveCount] = useState(0);
    const location = useLocation();

    // Close mobile menu on route change
    useEffect(() => {
        setMobileMenuOpen(false);
    }, [location]);

    // Fetch live match count
    useEffect(() => {
        const fetchLiveCount = async () => {
            try {
                const res = await fetch('/api/v1/matches/live/pro');
                if (res.ok) {
                    const data = await res.json();
                    setLiveCount(data.length);
                }
            } catch (e) {
                console.error('Failed to fetch live count:', e);
            }
        };
        fetchLiveCount();
        const interval = setInterval(fetchLiveCount, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen flex flex-col bg-stone-900">
            {/* Header */}
            <header className="sticky top-0 z-50 bg-stone-900/95 backdrop-blur-md border-b border-stone-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <Link to="/" className="flex items-center gap-2.5">
                            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
                                <span className="text-white font-bold text-lg">C</span>
                            </div>
                            <span className="text-xl font-semibold text-stone-100 hidden sm:block">
                                Chronosphere
                            </span>
                        </Link>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center gap-1">
                            <NavLink to="/" label="Home" />
                            <NavLink to="/matches" label="Matches" badge={liveCount > 0 ? `${liveCount} Live` : undefined} />
                            <NavLink to="/accuracy" label="Accuracy" />
                            <NavLink to="/about" label="About" />
                        </nav>

                        {/* Mobile Menu Button */}
                        <button
                            className="md:hidden p-2 rounded-lg text-stone-400 hover:text-stone-100 hover:bg-stone-800 transition-colors"
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        >
                            {mobileMenuOpen ? (
                                <IconX size={24} />
                            ) : (
                                <IconMenu2 size={24} />
                            )}
                        </button>
                    </div>
                </div>

                {/* Mobile Navigation */}
                {mobileMenuOpen && (
                    <div className="md:hidden border-t border-stone-800 bg-stone-900/98 backdrop-blur-md animate-fade-in">
                        <nav className="px-4 py-4 space-y-2">
                            <MobileNavLink to="/" label="Home" />
                            <MobileNavLink to="/matches" label="Matches" badge={liveCount > 0 ? `${liveCount} Live` : undefined} />
                            <MobileNavLink to="/accuracy" label="Accuracy" />
                            <MobileNavLink to="/about" label="About" />
                            <MobileNavLink to="/contact" label="Contact" />
                        </nav>
                    </div>
                )}
            </header>

            {/* Main Content */}
            <main className="flex-1">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="border-t border-stone-800 bg-stone-900/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                        {/* Brand */}
                        <div className="md:col-span-2">
                            <div className="flex items-center gap-2.5 mb-4">
                                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                                    <span className="text-white font-bold text-lg">C</span>
                                </div>
                                <span className="text-xl font-semibold text-stone-100">Chronosphere</span>
                            </div>
                            <p className="text-stone-400 text-sm max-w-md">
                                AI-powered Dota 2 match predictions using machine learning and real-time data analysis.
                                Make informed decisions with confidence.
                            </p>
                        </div>

                        {/* Links */}
                        <div>
                            <h4 className="text-stone-200 font-medium mb-4">Navigation</h4>
                            <ul className="space-y-2">
                                <li><Link to="/matches" className="text-stone-400 hover:text-amber-500 text-sm transition-colors">Live Matches</Link></li>
                                <li><Link to="/accuracy" className="text-stone-400 hover:text-amber-500 text-sm transition-colors">Accuracy Stats</Link></li>
                                <li><Link to="/about" className="text-stone-400 hover:text-amber-500 text-sm transition-colors">How It Works</Link></li>
                            </ul>
                        </div>

                        {/* Legal & Support */}
                        <div>
                            <h4 className="text-stone-200 font-medium mb-4">Support</h4>
                            <ul className="space-y-2">
                                <li><Link to="/contact" className="text-stone-400 hover:text-amber-500 text-sm transition-colors">Contact & Bug Report</Link></li>
                                <li><Link to="/terms" className="text-stone-400 hover:text-amber-500 text-sm transition-colors">Terms & Conditions</Link></li>
                                <li>
                                    <a
                                        href="https://ko-fi.com/chronosphere"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1.5 text-amber-500 hover:text-amber-400 text-sm transition-colors"
                                    >
                                        <IconHeart size={14} className="fill-current" />
                                        Support Us
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>

                    {/* Bottom */}
                    <div className="mt-12 pt-8 border-t border-stone-800 flex flex-col sm:flex-row justify-between items-center gap-4">
                        <p className="text-stone-500 text-sm">
                            © {new Date().getFullYear()} Chronosphere. Predictions are not gambling advice.
                        </p>
                        <p className="text-stone-600 text-xs">
                            Powered by professional esports data & AI analysis
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}

// Desktop Nav Link
function NavLink({ to, label, badge }: { to: string; label: string; badge?: string }) {
    const location = useLocation();
    const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

    return (
        <Link
            to={to}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2
        ${isActive
                    ? 'bg-stone-800 text-amber-500'
                    : 'text-stone-300 hover:text-stone-100 hover:bg-stone-800/50'
                }`}
        >
            {label}
            {badge && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">
                    {badge}
                </span>
            )}
        </Link>
    );
}

// Mobile Nav Link
function MobileNavLink({ to, label, badge }: { to: string; label: string; badge?: string }) {
    const location = useLocation();
    const isActive = location.pathname === to;

    return (
        <Link
            to={to}
            className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors flex items-center justify-between
        ${isActive
                    ? 'bg-stone-800 text-amber-500'
                    : 'text-stone-300 hover:text-stone-100 hover:bg-stone-800/50'
                }`}
        >
            {label}
            {badge && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">
                    {badge}
                </span>
            )}
        </Link>
    );
}
