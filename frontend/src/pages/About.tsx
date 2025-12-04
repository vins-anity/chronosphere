import React from 'react';

const About: React.FC = () => {
    return (
        <div className="hero min-h-screen bg-base-200">
            <div className="hero-content text-center">
                <div className="max-w-md">
                    <h1 className="text-5xl font-bold">Chronosphere</h1>
                    <p className="py-6">
                        Real-time Dota 2 game state ingestion and analysis platform.
                        Predict win probabilities and visualize game data instantly.
                    </p>
                    <div className="stats shadow">
                        <div className="stat">
                            <div className="stat-title">Tech Stack</div>
                            <div className="stat-value text-primary">Modern</div>
                            <div className="stat-desc">React, Vite, Python, SQLModel</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default About;
