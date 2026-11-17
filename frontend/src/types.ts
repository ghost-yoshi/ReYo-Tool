export type TypeNoeud = "section" | "info" | "consigne" | "cas" | "question";
export type Attendu = "texte" | "commande" | "capture";
export interface Noeud { id: string; type: TypeNoeud; enonce: string; attendu: Attendu[]; enfants: Noeud[]; }
export interface Meta { matiere: string; code_ue: string; titre: string; enseignant: string | null; }
export interface ReglesRendu { entete: string[]; format: "docx"; filename: string | null; }
export interface Structure { schema_version: 1; kind: "structure"; meta: Meta; regles_rendu: ReglesRendu; noeuds: Noeud[]; }
export interface StructureKit { version: string; prompt: string; schema: Record<string, unknown>; }
export interface StructureValidation { ok: boolean; errors: string[]; warnings: string[]; structure: Structure | null; prompt_reparation: string | null; }
export interface Theme { nom: string; description?: string; police_principale: string; couleur_primaire: string; couleur_secondaire: string; couleur_texte: string; couleur_fond?: string; taille_titre: number; taille_section: number; taille_texte: number; }