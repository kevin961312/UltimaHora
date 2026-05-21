import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p>© {new Date().getFullYear()} Última Hora Colombia · Monitor de noticias automatizado</p>
    </footer>
  );
}
