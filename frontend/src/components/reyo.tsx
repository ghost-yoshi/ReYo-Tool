import { useEffect, useRef, useState, type CSSProperties } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, ChevronRight, CircleHelp, Copy, Download, FileJson, FileText, Image, Info, LoaderCircle, LockKeyhole, Moon, RotateCcw, ShieldCheck, Sparkles, Sun, Trash2, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useDraft } from "@/lib/draft";
import { api, apiConfigured, ApiError, downloadDocument, generateEnabled } from "@/lib/api";
import { example, exampleThemes, flatten, markers, parseStructure, personalize, updateNode, validateStructure } from "@/lib/structure";
import type { Noeud, Structure, Theme } from "@/types";

const steps = ["Import", "Relecture", "Thème", "Téléchargement"];
const explanations = ["Votre structure, le point de départ.", "Un dernier regard avant la mise en forme.", "Une présentation à la hauteur de votre travail.", "Votre compte rendu, prêt à rendre."];
function ErrorList({ errors }: { errors: string[] }) { return <div aria-live="polite">{errors.length > 0 && <div className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"><p className="mb-2 font-semibold">Une vérification est nécessaire</p><ul className="list-disc space-y-1 pl-4">{errors.map((e, i) => <li key={i}>{e}</li>)}</ul></div>}</div>; }
function Highlight({ text }: { text: string }) { return <>{text.split(/(\[À COMPLÉTER[^\]]*\])/g).map((part, i) => part.startsWith("[À COMPLÉTER") ? <mark key={i}>{part}</mark> : part)}</>; }
function Editable({ text, label, id, onChange, className = "" }: { text: string; label: string; id: string; onChange: (text: string) => void; className?: string }) {
  const [editing, setEditing] = useState(false);
  return <div id={id} className={className}>{editing ? <Textarea aria-label={label} autoFocus className="edit-input" value={text} onChange={e => onChange(e.target.value)} onBlur={() => setEditing(false)} onKeyDown={e => { if (e.key === "Escape") setEditing(false); }} /> : <Button variant="ghost" className="editable" aria-label={`Modifier : ${label}`} onClick={() => setEditing(true)}><Highlight text={text || "…"} /></Button>}</div>;
}
function DocumentNode({ node, change }: { node: Noeud; change: (id: string, text: string) => void }) {
  const content = <Editable text={node.enonce} id={`node-${node.id}`} label={node.enonce || "Énoncé"} onChange={text => change(node.id, text)} />;
  const command = node.type === "consigne" && node.attendu.includes("commande");
  const capture = node.type === "consigne" && node.attendu.includes("capture");
  return <>
    {node.type === "section" ? <h1 className="document-section">{content}</h1> : node.type === "question" || node.type === "cas" ? <h2 className="document-question">{content}</h2> : command ? <div className="document-code">{content}</div> : capture ? <div className="document-capture"><Image className="size-6 shrink-0 text-muted-foreground" />{content}</div> : <div className="document-paragraph">{content}</div>}
    {node.enfants.map(child => <DocumentNode key={child.id} node={child} change={change} />)}
  </>;
}
function StructureHelper() {
  const kit = useQuery({ queryKey: ["structure-kit"], queryFn: api.structureKit, enabled: apiConfigured, retry: false, staleTime: Infinity });
  const [copied, setCopied] = useState("");
  const copy = async (key: string, text: string) => {
    try { await navigator.clipboard.writeText(text); setCopied(key); window.setTimeout(() => setCopied(""), 2000); } catch { /* presse-papiers indisponible */ }
  };
  return <details className="mb-6 rounded-lg border bg-card">
    <summary className="cursor-pointer px-5 py-4 text-sm font-semibold">Obtenir le JSON depuis votre IA<span className="ml-2 font-normal text-muted-foreground">— prompt et schéma à copier</span></summary>
    <div className="border-t px-5 py-4">
      <p className="text-xs leading-relaxed text-muted-foreground">Copiez le prompt dans l’IA de votre choix avec votre fiche de TP, puis collez le JSON obtenu ci-dessous. ReYo n’envoie aucune donnée à un service d’IA.</p>
      {kit.isPending && <p className="mt-4 flex items-center gap-2 text-xs text-muted-foreground"><LoaderCircle className="size-4 animate-spin" />Chargement du prompt…</p>}
      {kit.isError && <p className="mt-4 text-xs text-destructive">Le prompt n’est pas disponible. <Button variant="link" size="sm" onClick={() => void kit.refetch()}>Réessayer</Button></p>}
      {kit.data && <>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => void copy("prompt", kit.data.prompt)}>{copied === "prompt" ? <Check /> : <Copy />}Copier le prompt</Button>
          <Button variant="outline" size="sm" onClick={() => void copy("schema", JSON.stringify(kit.data.schema, null, 2))}>{copied === "schema" ? <Check /> : <Copy />}Copier le schéma JSON</Button>
          <span className="text-[10px] text-muted-foreground">{kit.data.version}</span>
          <span role="status" aria-live="polite" className="text-xs text-success">{copied ? "Copié" : ""}</span>
        </div>
        <details className="mt-4"><summary className="cursor-pointer text-xs text-muted-foreground">Voir le prompt</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border bg-muted p-3 text-xs leading-relaxed">{kit.data.prompt}</pre></details>
        <details className="mt-2"><summary className="cursor-pointer text-xs text-muted-foreground">Voir le schéma JSON</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border bg-muted p-3 font-mono text-[10px] leading-relaxed">{JSON.stringify(kit.data.schema, null, 2)}</pre></details>
      </>}
    </div>
  </details>;
}
function ThemeCard({ theme, selected, onSelect }: { theme: Theme; selected: boolean; onSelect: () => void }) {
  // Theme colors, sizes and fonts are service-supplied document data, not interface styling.
  const hex = (value: string | undefined, fallback: string) => {
    const v = value?.replace(/^#/, "") ?? "";
    return /^[0-9a-f]{6}$/i.test(v) ? `#${v}` : fallback;
  };
  const variables = {
    "--preview-font": `"${theme.police_principale.replace(/["\\;]/g, "")}"`,
    "--preview-primary": hex(theme.couleur_primaire, "var(--foreground)"),
    "--preview-secondary": hex(theme.couleur_secondaire, "var(--muted-foreground)"),
    "--preview-text": hex(theme.couleur_texte, "var(--foreground)"),
    "--preview-bg": hex(theme.couleur_fond, "var(--card)"),
    "--preview-title-size": `${theme.taille_titre}px`,
    "--preview-section-size": `${theme.taille_section}px`,
    "--preview-body-size": `${theme.taille_texte}px`,
  } as CSSProperties;
  return <Button variant="ghost" className={`theme-card ${selected ? "selected" : ""}`} style={variables} aria-pressed={selected} aria-label={`Choisir le thème ${theme.nom}`} onClick={onSelect}>
    <div className="flex items-start justify-between gap-3 border-b px-5 py-4"><span className="min-w-0"><span className="block font-semibold">{theme.nom}</span>{theme.description && <span className="mt-1 block text-xs font-normal leading-snug text-muted-foreground">{theme.description}</span>}</span><span className={`flex size-5 shrink-0 items-center justify-center rounded-full border ${selected ? "border-primary bg-primary text-primary-foreground" : "border-border"}`}>{selected && <Check className="size-3" />}</span></div>
    <div className="theme-preview"><div className="theme-title">Titre du compte rendu</div><div className="theme-section">1. Section</div><div className="theme-body">Texte courant. Une présentation soignée pour vos observations et vos résultats.</div></div>
    <div className="flex items-center justify-between border-t px-5 py-4"><span className="text-xs text-muted-foreground">{theme.police_principale}</span><span className="flex gap-1.5" aria-hidden="true"><span className="swatch swatch-primary" /><span className="swatch swatch-secondary" /><span className="swatch swatch-text" /><span className="swatch swatch-fond" /></span></div>
  </Button>;
}
export function ReYo() {
  const { draft, setDraft, reset, storageError } = useDraft();
  const { structure, step } = draft;
  const [json, setJson] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [repair, setRepair] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const [copied, setCopied] = useState("");
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState("");
  const [dark, setDark] = useState(false);
  const [confirmErase, setConfirmErase] = useState(false);
  const [markerDrawer, setMarkerDrawer] = useState(false);
  const [help, setHelp] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const generateInput = useRef<HTMLInputElement>(null);
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, retry: false, enabled: apiConfigured, refetchInterval: 60_000 });
  const themes = useQuery({ queryKey: ["themes"], queryFn: api.themes, enabled: step >= 3 && !draft.exampleMode, retry: false });
  const availableThemes = draft.exampleMode ? exampleThemes : themes.data;
  const render = useMutation({ mutationFn: () => { if (!structure) throw new ApiError(["Importez une structure pour continuer."]); return api.render(structure, draft.theme); }, onSuccess: downloadDocument });
  const generate = useMutation({ mutationFn: api.generate, onSuccess: result => { const issues = validateStructure(result); if (issues.length) { setErrors(issues); return; } load(result, false); } });
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  useEffect(() => { if (availableThemes && !availableThemes[draft.theme]) { const first = availableThemes["academic"] ? "academic" : Object.keys(availableThemes)[0]; if (first) setDraft(d => ({ ...d, theme: first })); } }, [availableThemes, draft.theme, setDraft]);
  const remaining = structure ? markers(structure) : [];
  const allNodes = structure ? flatten(structure.noeuds) : [];
  const go = (next: number) => { setErrors([]); setDraft(d => ({ ...d, step: next })); window.scrollTo({ top: 0, behavior: "smooth" }); };
  function load(value: Structure, exampleMode: boolean) { setDraft({ structure: structuredClone(value), step: 1, theme: "academic", exampleMode, originals: [...value.regles_rendu.entete], students: "", date: "" }); render.reset(); generate.reset(); setErrors([]); }
  const copyText = async (key: string, text: string) => {
    try { await navigator.clipboard.writeText(text); setCopied(key); window.setTimeout(() => setCopied(""), 2000); } catch { /* presse-papiers indisponible */ }
  };
  const importText = async (text: string, name?: string) => {
    setJson(text); setWarnings([]); setRepair(null);
    if (!apiConfigured) { const result = parseStructure(text); setErrors(result.errors); if (result.structure) { load(result.structure, false); setFileName(name || "Structure collée"); } return; }
    setChecking(true);
    try {
      const result = await api.validate(text);
      setErrors(result.errors); setWarnings(result.warnings); setRepair(result.prompt_reparation);
      if (result.ok && result.structure) { load(result.structure, false); setFileName(name || "Structure collée"); }
    } catch {
      // Le service est injoignable : la vérification locale reste disponible.
      const local = parseStructure(text);
      setErrors(local.errors);
      setWarnings(["Service de validation indisponible : vérification locale utilisée."]);
      if (local.structure) { load(local.structure, false); setFileName(name || "Structure collée"); }
    } finally { setChecking(false); }
  };
  const readFile = async (file?: File) => { if (!file) return; if (!file.name.toLowerCase().endsWith(".json")) { setErrors(["Choisissez un fichier au format .json."]); return; } try { importText(await file.text(), file.name); } catch { setErrors(["Impossible de lire ce fichier. Veuillez réessayer."]); } };
  const changeStructure = (update: (s: Structure) => Structure) => { setDraft(d => ({ ...d, structure: d.structure ? update(d.structure) : null })); render.reset(); };
  const changeStudent = (students: string, date: string) => { setDraft(d => ({ ...d, students, date, structure: d.structure ? { ...d.structure, regles_rendu: { ...d.structure.regles_rendu, entete: personalize(d.structure.regles_rendu.entete, d.originals, students, date) } } : null })); render.reset(); };
  const clear = () => { reset(); setJson(""); setErrors([]); setWarnings([]); setRepair(null); setFileName(""); render.reset(); generate.reset(); setConfirmErase(false); };
  const jump = (id: string) => { setMarkerDrawer(false); go(2); setTimeout(() => { const target = document.getElementById(id); target?.scrollIntoView({ behavior: "smooth", block: "center" }); target?.querySelector("button")?.focus({ preventScroll: true }); }, 150); };
  const markerList = <div className="mt-5 space-y-2">{remaining.length ? remaining.map((marker, i) => <Button key={`${marker.id}-${i}`} variant="ghost" className="h-auto w-full justify-start gap-3 whitespace-normal border-b px-0 py-3 text-left text-xs leading-relaxed" onClick={() => jump(marker.id)}><span className="self-start text-muted-foreground">{String(i + 1).padStart(2, "0")}</span><span className="min-w-0 break-words">{marker.text.replace(/^\[À COMPLÉTER\s*:\s*|\]$/g, "")}</span><ChevronRight className="ml-auto shrink-0" /></Button>) : <p className="text-sm text-muted-foreground">Tout est complété.</p>}</div>;
  return <div className="app-shell">
    <header className="border-b bg-card"><div className="mx-auto flex h-[78px] max-w-[1180px] items-center justify-between gap-4 px-5 md:px-8"><div className="flex items-center gap-3"><svg className="brand-symbol" viewBox="0 0 36 42" fill="none" aria-hidden="true"><path d="M7 3h16l8 8v28H7z" stroke="currentColor" strokeWidth="2" /><path d="M23 3v9h8M12 18h13M12 24h9M12 30h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg><span className="text-[26px] font-bold text-primary">ReYo<span className="text-muted-foreground">.</span></span><span className="ml-4 hidden border-l pl-5 text-xs text-muted-foreground md:block">Vos TP, prêts à rendre.</span></div><div className="flex items-center gap-2 sm:gap-5"><span role="status" className="flex items-center gap-2 text-[11px] text-muted-foreground"><span className={`size-1.5 rounded-full ${health.isSuccess ? "bg-success" : "bg-muted-foreground"}`} /><span className="hidden sm:inline">{health.isSuccess ? "Service disponible" : apiConfigured && health.isFetching ? "Connexion au service…" : "Service indisponible"}</span></span><Button variant="ghost" size="icon" title={dark ? "Mode clair" : "Mode sombre"} aria-label={dark ? "Activer le mode clair" : "Activer le mode sombre"} onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button><Button variant="ghost" size="icon" title="À propos de ReYo" aria-label="À propos de ReYo" onClick={() => setHelp(true)}><CircleHelp /></Button></div></div></header>
    <div className="border-b bg-card"><nav className="stepper px-3" aria-label="Étapes du compte rendu">{steps.map((label, i) => <div key={label} className={`step-item ${step === i + 1 ? "step-current" : step > i + 1 ? "step-complete" : ""}`}><Button variant="ghost" className="h-auto flex-col gap-2 px-1 py-0 hover:bg-transparent" disabled={i + 1 > step && (!structure || (i + 1 === 4 && !availableThemes?.[draft.theme]))} aria-current={step === i + 1 ? "step" : undefined} onClick={() => go(i + 1)}><span className="step-number">{step > i + 1 ? <Check className="size-4" /> : String(i + 1).padStart(2, "0")}</span><span className={`text-[11px] sm:text-xs ${step === i + 1 ? "font-semibold text-primary" : "text-muted-foreground"}`}>{label}</span></Button></div>)}</nav></div>
    <main className={`mx-auto w-full flex-1 px-5 pb-12 pt-10 md:px-8 md:pt-12 ${step === 2 ? "max-w-[1180px]" : "max-w-[1030px]"}`}>
      <div className="mb-9"><div className="mb-3 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[.12em] text-muted-foreground"><span className="text-primary">Étape {String(step).padStart(2, "0")}</span><span>/ 04</span>{draft.exampleMode && <span className="ml-2 rounded border px-2 py-0.5 normal-case tracking-normal">Exemple</span>}</div><h1 className="page-heading">{["Importez votre fiche de TP", "Relisez votre compte rendu", "Choisissez votre thème", "Générez votre document Word"][step - 1]}</h1><p className="mt-2 text-sm text-muted-foreground">{explanations[step - 1]}</p></div>
      {step === 1 && <>
        {apiConfigured && <StructureHelper />}
        <div className="import-grid"><section><label className="mb-3 block text-sm font-semibold" htmlFor="json-file">Importer un fichier</label><div className={`drop-zone ${dragging ? "dragging" : ""}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); void readFile(e.dataTransfer.files[0]); }}><div className="upload-icon mb-5"><Upload className="size-6" strokeWidth={1.5} /></div><p className="font-medium">Glissez votre fichier ici</p><p className="mb-5 mt-1.5 text-xs text-muted-foreground">Fichier de structure au format .json</p><Button variant="outline" onClick={() => fileInput.current?.click()}><FileJson />Choisir un fichier</Button><input id="json-file" ref={fileInput} type="file" accept=".json,application/json" className="sr-only" aria-label="Importer un fichier JSON" onChange={e => { void readFile(e.target.files?.[0]); e.target.value = ""; }} /></div></section>
        <section><div className="mb-3 flex items-center justify-between"><label htmlFor="json-text" className="text-sm font-semibold">Coller votre structure JSON</label><span className="font-mono text-xs text-muted-foreground">{ "{ }" }</span></div><Textarea id="json-text" className="json-input" value={json} onChange={e => { setJson(e.target.value); setErrors([]); setWarnings([]); setRepair(null); }} placeholder={'{\n  "schema_version": 1,\n  "kind": "structure",\n  "meta": { ... },\n  "noeuds": [ ... ]\n}'} spellCheck={false} /><div className="mt-3 flex justify-end"><Button variant="link" size="sm" disabled={!json.trim() || checking} onClick={() => void importText(json)}>{checking ? <LoaderCircle className="animate-spin" /> : null}{checking ? "Validation…" : "Valider le JSON"}{!checking && <ArrowRight />}</Button></div></section></div>
        <ErrorList errors={errors} />
        {warnings.length > 0 && <div aria-live="polite" className="mt-4 rounded-md border bg-secondary p-4 text-xs leading-relaxed text-muted-foreground">{warnings.map(warning => <p key={warning}>{warning}</p>)}</div>}
        {repair && <div className="mt-4 rounded-md border border-primary/20 bg-secondary p-4"><p className="text-sm font-semibold">Réparer avec votre IA</p><p className="mt-1 text-xs leading-relaxed text-muted-foreground">Copiez ce prompt dans la même IA, puis recollez le JSON corrigé et validez à nouveau.</p><div className="mt-3 flex flex-wrap items-center gap-2"><Button variant="outline" size="sm" onClick={() => void copyText("repair", repair)}>{copied === "repair" ? <Check /> : <Copy />}Copier le prompt de réparation</Button><span role="status" aria-live="polite" className="text-xs text-success">{copied === "repair" ? "Copié" : ""}</span></div><details className="mt-3"><summary className="cursor-pointer text-xs text-muted-foreground">Voir le prompt de réparation</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border bg-card p-3 text-xs leading-relaxed">{repair}</pre></details></div>}
        <div aria-live="polite">{structure && <div className="mb-5 mt-2 flex items-center gap-3 rounded-md border border-primary/20 bg-secondary p-3 text-primary"><Check className="size-4" /><span className="min-w-0 flex-1 break-words text-xs"><strong>{draft.exampleMode ? "Structure d’exemple chargée" : fileName || "Structure enregistrée"}</strong> · {allNodes.filter(n => n.type === "section").length} sections · {structure.meta.titre}</span><Button variant="ghost" size="icon" aria-label="Retirer la structure" onClick={clear}><X /></Button></div>}</div>
        <div className="example-band mt-5"><div className="flex items-center gap-3"><FileText className="size-5 shrink-0 text-primary" /><div><p className="text-sm font-medium">Pas de fichier sous la main ?</p><p className="mt-1 text-xs text-muted-foreground">Commencez avec un TP d’exemple.</p></div></div><Button variant="outline" onClick={() => { load(example, true); setJson(JSON.stringify(example, null, 2)); setFileName("Exemple — Réseaux informatiques"); }}>Utiliser un exemple<ArrowRight /></Button></div>
        <div className="mt-7 flex flex-wrap items-center gap-3"><Button variant="outline" className="max-w-full h-auto min-h-10 whitespace-normal text-left" disabled={!generateEnabled || generate.isPending} onClick={() => generateInput.current?.click()}><Sparkles />Générer depuis une fiche de TP (PDF/Word)</Button>{!generateEnabled && <span className="text-[10px] text-muted-foreground">Bientôt disponible</span>}<input ref={generateInput} className="sr-only" type="file" accept=".pdf,.doc,.docx" aria-label="Fiche de TP PDF ou Word" onChange={e => { const file = e.target.files?.[0]; if (file) generate.mutate(file); e.target.value = ""; }} />{generate.isPending && <LoaderCircle className="size-4 animate-spin" />}</div><ErrorList errors={generate.error instanceof ApiError ? generate.error.messages : []} />
      </>}
      {step === 2 && structure && <>
        <div className="mb-6 grid grid-cols-1 gap-5 border-y py-5 sm:grid-cols-2"><div><label htmlFor="students" className="mb-2 block text-xs font-medium">Étudiant(s)</label><Input id="students" value={draft.students} placeholder="Nom et prénom" onChange={e => changeStudent(e.target.value, draft.date)} /></div><div><label htmlFor="date" className="mb-2 block text-xs font-medium">Date</label><Input id="date" value={draft.date} placeholder="Ex. 12 novembre 2026" onChange={e => changeStudent(draft.students, e.target.value)} /></div></div>
        <div className="mb-5 lg:hidden"><Sheet open={markerDrawer} onOpenChange={setMarkerDrawer}><SheetTrigger asChild><Button variant="outline"><Info />À compléter<span className="rounded-full bg-marker px-2 text-marker-foreground">{remaining.length}</span></Button></SheetTrigger><SheetContent><SheetTitle>À compléter · {remaining.length}</SheetTitle><SheetDescription>Ces éléments peuvent être complétés dans Word.</SheetDescription>{markerList}</SheetContent></Sheet></div>
        <div className="grid items-start gap-8 lg:grid-cols-[1fr_240px]"><article className="paper" aria-label="Compte rendu éditable">{structure.regles_rendu.entete.map((text, i) => <Editable key={i} id={`header-${i}`} text={text} label={`Ligne d’en-tête ${i + 1}`} className="text-xs text-muted-foreground" onChange={text => changeStructure(s => ({ ...s, regles_rendu: { ...s.regles_rendu, entete: s.regles_rendu.entete.map((line, j) => j === i ? text : line) } }))} />)}<Editable id="document-title" text={structure.meta.titre} label="Titre du compte rendu" className="document-title" onChange={text => changeStructure(s => ({ ...s, meta: { ...s.meta, titre: text } }))} /><div className="mb-6 border-b" />{structure.noeuds.map(node => <DocumentNode key={node.id} node={node} change={(id, text) => changeStructure(s => ({ ...s, noeuds: updateNode(s.noeuds, id, text) }))} />)}</article><aside className="sticky top-6 hidden lg:block"><div className="flex items-center justify-between border-b pb-4"><h2 className="font-semibold">À compléter</h2><span className="rounded-full bg-marker px-2.5 py-1 text-xs text-marker-foreground">{remaining.length}</span></div>{markerList}<p className="mt-5 text-xs leading-relaxed text-muted-foreground">Ces éléments restent dans votre document et pourront être complétés dans Word.</p></aside></div>
      </>}
      {step === 3 && <>
        {draft.exampleMode && <p className="mb-6 flex items-center gap-2 text-xs text-muted-foreground"><Info className="size-4" />Thèmes d’exemple · Le téléchargement Word nécessite le service.</p>}
        {!draft.exampleMode && themes.isPending && <div className="grid gap-5 sm:grid-cols-3">{[1, 2, 3].map(i => <div key={i} className="h-[330px] animate-pulse rounded-lg bg-muted" aria-label="Chargement des thèmes" />)}</div>}
        {!draft.exampleMode && themes.isError && <div className="border-y py-10 text-center"><FileText className="mx-auto mb-4 size-8 text-muted-foreground" /><p className="mb-2 font-medium">Les thèmes ne sont pas disponibles</p><p className="mb-5 text-sm text-muted-foreground">{themes.error instanceof ApiError ? themes.error.message : "Impossible de joindre le service"}</p><Button variant="outline" onClick={() => void themes.refetch()}><RotateCcw />Réessayer</Button></div>}
        {availableThemes && <div className="grid gap-5 sm:grid-cols-3">{Object.entries(availableThemes).map(([key, theme]) => <ThemeCard key={key} theme={theme} selected={draft.theme === key} onSelect={() => { setDraft(d => ({ ...d, theme: key })); render.reset(); }} />)}</div>}
        {availableThemes && Object.keys(availableThemes).length === 0 && <p role="status">Aucun thème n’est proposé par le service. <Button variant="link" onClick={() => void themes.refetch()}>Réessayer</Button></p>}
      </>}
      {step === 4 && structure && <>
        <div className="border-y py-7"><div className="flex items-start gap-4"><div className="upload-icon shrink-0"><FileText className="size-6" /></div><div className="min-w-0"><h2 className="break-words text-lg font-semibold">{structure.meta.titre}</h2><p className="mt-2 text-xs text-muted-foreground">{structure.meta.matiere} · {structure.meta.code_ue}</p></div></div><dl className="mt-7 grid grid-cols-2 gap-6 sm:grid-cols-4">{[["Format", "Word (.docx)"], ["Thème", availableThemes?.[draft.theme]?.nom || draft.theme], ["Sections", allNodes.filter(n => n.type === "section").length], ["À compléter", remaining.length]].map(([key, value]) => <div key={key}><dt className="text-xs text-muted-foreground">{key}</dt><dd className="mt-2 text-sm font-semibold">{value}</dd></div>)}</dl></div>
        <div className="py-10 text-center">{render.isSuccess ? <><div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-secondary text-success"><Check /></div><p aria-live="polite" className="font-semibold">Votre document Word est prêt !</p><p className="mt-2 text-xs text-muted-foreground">{render.data.filename}</p><div className="mt-6 flex flex-wrap justify-center gap-3"><Button onClick={() => downloadDocument(render.data)}><Download />Télécharger à nouveau</Button><Button variant="outline" onClick={clear}><FileText />Nouveau compte rendu</Button></div></> : <><Button size="lg" className="h-12 max-w-full whitespace-normal" disabled={render.isPending || !availableThemes?.[draft.theme]} onClick={() => render.mutate()}>{render.isPending ? <LoaderCircle className="animate-spin" /> : <Download />}{render.isPending ? "Génération en cours…" : "Générer le document Word"}</Button><p className="mt-4 text-xs text-muted-foreground">{draft.exampleMode && !apiConfigured ? "Exemple prêt. Configurez le service pour télécharger le fichier Word." : "Votre compte rendu sera téléchargé au format .docx."}</p>{remaining.length > 0 && <p className="mt-2 text-xs text-muted-foreground">{remaining.length} éléments pourront être complétés dans Word.</p>}</>}<ErrorList errors={render.error instanceof ApiError ? render.error.messages : []} /></div>
      </>}
      <div className="wizard-footer"><div>{step === 1 ? <span className="flex items-center gap-2 text-[11px] text-muted-foreground"><LockKeyhole className="size-3.5 shrink-0" /><span>Vos données restent dans votre navigateur.</span></span> : <Button variant="ghost" onClick={() => go(step - 1)}><ArrowLeft />Retour</Button>}</div>{step < 4 && <Button className="h-11 px-5" disabled={!structure || (step === 3 && !availableThemes?.[draft.theme])} onClick={() => go(step + 1)}>Continuer<ArrowRight /></Button>}</div>
      {storageError && <p role="status" className="mt-4 text-xs text-destructive">La sauvegarde locale est indisponible. Ne fermez pas cette page avant de terminer.</p>}
    </main>
    <footer className="border-t"><div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-4 px-5 py-6 text-[11px] text-muted-foreground md:px-8"><span>ReYo · Le compte rendu, simplement.</span><div className="flex items-center gap-5"><span className="hidden items-center gap-1.5 sm:flex"><ShieldCheck className="size-3.5" />Sans compte. Sans installation.</span><Button variant="ghost" className="h-auto p-0 text-[11px] text-muted-foreground" onClick={() => setConfirmErase(true)}><Trash2 className="size-3.5" />Effacer mes données</Button></div></div></footer>
    <Sheet open={help} onOpenChange={setHelp}><SheetContent><SheetTitle>À propos de ReYo</SheetTitle><SheetDescription>Vos TP, prêts à rendre.</SheetDescription><div className="mt-6 space-y-5 text-sm leading-relaxed"><p>ReYo prépare vos comptes rendus de travaux pratiques au format Word.</p><p>Votre brouillon est conservé dans ce navigateur. Seule la génération envoie votre document au service configuré.</p><p>{apiConfigured ? "L’adresse du service est configurée." : "L’adresse du service n’est pas encore configurée. L’exemple permet de parcourir les quatre étapes sans service."}</p><p>Version 1.0</p></div></SheetContent></Sheet>
    <Sheet open={confirmErase} onOpenChange={setConfirmErase}><SheetContent><SheetTitle>Effacer vos données ?</SheetTitle><SheetDescription>Le brouillon et toutes vos modifications seront supprimés de ce navigateur.</SheetDescription><div className="mt-6 flex flex-wrap gap-3"><Button variant="destructive" onClick={clear}><Trash2 />Effacer mes données</Button><Button variant="outline" onClick={() => setConfirmErase(false)}>Annuler</Button></div></SheetContent></Sheet>
  </div>;
}
