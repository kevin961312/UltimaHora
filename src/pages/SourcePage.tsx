import { useParams, useNavigate } from 'react-router-dom';
import { IconArrowLeft, IconExternalLink } from '../components/icons';
import { NoticiasMap, toSlug } from '../hooks/useNoticias';
import styles from './SourcePage.module.css';

interface Props {
  data: NoticiasMap;
}

export default function SourcePage({ data }: Props) {
  const { slug }   = useParams<{ slug: string }>();
  const navigate   = useNavigate();

  const fuente = Object.keys(data).find(f => toSlug(f) === slug);
  const noticias = fuente ? data[fuente] : [];
  const tipo     = noticias[0]?.Tipo ?? '';

  if (!fuente) {
    return (
      <div className={styles.center}>
        <p>Fuente no encontrada.</p>
        <button className={styles.backBtn} onClick={() => navigate('/')}>
          <IconArrowLeft size={16} /> Volver al inicio
        </button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <button className={styles.backBtn} onClick={() => navigate('/')}>
          <IconArrowLeft size={16} /> Todas las fuentes
        </button>
        <div className={styles.titleRow}>
          <h1 className={styles.title}>{fuente}</h1>
          <span className={`${styles.badge} ${tipo.includes('Oficial') ? styles.oficial : styles.medio}`}>
            {tipo.includes('Oficial') ? 'Entidad Oficial' : 'Medio de Comunicación'}
          </span>
        </div>
        <p className={styles.count}>{noticias.length} noticias de hoy</p>
      </div>

      <ul className={styles.list}>
        {noticias.map((n, i) => (
          <li key={i} className={styles.item}>
            <span className={styles.fecha}>{n.Fecha}</span>
            <a
              href={n.URL}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.link}
            >
              {n.Titular}
              <IconExternalLink size={14} className={styles.extIcon} />
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
