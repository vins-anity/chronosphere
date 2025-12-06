import { useState } from 'react';
import {
    IconBug,
    IconBulb,
    IconMessageCircle,
    IconCheck,
    IconMail,
    IconBrandDiscord,
    IconBrandTwitter,
    IconHeart,
    IconSend,
} from '../components/Icons';

/**
 * Contact & Bug Report Page
 */
export function ContactPage() {
    const [formType, setFormType] = useState<'bug' | 'feature' | 'general'>('bug');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitted(true);
        setTimeout(() => setSubmitted(false), 5000);
    };

    const getFormIcon = () => {
        switch (formType) {
            case 'bug': return <IconBug size={18} />;
            case 'feature': return <IconBulb size={18} />;
            case 'general': return <IconMessageCircle size={18} />;
        }
    };

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-16">
            {/* Header */}
            <div className="text-center mb-12">
                <h1 className="text-3xl sm:text-4xl font-bold text-stone-100 mb-4">
                    Contact <span className="text-amber-500">Us</span>
                </h1>
                <p className="text-stone-400 max-w-xl mx-auto">
                    Report a bug, request a feature, or just say hello.
                    We appreciate all feedback!
                </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-8">
                {/* Form */}
                <div className="lg:col-span-2">
                    <div className="card-glass p-6">
                        {/* Form Type Tabs */}
                        <div className="flex gap-2 mb-6">
                            <FormTab
                                icon={<IconBug size={16} />}
                                label="Bug Report"
                                active={formType === 'bug'}
                                onClick={() => setFormType('bug')}
                            />
                            <FormTab
                                icon={<IconBulb size={16} />}
                                label="Feature Request"
                                active={formType === 'feature'}
                                onClick={() => setFormType('feature')}
                            />
                            <FormTab
                                icon={<IconMessageCircle size={16} />}
                                label="General"
                                active={formType === 'general'}
                                onClick={() => setFormType('general')}
                            />
                        </div>

                        {submitted ? (
                            <div className="text-center py-12">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                    <IconCheck size={32} className="text-emerald-400" />
                                </div>
                                <h3 className="text-xl font-semibold text-stone-100 mb-2">
                                    Thank you for your feedback!
                                </h3>
                                <p className="text-stone-400">
                                    We'll review your message and get back to you if needed.
                                </p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4">
                                {/* Email */}
                                <div>
                                    <label className="block text-stone-300 text-sm font-medium mb-2">
                                        Email (optional)
                                    </label>
                                    <input
                                        type="email"
                                        placeholder="your@email.com"
                                        className="w-full px-4 py-3 rounded-lg bg-stone-800 border border-stone-700 text-stone-100 placeholder-stone-500 focus:outline-none focus:border-amber-500 transition-colors"
                                    />
                                </div>

                                {/* Subject */}
                                <div>
                                    <label className="block text-stone-300 text-sm font-medium mb-2">
                                        {formType === 'bug' ? 'What went wrong?' : formType === 'feature' ? 'What would you like to see?' : 'Subject'}
                                    </label>
                                    <input
                                        type="text"
                                        required
                                        placeholder={
                                            formType === 'bug'
                                                ? 'Brief description of the issue'
                                                : formType === 'feature'
                                                    ? 'Your feature idea'
                                                    : 'What can we help with?'
                                        }
                                        className="w-full px-4 py-3 rounded-lg bg-stone-800 border border-stone-700 text-stone-100 placeholder-stone-500 focus:outline-none focus:border-amber-500 transition-colors"
                                    />
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-stone-300 text-sm font-medium mb-2">
                                        {formType === 'bug' ? 'Steps to reproduce' : 'Details'}
                                    </label>
                                    <textarea
                                        required
                                        rows={5}
                                        placeholder={
                                            formType === 'bug'
                                                ? '1. Go to...\n2. Click on...\n3. See error...'
                                                : 'Tell us more...'
                                        }
                                        className="w-full px-4 py-3 rounded-lg bg-stone-800 border border-stone-700 text-stone-100 placeholder-stone-500 focus:outline-none focus:border-amber-500 transition-colors resize-none"
                                    />
                                </div>

                                {/* Submit */}
                                <button
                                    type="submit"
                                    className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-stone-900 font-medium rounded-lg transition-colors"
                                >
                                    <IconSend size={18} />
                                    Submit {formType === 'bug' ? 'Bug Report' : formType === 'feature' ? 'Feature Request' : 'Message'}
                                </button>
                            </form>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Quick Contact */}
                    <div className="card-glass p-6">
                        <h3 className="text-lg font-semibold text-stone-200 mb-4">
                            Quick Contact
                        </h3>
                        <div className="space-y-3">
                            <a
                                href="mailto:support@chronosphere.gg"
                                className="flex items-center gap-3 text-stone-400 hover:text-amber-500 transition-colors"
                            >
                                <IconMail size={20} className="text-stone-500" />
                                support@chronosphere.gg
                            </a>
                            <a
                                href="https://discord.gg/chronosphere"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 text-stone-400 hover:text-amber-500 transition-colors"
                            >
                                <IconBrandDiscord size={20} className="text-stone-500" />
                                Discord Community
                            </a>
                            <a
                                href="https://twitter.com/chronosphere_gg"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 text-stone-400 hover:text-amber-500 transition-colors"
                            >
                                <IconBrandTwitter size={20} className="text-stone-500" />
                                @chronosphere_gg
                            </a>
                        </div>
                    </div>

                    {/* Support Us */}
                    <div className="card-glass p-6 text-center">
                        <h3 className="text-lg font-semibold text-stone-200 mb-2">
                            Support Chronosphere
                        </h3>
                        <p className="text-stone-400 text-sm mb-4">
                            Help us keep the servers running and improve our predictions!
                        </p>
                        <a
                            href="https://ko-fi.com/chronosphere"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white font-medium rounded-lg transition-all"
                        >
                            <IconHeart size={18} className="fill-current" />
                            Donate on Ko-fi
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}

function FormTab({ icon, label, active, onClick }: {
    icon: React.ReactNode;
    label: string;
    active: boolean;
    onClick: () => void
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${active
                    ? 'bg-amber-500 text-stone-900'
                    : 'bg-stone-800 text-stone-400 hover:bg-stone-700'
                }`}
        >
            {icon}
            {label}
        </button>
    );
}

export default ContactPage;
