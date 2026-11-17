import type { Structure, StructureKit, StructureValidation, Theme } from "@/types";

export const apiConfigured = Boolean(import.meta.env["VITE_REYO_API_URL"]?.trim());
export const generateEnabled = import.meta.env["VITE_ENABLE_GENERATE"] === "true";
export class ApiError extends Error { constructor(public messages: string[], public status?: number) { super(messages.join("\n")); } }
export function detailMessages(detail: unknown): string[] {
  if (typeof detail === "string") return [detail];
  if (Array.isArray(detail)) return detail.map(item => `${Array.isArray(item?.loc) ? item.loc.join(" > ") : "Validation"} : ${typeof item?.msg === "string" ? item.msg : "Valeur invalide"}`);
  return ["Le service n’a pas pu traiter le document."];
}
export function filenameFromDisposition(header: string | null): string {
  const encoded = header?.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)?.[1];
  let filename = header?.match(/filename\s*=\s*"([^"]+)"/i)?.[1] ?? header?.match(/filename\s*=\s*([^;]+)/i)?.[1];
  if (encoded) { try { filename = decodeURIComponent(encoded.trim()); } catch { /* use plain filename */ } }
  return filename?.trim().split(/[\\/]/).pop() || "compte_rendu.docx";
}
async function request(path: string, options: RequestInit = {}) {
  const base = import.meta.env["VITE_REYO_API_URL"]?.trim().replace(/\/$/, "");
  console.log(base)
  if (!base) throw new ApiError(["Impossible de joindre le service. L’adresse de l’API n’est pas configurée."]);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(`${base}${path}`, { ...options, signal: controller.signal });
    if (!response.ok) {
      let body: { detail?: unknown } = {};
      try { body = await response.json(); } catch { /* no JSON response */ }
      throw new ApiError(response.status === 422 ? detailMessages(body.detail) : [`Le service a renvoyé une erreur (${response.status}). Réessayez.`], response.status);
    }
    // Consume the body before clearing the timeout, including binary transfers.
    return path === "/render" ? { blob: await response.blob(), filename: filenameFromDisposition(response.headers.get("Content-Disposition")) } : await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError([controller.signal.aborted ? "Délai dépassé (30 s). Réessayez dans un instant." : "Impossible de joindre le service"]);
  } finally { clearTimeout(timeout); }
}
export const api = {
  health: (): Promise<unknown> => request("/health"),
  themes: async (): Promise<Record<string, Theme>> => normalizeThemes(await request("/themes")),
  structureKit: async (): Promise<StructureKit> => {
    const [prompt, schema] = await Promise.all([request("/prompt-structure"), request("/schema")]) as [{ version: string; prompt: string }, Record<string, unknown>];
    return { version: prompt.version, prompt: prompt.prompt, schema };
  },
  validate: (texte: string): Promise<StructureValidation> => request("/validate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ json: texte }) }),
  render: (structure: Structure, theme: string): Promise<{ blob: Blob; filename: string }> => request("/render", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structure, theme }) }),
  generate: (file: File): Promise<Structure> => { if (!generateEnabled) return Promise.reject(new ApiError(["Bientôt disponible"])); const form = new FormData(); form.append("file", file); return request("/generate", { method: "POST", body: form }); }
};
export function downloadDocument(result: { blob: Blob; filename: string }) {
  const url = URL.createObjectURL(result.blob);
  const link = document.createElement("a"); link.href = url; link.download = result.filename; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const defaultPalette: [string, string, string, string, string] = ["Calibri", "#1F3864", "#5B6B7F", "#222222", "#F7F8FA"];
const palettes: Record<string, [string, string, string, string, string]> = {
  academic: ["Times New Roman", "#1F3864", "#5B6B7F", "#222222", "#F7F8FA"],
  compte_rendu_tp: ["Calibri", "#1D4E89", "#9A3412", "#1F2937", "#F8FAFC"],
  modern_tech: ["Segoe UI", "#0F766E", "#475569", "#1F2937", "#F0FDFA"],
  universitaire: ["Cambria", "#1B2A4A", "#6B7280", "#1A1A1A", "#F8F7F4"],
  classique_bordeaux: ["Georgia", "#6D1A36", "#6B5B5B", "#2B2B2B", "#FBF7F8"],
  rapport_ingenieur: ["Calibri", "#14395E", "#475569", "#1F2933", "#F5F8FB"],
  minimal_gris: ["Arial", "#27272A", "#71717A", "#27272A", "#FAFAFA"],
  nature_vert: ["Trebuchet MS", "#1E4D2B", "#4A7C59", "#1F2A1F", "#F6FAF7"],
  litteraire: ["Garamond", "#3E2C1C", "#8B6B4A", "#2A2016", "#FBF8F3"],
  accessible: ["Verdana", "#000000", "#0047AB", "#000000", "#FFFFFF"],
};
/** The service may return either full theme objects or a simple key → name map. */
export function normalizeThemes(data: unknown): Record<string, Theme> {
  if (!data || typeof data !== "object") return {};
  const out: Record<string, Theme> = {};
  for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
    const [font, primary, secondary, text, fond] = palettes[key] ?? defaultPalette;
    const base: Theme = { nom: key, police_principale: font, couleur_primaire: primary, couleur_secondaire: secondary, couleur_texte: text, couleur_fond: fond, taille_titre: 20, taille_section: 14, taille_texte: 11 };
    if (typeof value === "string") { out[key] = { ...base, nom: value }; continue; }
    if (!value || typeof value !== "object") { out[key] = base; continue; }
    const theme: Theme = { ...base };
    const fields = value as Record<string, unknown>;
    for (const field of ["nom", "description", "police_principale", "couleur_primaire", "couleur_secondaire", "couleur_texte", "couleur_fond"] as const) {
      if (typeof fields[field] === "string" && fields[field]) theme[field] = fields[field] as string;
    }
    for (const field of ["taille_titre", "taille_section", "taille_texte"] as const) {
      if (typeof fields[field] === "number" && fields[field]) theme[field] = fields[field] as number;
    }
    out[key] = theme;
  }
  return out;
}
