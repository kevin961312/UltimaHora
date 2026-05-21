import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import SourcePage from './pages/SourcePage';
import { useNoticias } from './hooks/useNoticias';
import styles from './App.module.css';

export default function App() {
  const { data, loading, error, updatedAt } = useNoticias();

  return (
    <BrowserRouter basename="/UltimaHora">
      <div className={styles.layout}>
        <Navbar updatedAt={updatedAt} loading={loading} />
        <main className={styles.main}>
          <Routes>
            <Route path="/"      element={<HomePage   data={data} loading={loading} error={error} />} />
            <Route path="/:slug" element={<SourcePage data={data} />} />
            <Route path="*"      element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
