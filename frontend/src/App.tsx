import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { MatchesPage } from './pages/MatchesPage';
import { MatchDetailPage } from './pages/MatchDetailPage';
import { AboutPage } from './pages/AboutPage';
import { AccuracyPage } from './pages/AccuracyPage';
import { TermsPage } from './pages/TermsPage';
import { ContactPage } from './pages/ContactPage';

/**
 * Chronosphere v3.0 - AI-Powered Dota 2 Match Predictions
 * 
 * Features:
 * - Smart landing with live/upcoming matches
 * - ML predictions with AI-powered analysis
 * - Trust-building accuracy stats
 * - Mobile-first responsive design
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="matches" element={<MatchesPage />} />
          <Route path="matches/:matchId" element={<MatchDetailPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="accuracy" element={<AccuracyPage />} />
          <Route path="terms" element={<TermsPage />} />
          <Route path="contact" element={<ContactPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
