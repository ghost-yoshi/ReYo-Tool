import { createFileRoute } from "@tanstack/react-router";
import { ReYo } from "@/components/reyo";
import { DraftProvider } from "@/lib/draft";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "ReYo — Créer un compte rendu de TP" },
    { name: "description", content: "Importez, relisez et mettez en forme votre compte rendu de TP, puis téléchargez votre document Word." },
    { property: "og:title", content: "ReYo — Créer un compte rendu de TP" },
    { property: "og:description", content: "Du TP au compte rendu Word, en quatre étapes." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Index,
});
function Index() { return <DraftProvider><ReYo /></DraftProvider>; }
