import SourceCard from '../components/SourceCard';
import { NoticiasMap } from '../hooks/useNoticias';
import styles from './HomePage.module.css';

const PINNED = 'El Tiempo';

interface Props {
  data:    NoticiasMap;
  loading: boolean;
  error:   string | null;
}

export default function HomePage({ data, loading, error }: Props) {
  const sources      = Object.keys(data);
  const otherSources = sources.filter(s => s !== PINNED);
  const hasPinned    = PINNED in data;

  const totalNoticias = Object.values(data).reduce((s, arr) => s + arr.length, 0);

  if (error) {
    return (
      <div className={styles.center}>
        <div className={styles.errorCard}>
          <h2>Sin datos disponibles</h2>
          <p>{error}</p>
          <p className={styles.hint}>
            El scraper aún no ha generado el archivo. Espera la próxima ejecución automática
            o ejecuta el workflow manualmente desde GitHub Actions.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Monitor de Noticias</h1>
        {!loading && totalNoticias > 0 && (
          <p className={styles.summary}>
            {totalNoticias} noticias de hoy · {sources.length} fuentes
          </p>
        )}
      </div>

      {loading ? (
        <div className={styles.layout}>
          <div className={styles.pinnedLeft}><div className={styles.skeleton} style={{ height: '100%', minHeight: 400 }} /></div>
          <div className={styles.grid}>
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className={styles.skeleton} />
            ))}
          </div>
        </div>
      ) : sources.length === 0 ? (
        <div className={styles.center}>
          <p className={styles.empty}>No hay noticias para hoy todavía.</p>
        </div>
      ) : (
        <div className={styles.layout}>
          {hasPinned && (
            <aside className={styles.pinnedLeft}>
              <SourceCard
                fuente={PINNED}
                noticias={data[PINNED]}
                index={0}
                showAll
              />
            </aside>
          )}
          <div className={styles.grid}>
            {otherSources.map((fuente, i) => (
              <SourceCard
                key={fuente}
                fuente={fuente}
                noticias={data[fuente]}
                index={hasPinned ? i + 1 : i}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
