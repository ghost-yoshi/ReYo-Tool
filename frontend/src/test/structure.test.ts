import { describe, expect, it } from "vitest";
import { example, flatten, markers, parseStructure, personalize, updateNode, validateStructure } from "@/lib/structure";

describe("Structure document rules", () => {
  it("requires schema_version 1", () => { expect(validateStructure({ ...example, schema_version: 2 })).toContain("schema_version : la valeur doit être 1."); });
  it("requires kind structure", () => { expect(validateStructure({ ...example, kind: "report" })).toContain('kind : la valeur doit être « structure ».'); });
  it("requires a nonempty node array", () => { expect(validateStructure({ ...example, noeuds: [] })).toContain("noeuds : au moins un nœud est requis."); });
  it.each(["id", "type", "enonce", "attendu", "enfants"])("requires node field %s recursively", key => { const value = structuredClone(example); const child = value.noeuds[0]?.enfants[0]; if (!child) throw new Error("Example child required"); const node = child as unknown as Record<string, unknown>; delete node[key]; expect(validateStructure(value).some(error => error.includes(key))).toBe(true); });
  it("handles invalid JSON without throwing", () => { expect(parseStructure("{").errors).toHaveLength(1); });
  it("supplies exactly two sections and one question with command and capture", () => { expect(validateStructure(example)).toEqual([]); const nodes = flatten(example.noeuds); expect(nodes.filter(n => n.type === "section")).toHaveLength(2); const questions = nodes.filter(n => n.type === "question"); expect(questions).toHaveLength(1); expect(questions[0]?.enfants.some(n => n.attendu.includes("commande"))).toBe(true); expect(questions[0]?.enfants.some(n => n.attendu.includes("capture"))).toBe(true); });
  it("keeps markers valid in final structure", () => { expect(markers(example)).toHaveLength(4); expect(validateStructure(example)).toEqual([]); });
  it("only replaces the last two marker headers and restores them on blank input", () => { const original = example.regles_rendu.entete; const changed = personalize(original, original, "Alice", "12 novembre 2026"); expect(changed).toEqual([original[0], original[1], "Étudiant(s) : Alice", "Date : 12 novembre 2026"]); expect(personalize(changed, original, "", "")).toEqual(original); });
  it("text editing does not add or remove nodes", () => { const nodes = updateNode(example.noeuds, "cmd", "ping localhost"); expect(flatten(nodes)).toHaveLength(flatten(example.noeuds).length); expect(flatten(nodes).find(n => n.id === "cmd")?.enonce).toBe("ping localhost"); });
});