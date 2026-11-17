import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Structure } from "@/types";
import { validateStructure } from "@/lib/structure";

type Draft = { structure: Structure | null; theme: string; step: number; exampleMode: boolean; originals: string[]; students: string; date: string };
const empty: Draft = { structure: null, theme: "academic", step: 1, exampleMode: false, originals: [], students: "", date: "" };
const key = "reyo-draft-v1";
const Context = createContext<{ draft: Draft; setDraft: React.Dispatch<React.SetStateAction<Draft>>; reset: () => void; storageError: boolean } | null>(null);
export function DraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<Draft>(empty);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  useEffect(() => {
    try { const raw = localStorage.getItem(key); if (raw) { const saved = JSON.parse(raw); if (saved.structure && !validateStructure(saved.structure).length) setDraft({ ...empty, ...saved, theme: typeof saved.theme === "string" ? saved.theme : "academic", step: [1, 2, 3, 4].includes(saved.step) ? saved.step : 1, originals: Array.isArray(saved.originals) && saved.originals.every((v: unknown) => typeof v === "string") ? saved.originals : saved.structure.regles_rendu.entete, students: typeof saved.students === "string" ? saved.students : "", date: typeof saved.date === "string" ? saved.date : "" }); } } catch { setStorageError(true); }
    setReady(true);
  }, []);
  useEffect(() => { if (!ready) return; try { if (draft.structure) localStorage.setItem(key, JSON.stringify(draft)); else localStorage.removeItem(key); } catch { setStorageError(true); } }, [draft, ready]);
  const reset = () => { setDraft(empty); try { localStorage.removeItem(key); } catch { setStorageError(true); } };
  return <Context.Provider value={{ draft, setDraft, reset, storageError }}>{children}</Context.Provider>;
}
export function useDraft() { const context = useContext(Context); if (!context) throw new Error("DraftProvider required"); return context; }