import React, { useEffect, useState } from 'react'
import useGameStore from '../store/useGameStore'
import useWebSocket from '../hooks/useWebSocket'

const Dashboard = () => {
    // Connect to WebSocket
    useWebSocket('ws://localhost:8001/ws/live') // Port 8001 as used in verify_pipeline, or 8000? verify_pipeline used 8001.
    // Let's assume we run uvicorn on 8000 for dev.
    // Actually, let's stick to 8000 for standard dev.

    const { winProbability, gameTime, isConnected, lastUpdate } = useGameStore()
    const [isDead, setIsDead] = useState(false)

    // Deadman Switch Logic
    useEffect(() => {
        const interval = setInterval(() => {
            if (Date.now() - lastUpdate > 2000 && isConnected) {
                setIsDead(true)
            } else {
                setIsDead(false)
            }
        }, 1000)
        return () => clearInterval(interval)
    }, [lastUpdate, isConnected])

    // Format Win Probability
    const radiantWin = (winProbability * 100).toFixed(1)
    const direWin = (100 - (winProbability * 100)).toFixed(1)

    // Dynamic Color
    const getWinColor = (prob) => {
        if (prob > 0.6) return 'text-success' // Radiant winning
        if (prob < 0.4) return 'text-error'   // Dire winning (Radiant losing)
        return 'text-warning'                 // Even
    }

    return (
        <div className="min-h-screen bg-base-200 flex flex-col items-center justify-center p-4 font-sans">

            {/* Header / Status */}
            <div className="absolute top-4 right-4 flex gap-2">
                <div className={`badge ${isConnected ? 'badge-success' : 'badge-error'} gap-2`}>
                    {isConnected ? 'LIVE' : 'OFFLINE'}
                </div>
                {isDead && <div className="badge badge-warning animate-pulse">NO DATA</div>}
            </div>

            <div className="card w-full max-w-3xl bg-base-100 shadow-xl">
                <div className="card-body text-center">
                    <h2 className="card-title justify-center text-4xl mb-8">Chronosphere Lite</h2>

                    {/* Win Probability Display */}
                    <div className="flex justify-between items-center mb-12">
                        <div className="text-left">
                            <p className="text-sm uppercase tracking-widest opacity-70">Radiant</p>
                            <p className={`text-6xl font-black ${getWinColor(winProbability)}`}>{radiantWin}%</p>
                        </div>

                        <div className="divider divider-horizontal">VS</div>

                        <div className="text-right">
                            <p className="text-sm uppercase tracking-widest opacity-70">Dire</p>
                            <p className={`text-6xl font-black ${getWinColor(1 - winProbability)}`}>{direWin}%</p>
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <progress
                        className="progress progress-success w-full h-4"
                        value={winProbability * 100}
                        max="100"
                    ></progress>

                    {/* Game Info */}
                    <div className="stats shadow mt-8">
                        <div className="stat">
                            <div className="stat-title">Game Time</div>
                            <div className="stat-value font-mono">{gameTime}</div>
                            <div className="stat-desc">Seconds</div>
                        </div>

                        <div className="stat">
                            <div className="stat-title">Confidence</div>
                            <div className="stat-value">High</div>
                            <div className="stat-desc">Model v1.0</div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    )
}

export default Dashboard
