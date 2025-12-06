import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../store/useAppStore';

// Match the actual backend payload structure
interface PredictionData {
    type?: string;
    match_id?: string;
    game_time: number;
    gold_diff: number;
    xp_diff: number;
    networth_velocity: number;
    model_win_probability: number;
    market_implied_probability: number;
    mispricing_index: number;
    is_mock_odds?: boolean;
}

export default function SpectatePage({ onBack }: { onBack: () => void }) {
    const { connectionStatus, setConnectionStatus } = useAppStore();
    const wsRef = useRef<WebSocket | null>(null);
    const [prediction, setPrediction] = useState<PredictionData | null>(null);

    // WebSocket connection
    useEffect(() => {
        const wsUrl = `ws://localhost:8000/ws/live`;
        console.log('Connecting to WebSocket:', wsUrl);

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnectionStatus('connected');
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnectionStatus('disconnected');
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnectionStatus('disconnected');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Received prediction:', data);

                // Only process valid update messages
                if (data.type === 'update' && data.model_win_probability !== undefined) {
                    setPrediction(data);
                }
            } catch (err) {
                console.error('Error parsing WebSocket message:', err);
            }
        };

        return () => {
            ws.close();
            wsRef.current = null;
        };
    }, [setConnectionStatus]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(Math.abs(seconds) / 60);
        const secs = Math.abs(seconds) % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Map backend field names to display values
    const radiantProb = prediction?.model_win_probability ?? 0.5;
    const direProb = 1 - radiantProb;

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            padding: '2rem',
            color: '#fff',
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '2rem',
            }}>
                <button
                    onClick={onBack}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '8px',
                        color: '#fff',
                        padding: '0.5rem 1rem',
                        cursor: 'pointer',
                        fontSize: '0.9rem',
                    }}
                >
                    ← Back to Matches
                </button>

                <h1 style={{
                    fontSize: '2rem',
                    fontWeight: 'bold',
                    background: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                }}>
                    SPECTATE MODE
                </h1>

                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 1rem',
                    background: connectionStatus === 'connected' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    borderRadius: '20px',
                    fontSize: '0.85rem',
                }}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: connectionStatus === 'connected' ? '#22c55e' : '#ef4444',
                        animation: connectionStatus === 'connected' ? 'pulse 2s infinite' : 'none',
                    }} />
                    {connectionStatus === 'connected' ? 'LIVE' : 'OFFLINE'}
                </div>
            </div>

            {/* Main Content */}
            {!prediction ? (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '60vh',
                    gap: '1.5rem',
                }}>
                    <div style={{
                        width: '60px',
                        height: '60px',
                        border: '4px solid rgba(251, 191, 36, 0.3)',
                        borderTopColor: '#fbbf24',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                    }} />
                    <h2 style={{ fontSize: '1.5rem', color: '#888' }}>Waiting for GSI data...</h2>
                    <p style={{ color: '#666', maxWidth: '400px', textAlign: 'center' }}>
                        Run the GSI simulation or spectate a live Dota 2 match to see predictions here.
                    </p>
                    <code style={{
                        background: 'rgba(0,0,0,0.3)',
                        padding: '1rem',
                        borderRadius: '8px',
                        color: '#fbbf24',
                    }}>
                        uv run python simulate_gsi.py
                    </code>
                </div>
            ) : (
                <>
                    {/* Win Probability Display */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr auto 1fr',
                        gap: '2rem',
                        alignItems: 'center',
                        marginBottom: '2rem',
                    }}>
                        {/* Radiant */}
                        <div style={{
                            textAlign: 'center',
                            padding: '2rem',
                            background: 'rgba(34, 197, 94, 0.1)',
                            borderRadius: '16px',
                            border: '1px solid rgba(34, 197, 94, 0.3)',
                        }}>
                            <div style={{ color: '#22c55e', fontSize: '1rem', marginBottom: '0.5rem' }}>
                                RADIANT
                            </div>
                            <div style={{
                                fontSize: '4rem',
                                fontWeight: 'bold',
                                color: '#22c55e',
                            }}>
                                {(radiantProb * 100).toFixed(1)}%
                            </div>
                        </div>

                        {/* VS */}
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '0.5rem',
                        }}>
                            <div style={{ fontSize: '1.5rem', color: '#666' }}>VS</div>
                            <div style={{
                                fontSize: '2rem',
                                fontWeight: 'bold',
                                color: '#fbbf24',
                            }}>
                                {formatTime(prediction.game_time || 0)}
                            </div>
                        </div>

                        {/* Dire */}
                        <div style={{
                            textAlign: 'center',
                            padding: '2rem',
                            background: 'rgba(239, 68, 68, 0.1)',
                            borderRadius: '16px',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                        }}>
                            <div style={{ color: '#ef4444', fontSize: '1rem', marginBottom: '0.5rem' }}>
                                DIRE
                            </div>
                            <div style={{
                                fontSize: '4rem',
                                fontWeight: 'bold',
                                color: '#ef4444',
                            }}>
                                {(direProb * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>

                    {/* Probability Bar */}
                    <div style={{
                        height: '24px',
                        background: '#1f2937',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        marginBottom: '2rem',
                    }}>
                        <div style={{
                            height: '100%',
                            width: `${radiantProb * 100}%`,
                            background: 'linear-gradient(90deg, #22c55e, #16a34a)',
                            borderRadius: '12px',
                            transition: 'width 0.5s ease-out',
                        }} />
                    </div>

                    {/* Stats Grid */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: '1.5rem',
                        marginBottom: '2rem',
                    }}>
                        <StatCard
                            label="Gold Diff"
                            value={prediction.gold_diff || 0}
                            format="gold"
                        />
                        <StatCard
                            label="XP Diff"
                            value={prediction.xp_diff || 0}
                            format="xp"
                        />
                        <StatCard
                            label="Velocity"
                            value={prediction.velocity || 0}
                            format="velocity"
                        />
                        <StatCard
                            label="Confidence"
                            value={prediction.confidence || 'N/A'}
                            format="confidence"
                        />
                    </div>

                    {/* Value Signal (if market data available) */}
                    {prediction.value_signal && (
                        <div style={{
                            padding: '1.5rem',
                            background: prediction.value_signal.includes('RADIANT')
                                ? 'rgba(34, 197, 94, 0.2)'
                                : prediction.value_signal.includes('DIRE')
                                    ? 'rgba(239, 68, 68, 0.2)'
                                    : 'rgba(128, 128, 128, 0.2)',
                            borderRadius: '12px',
                            textAlign: 'center',
                            marginBottom: '2rem',
                        }}>
                            <div style={{ fontSize: '0.9rem', color: '#888', marginBottom: '0.5rem' }}>
                                VALUE SIGNAL
                            </div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                                {prediction.value_signal}
                            </div>
                            {prediction.mispricing_index !== undefined && (
                                <div style={{ fontSize: '0.9rem', color: '#888', marginTop: '0.5rem' }}>
                                    Mispricing: {(prediction.mispricing_index * 100).toFixed(1)}%
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* CSS Animations */}
            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
        </div>
    );
}

function StatCard({ label, value, format }: {
    label: string;
    value: number | string;
    format: 'gold' | 'xp' | 'velocity' | 'confidence';
}) {
    let displayValue: string;
    let color = '#fff';

    if (format === 'gold') {
        const num = value as number;
        displayValue = `${num >= 0 ? '+' : ''}${num.toLocaleString()}`;
        color = num >= 0 ? '#22c55e' : '#ef4444';
    } else if (format === 'xp') {
        const num = value as number;
        displayValue = `${num >= 0 ? '+' : ''}${num.toLocaleString()}`;
        color = num >= 0 ? '#22c55e' : '#ef4444';
    } else if (format === 'velocity') {
        const num = value as number;
        displayValue = `${num >= 0 ? '+' : ''}${num.toFixed(1)}`;
        color = num >= 0 ? '#22c55e' : '#ef4444';
    } else {
        displayValue = String(value).toUpperCase();
        color = value === 'high' ? '#22c55e' : value === 'medium' ? '#eab308' : '#ef4444';
    }

    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '12px',
            padding: '1.5rem',
            textAlign: 'center',
        }}>
            <div style={{ color: '#888', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                {label}
            </div>
            <div style={{ color, fontSize: '1.5rem', fontWeight: 'bold' }}>
                {displayValue}
            </div>
        </div>
    );
}
