import { useState, useCallback } from 'react';

const KEY = 'uh_pinned';

function load(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function persist(pins: Set<string>): void {
  localStorage.setItem(KEY, JSON.stringify([...pins]));
}

export function usePinnedSources() {
  const [pinned, setPinned] = useState<Set<string>>(load);

  const toggle = useCallback((fuente: string) => {
    setPinned(prev => {
      const next = new Set(prev);
      if (next.has(fuente)) next.delete(fuente);
      else next.add(fuente);
      persist(next);
      return next;
    });
  }, []);

  return {
    isPinned: (fuente: string) => pinned.has(fuente),
    toggle,
  };
}
