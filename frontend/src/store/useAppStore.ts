import { create } from 'zustand';

// Types matching backend StateManager output
export interface GameState {
    type: string;
    match_id: string | null;
    is_verified: boolean;
    game_time: number;
    gold_diff: number;
    xp_diff: number;
    networth_velocity: number;
    model_win_probability: number;
    market_implied_probability: number;
    market_odds_radiant: number;
    mispricing_index: number;
    draft_radiant_score: number;
    series_score_diff: number;
    is_mock_odds: boolean;
}

export interface AppState {
    // Connection
    connectionStatus: 'connected' | 'disconnected' | 'connecting';
    setConnectionStatus: (status: 'connected' | 'disconnected' | 'connecting') => void;

    // Game State
    gameState: GameState | null;
    updateGameState: (state: GameState) => void;

    // History for charts (last 60 seconds)
    probabilityHistory: { time: number; model: number; market: number }[];
    addProbabilityPoint: (time: number, model: number, market: number) => void;

    // UI State
    currentPage: 'dashboard' | 'analytics' | 'settings';
    setCurrentPage: (page: 'dashboard' | 'analytics' | 'settings') => void;
}

const MAX_HISTORY_POINTS = 60;

export const useAppStore = create<AppState>((set, get) => ({
    // Connection
    connectionStatus: 'connecting',
    setConnectionStatus: (status) => set({ connectionStatus: status }),

    // Game State
    gameState: null,
    updateGameState: (state) => {
        set({ gameState: state });
        // Also add to history
        if (state.game_time != null) {
            get().addProbabilityPoint(
                state.game_time,
                state.model_win_probability,
                state.market_implied_probability
            );
        }
    },

    // History
    probabilityHistory: [],
    addProbabilityPoint: (time, model, market) => {
        set((state) => {
            const newPoint = { time, model, market };
            const newHistory = [...state.probabilityHistory, newPoint];
            // Keep only last MAX_HISTORY_POINTS
            if (newHistory.length > MAX_HISTORY_POINTS) {
                return { probabilityHistory: newHistory.slice(-MAX_HISTORY_POINTS) };
            }
            return { probabilityHistory: newHistory };
        });
    },

    // UI State
    currentPage: 'dashboard',
    setCurrentPage: (page) => set({ currentPage: page }),
}));
