import { useNavigate } from 'react-router-dom';
import { IconExternalLink, IconPin } from './icons';
import { Noticia, toSlug } from '../hooks/useNoticias';
import styles from './SourceCard.module.css';

const CARD_COLORS = [
  { bg: '#f5f0ff', accent: '#7c3aed' },
  { bg: '#fdf2ff', accent: '#a21caf' },
  { bg: '#eef2ff', accent: '#4f46e5' },
  { bg: '#fdf4ff', accent: '#9333ea' },
  { bg: '#ede9fe', accent: '#6d28d9' },
  { bg: '#f0f4ff', accent: '#3730a3' },
  { bg: '#faf5ff', accent: '#8b5cf6' },
  { bg: '#e8e0ff', accent: '#5b21b6' },
];

interface Props {
  fuente:        string;
  noticias:      Noticia[];
  index:         number;
  showAll?:      boolean;
  isPinned?:     boolean;
  onTogglePin?:  () => void;
}

const PREVIEW = 5;

export default function SourceCard({ fuente, noticias, index, showAll = false, isPinned = false, onTogglePin }: Props) {
  const navigate = useNavigate();
  const color    = CARD_COLORS[index % CARD_COLORS.length];
  const visible  = showAll ? noticias : noticias.slice(0, PREVIEW);
  const tipo     = noticias[0]?.Tipo ?? '';

  return (
    <article
      className={`${styles.card} ${isPinned ? styles.cardPinned : ''}`}
      style={{ '--card-bg': color.bg, '--card-accent': color.accent } as React.CSSProperties}
    >
      <header className={styles.header}>
        <h2 className={styles.title}>{fuente}</h2>
        <div className={styles.headerRight}>
          {onTogglePin && (
            <button
              className={`${styles.pinBtn} ${isPinned ? styles.pinActive : ''}`}
              onClick={onTogglePin}
              title={isPinned ? 'Quitar pin' : 'Fijar fuente'}
              aria-label={isPinned ? 'Quitar pin' : 'Fijar fuente'}
            >
              <IconPin size={14} filled={isPinned} />
            </button>
          )}
          <span className={`${styles.badge} ${tipo.includes('Oficial') ? styles.oficial : styles.medio}`}>
            {tipo.includes('Oficial') ? 'Oficial' : 'Medio'}
          </span>
        </div>
      </header>

      <ul className={styles.list}>
        {visible.map((n, i) => (
          <li key={i} className={styles.item}>
            <span className={styles.fecha}>{n.Fecha}</span>
            <a
              href={n.URL}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.link}
            >
              {n.Titular}
              <IconExternalLink size={12} className={styles.extIcon} />
            </a>
          </li>
        ))}
      </ul>

      {!showAll && noticias.length > PREVIEW && (
        <footer className={styles.footer}>
          <button
            className={styles.verMas}
            onClick={() => navigate(`/${toSlug(fuente)}`)}
          >
            Ver más ({noticias.length - PREVIEW} más) →
          </button>
        </footer>
      )}

      {noticias.length === 0 && (
        <p className={styles.empty}>Sin noticias hoy</p>
      )}
    </article>
  );
}
