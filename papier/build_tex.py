#!/usr/bin/env python3
"""Convertit papier/article.md en LaTeX natif et le compile avec Tectonic.

Convertisseur taillé pour la structure de cet article (titres, tableaux
GFM, figures, gras/italique/code, citations, guillemets français). Produit
article.tex puis Garnier_2026_lit-charts_LaTeX.pdf.

    python papier/build_tex.py
"""

import re
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parent
ARTICLE = RACINE / "article.md"
TEX = RACINE / "article.tex"
PDF_FINAL = RACINE / "Garnier_2026_lit-charts_LaTeX.pdf"

TITRE = ("«~That's kino anon~» : les charts de /lit/\\\\comme dispositifs "
         "gamifiés")
SOUS_TITRE = ("D'une lecture qualitative à une mesure computationnelle du corpus")


def echapper(texte):
    """Échappe les caractères spéciaux LaTeX dans du texte courant."""
    remplacements = [
        ("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
        ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
        ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
    ]
    for a, b in remplacements:
        texte = texte.replace(a, b)
    return texte


def inline(texte):
    """Traite le balisage en ligne d'un fragment déjà échappé au besoin.

    On protège d'abord le code `…` et les liens, on échappe le reste,
    puis on rétablit gras/italique. L'ordre évite d'échapper à l'intérieur
    du code et de casser les URLs.
    """
    jetons = {}

    def sceller(motif, gabarit, source):
        def rem(m):
            cle = f"@@{len(jetons)}@@"
            jetons[cle] = gabarit(m)
            return cle
        return re.sub(motif, rem, source)

    # Code `x` -> \texttt (contenu échappé pour le mode verbatim-léger)
    texte = sceller(r"`([^`]+)`",
                    lambda m: r"\texttt{" + echapper(m.group(1)) + "}", texte)
    # Liens [txt](url) -> \href
    texte = sceller(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                    lambda m: r"\href{" + m.group(2).replace("%", r"\%").replace("#", r"\#")
                    + "}{" + echapper(m.group(1)) + "}", texte)
    # URL nue <url>
    texte = sceller(r"<(https?://[^>]+)>",
                    lambda m: r"\url{" + m.group(1) + "}", texte)

    texte = echapper(texte)

    # Gras puis italique (sur le texte échappé)
    texte = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", texte)
    texte = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", texte)

    # Typographie française : guillemets, tirets, espaces fines
    texte = texte.replace("« ", "«~").replace(" »", "~»")
    texte = texte.replace("—", "---").replace("–", "--")
    texte = texte.replace(" :", "~:").replace(" ;", "~;")
    texte = texte.replace(" %", "~\\%")

    for cle, val in jetons.items():
        texte = texte.replace(cle, val)
    return texte


def table(lignes):
    """Convertit un tableau GFM (liste de lignes) en tabular."""
    lignes = [l for l in lignes if l.strip()]
    entete = [c.strip() for c in lignes[0].strip("|").split("|")]
    aligns = lignes[1]
    col = []
    for a in aligns.strip("|").split("|"):
        a = a.strip()
        col.append("r" if a.endswith(":") and not a.startswith(":") else "l")
    corps = lignes[2:]
    out = [r"\begin{center}\small",
           r"\begin{tabular}{" + "".join(col) + "}",
           r"\toprule",
           " & ".join(r"\textbf{" + inline(c) + "}" for c in entete) + r" \\",
           r"\midrule"]
    for l in corps:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        out.append(" & ".join(inline(c) for c in cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]
    return "\n".join(out)


def corps_latex(md):
    """Convertit le corps markdown (après le front matter) en LaTeX."""
    lignes = md.split("\n")
    out, i = [], 0
    dans_refs = False
    while i < len(lignes):
        l = lignes[i]
        # Bloc de code ``` … ```
        if l.startswith("```"):
            bloc = []
            i += 1
            while i < len(lignes) and not lignes[i].startswith("```"):
                bloc.append(lignes[i]); i += 1
            out.append(r"\begin{quote}\ttfamily\small\obeylines")
            out += [echapper(b) for b in bloc]
            out.append(r"\end{quote}")
            i += 1
            continue
        # Tableau
        if l.strip().startswith("|") and i + 1 < len(lignes) and set(lignes[i+1].strip()) <= set("|-: "):
            bloc = []
            while i < len(lignes) and lignes[i].strip().startswith("|"):
                bloc.append(lignes[i]); i += 1
            out.append(table(bloc))
            continue
        # Figure
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l.strip())
        if m:
            out.append(r"\begin{figure}[htbp]\centering")
            out.append(r"\includegraphics[width=0.86\linewidth]{" + m.group(2) + "}")
            out.append(r"\end{figure}")
            i += 1
            continue
        # Titres
        if l.startswith("## "):
            titre = l[3:].strip()
            dans_refs = titre.startswith("Références")
            if titre == "Références":
                out.append(r"\section*{Références}\small\setlength{\parindent}{-1.2em}\setlength{\leftskip}{1.2em}")
            else:
                out.append(r"\section*{" + inline(titre) + "}")
            i += 1
            continue
        if l.startswith("### "):
            out.append(r"\subsection*{" + inline(l[4:].strip()) + "}")
            i += 1
            continue
        # Caption de figure en gras (**Figure n.** …)
        if re.match(r"\*\*(Tableau|Figure|Table)", l):
            out.append(r"\noindent " + inline(l) + r"\\[-0.2em]")
            i += 1
            continue
        # Paragraphe vide
        if not l.strip():
            out.append("")
            i += 1
            continue
        # Séparateur horizontal
        if l.strip() == "---":
            out.append("")
            i += 1
            continue
        # Paragraphe normal (une entrée de biblio en mode refs = un paragraphe)
        out.append(inline(l))
        i += 1
    return "\n".join(out)


def construire():
    texte = ARTICLE.read_text(encoding="utf-8")
    segments = re.split(r"\n---\n", texte)
    bloc_resume = segments[1]
    corps_md = "\n---\n".join(segments[2:])

    def extraire(entete):
        m = re.search(rf"## {entete}\n\n(.+?)(?=\n## |\n\*\*Mots|\n\*\*Key|\Z)",
                      bloc_resume, re.S)
        return m.group(1).strip() if m else ""
    resume = inline(extraire("Résumé"))
    abstract = inline(extraire("Abstract"))
    mots = re.search(r"\*\*Mots-clés :\*\* (.+)", bloc_resume)
    keys = re.search(r"\*\*Keywords:\*\* (.+)", bloc_resume)
    mots = inline(mots.group(1)) if mots else ""
    keys = inline(keys.group(1)) if keys else ""

    return PREAMBULE.format(
        titre=TITRE, sous_titre=SOUS_TITRE,
        resume=resume, abstract=abstract, mots=mots, keys=keys,
        corps=corps_latex(corps_md))


PREAMBULE = r"""\documentclass[11pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[french]{{babel}}
\usepackage{{lmodern}}
\usepackage[margin=2.3cm]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\usepackage{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage{{microtype}}
\usepackage{{parskip}}
\hypersetup{{colorlinks=true, linkcolor=black, urlcolor=[RGB]{{26,79,138}},
            citecolor=black, pdftitle={{That's kino anon — les charts de /lit/}},
            pdfauthor={{Marc Garnier}}}}
\pagestyle{{fancy}}\fancyhf{{}}
\fancyhead[L]{{\footnotesize\color{{gray}}Garnier · Les charts de /lit/ comme dispositifs gamifiés}}
\fancyhead[R]{{\footnotesize\color{{gray}}SocArXiv · préprint}}
\fancyfoot[C]{{\footnotesize\color{{gray}}\thepage}}
\renewcommand{{\headrulewidth}}{{0.2pt}}
\setlength{{\emergencystretch}}{{2em}}

\begin{{document}}
\thispagestyle{{fancy}}

\begin{{center}}
{{\footnotesize\sffamily\color{{gray}}\fbox{{\textsc{{Préprint}} · SocArXiv · sciences de l'information et de la communication · 2026}}}}\\[1.4em]
{{\LARGE\bfseries {titre}\par}}\\[0.5em]
{{\large\itshape {sous_titre}\par}}\\[1em]
{{\large Marc Garnier\par}}\\[0.3em]
{{\footnotesize\itshape Version étendue du travail présenté au séminaire COM~885 · juillet 2026\\
Code et données : \url{{https://github.com/marcgarnier/lit-charts}}\par}}
\end{{center}}
\vspace{{0.8em}}

\begin{{center}}\begin{{minipage}}{{0.92\linewidth}}
\small
{{\sffamily\footnotesize\bfseries RÉSUMÉ}}\\[0.3em]
{resume}\\[0.4em]
\textbf{{Mots-clés :}} {mots}\\[0.9em]
{{\sffamily\footnotesize\bfseries ABSTRACT}}\\[0.3em]
{abstract}\\[0.4em]
\textbf{{Keywords:}} {keys}
\end{{minipage}}\end{{center}}
\vspace{{1em}}

{corps}

\end{{document}}
"""


def main():
    TEX.write_text(construire(), encoding="utf-8")
    print(f"{TEX.name} écrit ({TEX.stat().st_size // 1024} Ko)")
    r = subprocess.run(
        ["tectonic", "-X", "compile", str(TEX), "--outdir", str(RACINE), "-Z", "continue-on-errors"],
        capture_output=True, text=True)
    produit = RACINE / "article.pdf"
    if produit.exists():
        produit.replace(PDF_FINAL)
        print(f"{PDF_FINAL.name} — {PDF_FINAL.stat().st_size // 1024} Ko")
    else:
        print("Échec de compilation :\n", r.stderr[-2000:])


if __name__ == "__main__":
    main()
