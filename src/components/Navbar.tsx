import { NavLink } from 'react-router-dom';
import { IconNewspaper, IconRefresh } from './icons';
import styles from './Navbar.module.css';

interface NavbarProps {
  updatedAt: string;
  loading:   boolean;
  onRefresh: () => void;
}

export default function Navbar({ updatedAt, loading, onRefresh }: NavbarProps) {
  return (
    <nav className={styles.navbar}>
      <div className={styles.inner}>
        <NavLink to="/" className={styles.brand}>
          <IconNewspaper size={20} />
          <span className={styles.brandText}>Última Hora Colombia</span>
        </NavLink>

        <div className={styles.right}>
          {updatedAt && !loading && (
            <span className={styles.status}>Actualizado: {updatedAt}</span>
          )}
          <button
            className={styles.refreshBtn}
            onClick={onRefresh}
            disabled={loading}
            title={loading ? 'Actualizando…' : 'Actualizar noticias'}
          >
            <IconRefresh size={15} className={loading ? styles.spin : undefined} />
            <span className={styles.refreshBtnText}>
              {loading ? 'Actualizando…' : 'Actualizar'}
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}
