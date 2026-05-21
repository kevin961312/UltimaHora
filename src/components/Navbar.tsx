import { NavLink } from 'react-router-dom';
import { IconNewspaper, IconRefresh } from './icons';
import styles from './Navbar.module.css';

interface NavbarProps {
  updatedAt: string;
  loading:   boolean;
}

export default function Navbar({ updatedAt, loading }: NavbarProps) {
  return (
    <nav className={styles.navbar}>
      <div className={styles.inner}>
        <NavLink to="/" className={styles.brand}>
          <IconNewspaper size={22} />
          <span>Última Hora Colombia</span>
        </NavLink>

        {loading ? (
          <span className={styles.status}>
            <IconRefresh size={14} className={styles.spin} />
            Actualizando…
          </span>
        ) : updatedAt ? (
          <span className={styles.status}>
            Actualizado: {updatedAt}
          </span>
        ) : null}
      </div>
    </nav>
  );
}
