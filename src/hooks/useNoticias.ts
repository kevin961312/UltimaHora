import { useCallback, useEffect, useState } from 'react';
import * as XLSX from 'xlsx';

export interface Noticia {
  Fecha:    string;
  Tipo:     string;
  Fuente:   string;
  Titular:  string;
  URL:      string;
}

export type NoticiasMap = Record<string, Noticia[]>;

export function toSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

const POLL_MS = 30 * 60 * 1000; // 30 minutos, igual que el workflow

export function useNoticias() {
  const [data,      setData]      = useState<NoticiasMap>({});
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string>('');

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    const base = import.meta.env.BASE_URL;
    fetch(`${base}ultimahora.xlsx?t=${Date.now()}`)
      .then(res => {
        if (!res.ok) throw new Error('Datos no disponibles aún');
        return res.arrayBuffer();
      })
      .then(buf => {
        const wb   = XLSX.read(buf, { type: 'array' });
        const ws   = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<Noticia>(ws);

        const map: NoticiasMap = {};
        for (const row of rows) {
          const f = row.Fuente || '';
          if (!map[f]) map[f] = [];
          map[f].push(row);
        }
        setData(map);
        setUpdatedAt(
          new Date().toLocaleString('es-CO', {
            timeZone: 'America/Bogota',
            day:    '2-digit',
            month:  '2-digit',
            year:   'numeric',
            hour:   '2-digit',
            minute: '2-digit',
          })
        );
      })
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, POLL_MS);
    return () => clearInterval(id);
  }, [fetchData]);

  return { data, loading, error, updatedAt, refetch: fetchData };
}
