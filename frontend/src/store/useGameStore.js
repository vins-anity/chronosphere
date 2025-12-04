import { create } from 'zustand'

const useGameStore = create((set) => ({
    winProbability: 0.5, // Default 50%
    gameTime: 0,
    isConnected: false,
    lastUpdate: Date.now(),

    setWinProbability: (prob) => set({ winProbability: prob }),
    setGameTime: (time) => set({ gameTime: time }),
    setConnectionStatus: (status) => set({ isConnected: status }),
    updateLastTimestamp: () => set({ lastUpdate: Date.now() }),

    // Reset state
    reset: () => set({ winProbability: 0.5, gameTime: 0, isConnected: false })
}))

export default useGameStore
