import type { Noeud, Structure, Theme } from "@/types";

const object = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
export function validateStructure(value: unknown): string[] {
  const errors: string[] = [];
  if (!object(value)) return ["Le JSON doit être un objet."];
  if (value["schema_version"] !== 1) errors.push("schema_version : la valeur doit être 1.");
  if (value["kind"] !== "structure") errors.push('kind : la valeur doit être « structure ».');
  const strings = (obj: Record<string, unknown>, keys: string[], path: string) => keys.forEach(key => { if (typeof obj[key] !== "string") errors.push(`${path} > ${key} : texte requis.`); });
  if (!object(value["meta"])) errors.push("meta : objet requis.");
  else { strings(value["meta"], ["matiere", "code_ue", "titre"], "meta"); if (value["meta"]["enseignant"] !== null && typeof value["meta"]["enseignant"] !== "string") errors.push("meta > enseignant : texte ou null requis."); }
  if (!object(value["regles_rendu"])) errors.push("regles_rendu : objet requis.");
  else {
    if (!Array.isArray(value["regles_rendu"]["entete"]) || !value["regles_rendu"]["entete"].every(v => typeof v === "string")) errors.push("regles_rendu > entete : liste de textes requise.");
    if (!["docx", "pdf"].includes(String(value["regles_rendu"]["format"]))) errors.push("regles_rendu > format : docx ou pdf requis.");
    if (value["regles_rendu"]["filename"] !== null && typeof value["regles_rendu"]["filename"] !== "string") errors.push("regles_rendu > filename : texte ou null requis.");
  }
  const ids = new Set<string>();
  function nodes(list: unknown, path: string, depth: number) {
    if (depth > 50) { errors.push(`${path} : trop de niveaux imbriqués.`); return; }
    if (!Array.isArray(list)) { errors.push(`${path} : tableau requis.`); return; }
    list.forEach((node: unknown, i) => {
      const p = `${path} > ${i + 1}`;
      if (!object(node)) { errors.push(`${p} : objet requis.`); return; }
      strings(node, ["id", "enonce"], p);
      if (typeof node["id"] === "string") { if (!node["id"] || ids.has(node["id"])) errors.push(`${p} > id : identifiant vide ou dupliqué.`); ids.add(node["id"]); }
      if (!["section", "info", "consigne", "cas", "question"].includes(String(node["type"]))) errors.push(`${p} > type : type absent ou non reconnu.`);
      if (!Array.isArray(node["attendu"]) || !node["attendu"].every(v => ["texte", "commande", "capture"].includes(v))) errors.push(`${p} > attendu : liste de texte, commande ou capture requise.`);
      nodes(node["enfants"], `${p} > enfants`, depth + 1);
    });
  }
  if (!Array.isArray(value["noeuds"]) || value["noeuds"].length === 0) errors.push("noeuds : au moins un nœud est requis.");
  nodes(value["noeuds"], "noeuds", 0);
  return errors;
}
export function parseStructure(text: string): { structure?: Structure; errors: string[] } {
  try { const value = JSON.parse(text); const errors = validateStructure(value); return errors.length ? { errors } : { structure: value as Structure, errors }; }
  catch { return { errors: ["JSON invalide : vérifiez les virgules, les guillemets et les accolades."] }; }
}
export function flatten(nodes: Noeud[]): Noeud[] { return nodes.flatMap(n => [n, ...flatten(n.enfants)]); }
export function updateNode(nodes: Noeud[], id: string, text: string): Noeud[] { return nodes.map(n => ({ ...n, enonce: n.id === id ? text : n.enonce, enfants: updateNode(n.enfants, id, text) })); }
export function markers(structure: Structure) {
  return [{ id: "document-title", text: structure.meta.titre }, ...structure.regles_rendu.entete.map((text, i) => ({ id: `header-${i}`, text })), ...flatten(structure.noeuds).map(n => ({ id: `node-${n.id}`, text: n.enonce }))].flatMap(item => [...item.text.matchAll(/\[À COMPLÉTER[^\]]*\]/g)].map(match => ({ id: item.id, text: match[0] })));
}
export function personalize(headers: string[], originals: string[], students: string, date: string) {
  const result = [...headers];
  const start = originals.length - 2;
  if (start < 0) return result;
  if (originals[start]?.includes("[À COMPLÉTER")) result[start] = students.trim() ? `Étudiant(s) : ${students}` : originals[start] ?? "";
  if (originals[start + 1]?.includes("[À COMPLÉTER")) result[start + 1] = date.trim() ? `Date : ${date}` : originals[start + 1] ?? "";
  return result;
}
export const example: Structure = {
  schema_version: 1, kind: "structure",
  meta: { matiere: "Réseaux informatiques", code_ue: "INF 204", titre: "TP 01 — Prise en main des réseaux", enseignant: "Dr. Martin" },
  regles_rendu: { format: "docx", filename: null, entete: ["Université · Département informatique", "Réseaux informatiques — INF 204", "Étudiant(s) : [À COMPLÉTER : nom et prénom]", "Date : [À COMPLÉTER : date du TP]"] },
  noeuds: [
    { id: "s1", type: "section", enonce: "1. Objectifs du TP", attendu: [], enfants: [{ id: "intro", type: "info", enonce: "Identifier les paramètres réseau de votre poste et vérifier la connectivité avec une machine distante.", attendu: ["texte"], enfants: [] }] },
    { id: "s2", type: "section", enonce: "2. Configuration et connectivité", attendu: [], enfants: [{ id: "q1", type: "question", enonce: "2.1. Observer la configuration réseau", attendu: ["texte"], enfants: [
      { id: "cmd", type: "consigne", enonce: "ipconfig /all", attendu: ["commande"], enfants: [] },
      { id: "capture", type: "consigne", enonce: "[À COMPLÉTER : insérer une capture de la configuration réseau]", attendu: ["capture"], enfants: [] },
      { id: "answer", type: "info", enonce: "Adresse IPv4 et masque de sous-réseau : [À COMPLÉTER : votre observation]", attendu: ["texte"], enfants: [] }
    ] }] }
  ]
};
export const exampleThemes: Record<string, Theme> = {
  academic: { nom: "Rapport académique", description: "Sobre et institutionnel, pour un rapport ou un devoir universitaire.", police_principale: "Georgia", couleur_primaire: "1F3864", couleur_secondaire: "5B6B7F", couleur_texte: "222222", couleur_fond: "F7F8FA", taille_titre: 20, taille_section: 14, taille_texte: 11 },
  modern: { nom: "Rapport informatique", description: "Titres teal et ton technique, pour un projet de développement ou de réseaux.", police_principale: "Arial", couleur_primaire: "0F766E", couleur_secondaire: "475569", couleur_texte: "1F2937", couleur_fond: "F0FDFA", taille_titre: 20, taille_section: 14, taille_texte: 11 },
  classic: { nom: "Compte rendu classique", description: "Noir et gris, sans fioriture, pour un compte rendu court.", police_principale: "Times New Roman", couleur_primaire: "27272A", couleur_secondaire: "71717A", couleur_texte: "27272A", couleur_fond: "FAFAFA", taille_titre: 19, taille_section: 13, taille_texte: 11 }
};