/**
 * Terms & Conditions Page
 */
export function TermsPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-16">
            <h1 className="text-3xl font-bold text-stone-100 mb-8">
                Terms & Conditions
            </h1>

            <div className="prose prose-invert prose-stone max-w-none space-y-8">
                <Section title="1. Acceptance of Terms">
                    <p>
                        By accessing and using Chronosphere ("the Service"), you agree to be bound by these
                        Terms and Conditions. If you do not agree to these terms, do not use the Service.
                    </p>
                </Section>

                <Section title="2. Nature of Service">
                    <p>
                        Chronosphere provides predictions and analysis for Dota 2 esports matches using
                        machine learning and artificial intelligence. Our predictions are:
                    </p>
                    <ul className="list-disc pl-6 space-y-2 text-stone-400">
                        <li>For informational and entertainment purposes only</li>
                        <li>Not financial or gambling advice</li>
                        <li>Not guarantees of any outcome</li>
                        <li>Based on available data which may be incomplete or delayed</li>
                    </ul>
                </Section>

                <Section title="3. No Guarantee of Accuracy">
                    <p>
                        While we strive to provide accurate predictions, we make no warranty regarding:
                    </p>
                    <ul className="list-disc pl-6 space-y-2 text-stone-400">
                        <li>The accuracy of any prediction</li>
                        <li>The reliability of data sources</li>
                        <li>The availability of the service</li>
                        <li>Future prediction performance</li>
                    </ul>
                    <p className="text-amber-500 font-medium">
                        Past performance does not guarantee future results.
                    </p>
                </Section>

                <Section title="4. Gambling Disclaimer">
                    <p>
                        Chronosphere does not facilitate gambling or betting directly. We do not:
                    </p>
                    <ul className="list-disc pl-6 space-y-2 text-stone-400">
                        <li>Accept bets or wagers</li>
                        <li>Process payments for gambling</li>
                        <li>Endorse any betting platform</li>
                        <li>Guarantee profits from betting</li>
                    </ul>
                    <p>
                        If you choose to use our predictions for betting, you do so at your own risk.
                        Gambling laws vary by jurisdiction. It is your responsibility to ensure compliance
                        with local laws.
                    </p>
                </Section>

                <Section title="5. User Responsibilities">
                    <p>You agree to:</p>
                    <ul className="list-disc pl-6 space-y-2 text-stone-400">
                        <li>Use the Service legally and responsibly</li>
                        <li>Not use the Service if underage for gambling in your jurisdiction</li>
                        <li>Seek help if you have gambling problems</li>
                        <li>Make your own decisions regarding betting</li>
                    </ul>
                </Section>

                <Section title="6. Intellectual Property">
                    <p>
                        All content on Chronosphere, including but not limited to predictions, analysis,
                        design, and code, is the property of Chronosphere and is protected by intellectual
                        property laws. You may not reproduce, distribute, or create derivative works without
                        express permission.
                    </p>
                </Section>

                <Section title="7. Limitation of Liability">
                    <p>
                        To the maximum extent permitted by law, Chronosphere and its operators shall not be
                        liable for any direct, indirect, incidental, consequential, or punitive damages
                        arising from your use of the Service, including but not limited to:
                    </p>
                    <ul className="list-disc pl-6 space-y-2 text-stone-400">
                        <li>Financial losses from betting</li>
                        <li>Data inaccuracies or delays</li>
                        <li>Service interruptions</li>
                        <li>Decisions made based on our predictions</li>
                    </ul>
                </Section>

                <Section title="8. Changes to Terms">
                    <p>
                        We reserve the right to modify these terms at any time. Continued use of the Service
                        after changes constitutes acceptance of the new terms.
                    </p>
                </Section>

                <Section title="9. Contact">
                    <p>
                        For questions about these terms, please contact us through our{' '}
                        <a href="/contact" className="text-amber-500 hover:text-amber-400">contact page</a>.
                    </p>
                </Section>

                <div className="pt-8 border-t border-stone-700">
                    <p className="text-stone-500 text-sm">
                        Last updated: December 2024
                    </p>
                </div>
            </div>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section>
            <h2 className="text-xl font-semibold text-stone-200 mb-4">{title}</h2>
            <div className="text-stone-400 space-y-4">
                {children}
            </div>
        </section>
    );
}

export default TermsPage;
