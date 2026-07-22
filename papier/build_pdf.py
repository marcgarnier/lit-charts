#!/usr/bin/env python3
"""Rend papier/article.md en PDF de préprint, au format SocArXiv.

HTML mis en page par CSS paginé, imprimé par le Chrome du système via
Playwright (channel="chrome" : aucun Chromium à télécharger). Les figures
sont incorporées en data URI pour être indépendantes du dossier courant.

    python papier/build_pdf.py
"""

import base64
import re
from pathlib import Path

import markdown

RACINE = Path(__file__).resolve().parent
ARTICLE = RACINE / "article.md"
FIGURES = RACINE / "figures"
SORTIE = RACINE / "Garnier_2026_lit-charts_SocArXiv.pdf"

TITRE = ("« That's kino anon » : les charts de /lit/ comme dispositifs "
         "gamifiés")
ENTETE_COURT = "Garnier · Les charts de /lit/ comme dispositifs gamifiés"


def inliner_images(html):
    """Remplace les <img src="figures/x.png"> par des data URI."""
    def remplace(m):
        chemin = FIGURES / Path(m.group(1)).name
        b64 = base64.b64encode(chemin.read_bytes()).decode("ascii")
        return f'src="data:image/png;base64,{b64}"'
    return re.sub(r'src="(figures/[^"]+)"', remplace, html)


def construire_html():
    texte = ARTICLE.read_text(encoding="utf-8")
    segments = re.split(r"\n---\n", texte)
    # seg0 titre/byline, seg1 résumé+abstract, seg2… corps
    bloc_resume = segments[1].strip()
    corps_md = "\n---\n".join(segments[2:]).strip()

    # --- Résumé / Abstract : découpés pour un cadre dédié ---
    def extraire(source, entete):
        m = re.search(rf"## {entete}\n\n(.+?)(?=\n## |\Z)", source, re.S)
        return m.group(1).strip() if m else ""
    resume_fr = extraire(bloc_resume, "Résumé")
    resume_en = extraire(bloc_resume, "Abstract")

    md = markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"])
    corps_html = inliner_images(md.convert(corps_md))
    resume_fr_html = markdown.markdown(resume_fr)
    resume_en_html = markdown.markdown(resume_en)

    return TEMPLATE.format(
        titre=TITRE,
        resume_fr=resume_fr_html,
        resume_en=resume_en_html,
        corps=corps_html,
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 2.4cm 2.2cm 2.2cm 2.2cm;
  }}
  html {{ font-family: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif; }}
  body {{
    margin: 0; color: #111; font-size: 10.5pt; line-height: 1.42;
    text-align: justify; hyphens: auto;
  }}

  /* ---- Bandeau de préprint ---- */
  .banner {{
    border: 1px solid #999; border-radius: 3px;
    padding: 5pt 9pt; margin-bottom: 20pt;
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 7.6pt; letter-spacing: .04em; color: #555;
    display: flex; justify-content: space-between;
  }}
  .banner b {{ color: #333; letter-spacing: .12em; }}

  /* ---- Titre ---- */
  h1.doc-title {{
    font-size: 17pt; line-height: 1.22; margin: 0 0 12pt;
    text-align: center; font-weight: 600; hyphens: none;
  }}
  .byline {{ text-align: center; margin-bottom: 3pt; font-size: 11.5pt; }}
  .affil {{ text-align: center; color: #444; font-size: 9.5pt;
            font-style: italic; margin-bottom: 16pt; }}

  /* ---- Cadre résumé ---- */
  .abstract {{
    margin: 0 8pt 6pt; padding: 11pt 15pt;
    background: #f7f7f5; border: 1px solid #e2e2dc; border-radius: 3px;
    font-size: 9.6pt; line-height: 1.4;
  }}
  .abstract h3 {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 8.4pt; letter-spacing: .1em; text-transform: uppercase;
    color: #666; margin: 0 0 5pt; font-weight: 600;
  }}
  .abstract h3.second {{ margin-top: 11pt; }}
  .abstract p {{ margin: 0; }}

  /* ---- Corps ---- */
  h2 {{
    font-size: 12pt; margin: 17pt 0 7pt; font-weight: 600;
    line-height: 1.25; hyphens: none; page-break-after: avoid;
  }}
  h3 {{
    font-size: 10.5pt; margin: 12pt 0 5pt; font-weight: 600;
    font-style: italic; hyphens: none; page-break-after: avoid;
  }}
  p {{ margin: 0 0 6.5pt; }}
  a {{ color: #1a4f8a; text-decoration: none; word-break: break-word; }}
  strong {{ font-weight: 600; }}

  /* ---- Tableaux ---- */
  table {{
    width: 100%; border-collapse: collapse; margin: 8pt 0 12pt;
    font-size: 9.2pt; page-break-inside: avoid;
  }}
  th, td {{ padding: 3pt 7pt; border-bottom: .5pt solid #ccc; }}
  thead th {{ border-top: 1pt solid #333; border-bottom: 1pt solid #333;
              text-align: left; font-weight: 600; }}
  tbody tr:last-child td {{ border-bottom: 1pt solid #333; }}
  td:nth-child(n+2), th:nth-child(n+2) {{ text-align: right;
    font-variant-numeric: tabular-nums; white-space: nowrap; }}

  /* ---- Figures ---- */
  img {{ display: block; max-width: 88%; margin: 10pt auto 4pt; }}
  p img + em, .figcap {{ display: block; text-align: center; }}

  /* ---- Références : retrait négatif ---- */
  h2#references + p, .refs p {{ }}
  .refs {{ font-size: 9.2pt; line-height: 1.34; }}
  .refs p {{ padding-left: 16pt; text-indent: -16pt; margin: 0 0 5pt;
             text-align: left; hyphens: none; }}

  h2, h3 {{ -webkit-column-break-after: avoid; }}
</style></head>
<body>
  <div class="banner">
    <span><b>PRÉPRINT</b> · SocArXiv · sciences de l'information et de la communication</span>
    <span>2026</span>
  </div>

  <h1 class="doc-title">{titre}</h1>
  <p class="byline">Marc Garnier</p>
  <p class="affil">Version étendue du travail présenté au séminaire COM 885 · juillet 2026<br>
     Code et données : github.com/marcgarnier/lit-charts</p>

  <div class="abstract">
    <h3>Résumé</h3>
    {resume_fr}
    <h3 class="second">Abstract</h3>
    {resume_en}
  </div>

  {corps}
</body></html>"""


def marquer_references(html):
    """Enveloppe la liste de références pour le retrait négatif.

    On repère le titre « Références » et on enrobe tout ce qui suit,
    jusqu'au titre suivant (« Annexe »), dans <div class="refs">.
    """
    # Chaque entrée de la biblio est un <p> ; on les regroupe.
    def envelopper(m):
        return f'{m.group(1)}<div class="refs">{m.group(2)}</div>{m.group(3)}'
    motif = re.compile(
        r'(<h2[^>]*>Références</h2>)(.*?)(<h2[^>]*>Annexe)', re.S)
    return motif.sub(envelopper, html)


def main():
    from playwright.sync_api import sync_playwright

    html = marquer_references(construire_html())
    fichier_html = RACINE / "_article_print.html"
    fichier_html.write_text(html, encoding="utf-8")

    entete = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;'
              'font-size:7pt;color:#999;padding:0 1.6cm;display:flex;'
              'justify-content:space-between;">'
              f'<span>{ENTETE_COURT}</span><span>SocArXiv · préprint</span></div>')
    pied = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;'
            'font-size:7.5pt;color:#999;padding:0 1.6cm;text-align:center;">'
            '<span class="pageNumber"></span></div>')

    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        page = nav.new_page()
        page.goto(fichier_html.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(SORTIE), format="A4", print_background=True,
            display_header_footer=True,
            header_template=entete, footer_template=pied,
            margin={"top": "2.4cm", "bottom": "1.7cm",
                    "left": "0cm", "right": "0cm"},
        )
        nav.close()
    fichier_html.unlink(missing_ok=True)
    ko = SORTIE.stat().st_size / 1024
    print(f"{SORTIE.name} — {ko:.0f} Ko")


if __name__ == "__main__":
    main()
