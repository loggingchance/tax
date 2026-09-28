import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from round2_fixes import (  # noqa: E402
    card_html,
    detail_sidebar,
    shared_footer_dialog,
    source_section,
    timing_section,
    update_html_files,
    update_records,
    validate,
    write_min_json,
)


GA_ORDER = [
    "GA-JOBS-001",
    "GA-QJ-001",
    "GA-INV-001",
    "GA-OPTINV-001",
    "GA-RD-001",
    "GA-RETRAIN-001",
    "GA-CHILD-001",
]


ADDITIONS = [
    {
        "id": "GA-QJ-001",
        "title": "Quality Jobs Credit",
        "jurisdiction": "Georgia",
        "jurisdiction_type": "State",
        "state_code": "GA",
        "activity": "Jobs",
        "slug": "ga-qj-001",
        "sourcebook_page": None,
        "publication_edition": "2026",
        "publication_revision_date": "September 28, 2026 web addition",
        "credit_amount_calculation": "Credit amount varies by wage level for taxpayers creating at least 50 new quality jobs; excess credit may be usable against Georgia withholding.",
        "business_fit_and_eligible_activity": "Larger forest-products employers creating substantial new Georgia jobs at or above the county wage threshold should screen this alongside the regular Job Tax Credit.",
        "eligibility_and_practical_use": "This is a high-growth hiring credit rather than an equipment credit. It is most likely to matter for a mill, engineered-wood plant, or other expansion adding a large block of qualifying jobs; small logging contractors and modest staffing increases generally will not clear the threshold.",
        "illustrative_business_benefit": "Use-of-credit illustration, not an estimated award: if the completed Georgia calculation establishes a $75,000 credit and the taxpayer has sufficient Georgia liability or approved withholding offset capacity, the usable benefit depends on the annual limits and filing requirements. The job count, wage level, location, and withholding approval drive the actual value.",
        "timing_first_action": "Before assigning value, test the hiring plan against the new-quality-job count, wage, work-week, Georgia location, and filing requirements; file the required Georgia forms on time.",
        "refundable": "No cash refund; excess credit may be taken against Georgia withholding if requirements are met.",
        "transferable": "No",
        "carryforward": "Not established in the cited summary. Confirm the period before relying on unused credits.",
        "additional_detail": "",
        "official_sources": [
            {
                "label": "Georgia Department of Revenue — Quality Jobs Credit",
                "publisher": "Georgia Department of Revenue",
                "url": "https://dor.georgia.gov/quality-jobs-credit",
            }
        ],
        "difficulty_score": 2,
        "difficulty_label": "Certified",
        "forest_products_fit_score": 2,
        "forest_products_fit_label": "Conditional",
        "qualification": "Contains a qualification or item to confirm before relying on the credit.",
        "activity_tags": ["Jobs", "Workforce"],
        "business_relevance": ["Primary processing", "Secondary manufacturing"],
        "timing_tags": ["Advance action required", "Tax-return or annual claim"],
        "refundable_status": "no",
        "transferable_status": "no",
        "search_synonyms": "quality job high wage withholding",
        "url": "/credits/georgia/ga-qj-001/",
    },
    {
        "id": "GA-CHILD-001",
        "title": "Georgia Employer Childcare Expense Credit",
        "jurisdiction": "Georgia",
        "jurisdiction_type": "State",
        "state_code": "GA",
        "activity": "Workforce",
        "slug": "ga-child-001",
        "sourcebook_page": None,
        "publication_edition": "2026",
        "publication_revision_date": "September 28, 2026 web addition",
        "credit_amount_calculation": "$1,000 per child in the first year and $500 per child in later years for eligible child-care payments; statewide annual cap applies.",
        "business_fit_and_eligible_activity": "Forest-products employers making eligible child-care payments for employees can screen this as a workforce-support credit beginning with 2026 tax years.",
        "eligibility_and_practical_use": "This is a general employer workforce credit, not a forestry-specific incentive. It may matter where child care is a real hiring or retention barrier and the employer pays a qualifying child-care facility directly for employees' children.",
        "illustrative_business_benefit": "A mill makes eligible payments for 12 employees' children in its first qualifying year. At $1,000 per child, the nominal credit would be $12,000 before preapproval, statewide cap, income-tax-liability, and documentation limits.",
        "timing_first_action": "Seek preapproval through the Georgia Tax Center before relying on the credit; document eligible payments, covered employees, child age, and the qualifying child-care facility.",
        "refundable": "No",
        "transferable": "No",
        "carryforward": "No carryforward or carryback is allowed under the cited summary.",
        "additional_detail": "",
        "official_sources": [
            {
                "label": "Georgia Department of Revenue — Georgia Employer Childcare Expense Credit",
                "publisher": "Georgia Department of Revenue",
                "url": "https://dor.georgia.gov/georgia-employer-childcare-expense-credit",
            }
        ],
        "difficulty_score": 2,
        "difficulty_label": "Certified",
        "forest_products_fit_score": 2,
        "forest_products_fit_label": "Conditional",
        "qualification": "Contains a qualification or item to confirm before relying on the credit.",
        "activity_tags": ["Jobs", "Workforce"],
        "business_relevance": ["Logging / harvesting", "Primary processing", "Secondary manufacturing"],
        "timing_tags": ["Advance action required", "Tax-return or annual claim"],
        "refundable_status": "no",
        "transferable_status": "no",
        "search_synonyms": "child care childcare workforce retention",
        "url": "/credits/georgia/ga-child-001/",
    },
]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def header(active=""):
    states = ' aria-current="page"' if active == "states" else ""
    activity = ' aria-current="page"' if active == "activity" else ""
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <a class="brand" href="/"><span>Forest Products</span><strong>Tax Credit Sourcebook</strong></a>
  <nav aria-label="Primary"><a href="/search/">Search</a><a href="/states/"{states}>States</a><a href="/activity/"{activity}>Activities</a><a href="/updates/">Updates</a><a href="/compare/">Compare</a><a href="/about/">About</a><a class="pdf-link" href="/assets/pdf/NFPTC-2026.pdf" download>Full Sourcebook</a></nav>
</header>'''


def georgia_detail_sidebar(record):
    first = record.get("timing_first_action", "")
    if len(first) > 105:
        first = first[:105].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."
    sourcebook = ""
    if record.get("sourcebook_page"):
        sourcebook = f'<a class="button secondary" href="/sourcebook/#page-{esc(record.get("sourcebook_page"))}">Sourcebook page {esc(record.get("sourcebook_page"))}</a>'
    else:
        sourcebook = '<span class="button secondary" aria-disabled="true">Web addition</span>'
    return f'''<aside class="detail-sidebar"><h2>Key facts</h2><dl class="key-facts"><div><dt>Refundable</dt><dd>{esc(record.get("refundable") or "Not established in the sourcebook")}</dd></div><div><dt>Transferable</dt><dd>{esc(record.get("transferable") or "Not established in the sourcebook")}</dd></div><div><dt>Carryforward</dt><dd>{esc(record.get("carryforward") or "Not established in the sourcebook")}</dd></div><div><dt>Difficulty</dt><dd>{esc(record.get("difficulty_score"))} of 3 - {esc(record.get("difficulty_label"))}</dd></div><div><dt>Fit</dt><dd>{esc(record.get("forest_products_fit_score"))} of 3 - {esc(record.get("forest_products_fit_label"))}</dd></div><div><dt>First action</dt><dd>{esc(first)}</dd></div></dl>{sourcebook}<button type="button" class="compare-toggle" data-compare-id="{esc(record["id"])}">Compare</button><button type="button" data-print>Print</button><button type="button" data-feedback>Report a correction</button></aside>'''


def head(title, description, canonical):
    return f'''<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:site_name" content="National Forest Products Tax Credit Sourcebook">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="https://tax.lumbermen.org/assets/social/nfptc-2026-og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="National Forest Products Tax Credit Sourcebook cover image with forest-products mill scene">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="https://tax.lumbermen.org/assets/social/nfptc-2026-og.jpg">
<meta name="theme-color" content="#1f4d38">
<link rel="icon" href="/assets/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/css/styles.css?v=20260927h">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"National Forest Products Tax Credit Sourcebook","url":"https://tax.lumbermen.org","potentialAction":{{"@type":"SearchAction","target":"https://tax.lumbermen.org/search/?q={{search_term_string}}","query-input":"required name=search_term_string"}}}}</script>
</head>'''


def upsert_programs(records):
    by_id = {record["id"]: record for record in records}
    for addition in ADDITIONS:
        by_id[addition["id"]] = {**by_id.get(addition["id"], {}), **addition}
    output = []
    inserted = False
    for record in records:
        if record["id"] == "HI-RETITC-001" and not inserted:
            for rid in GA_ORDER:
                output.append(by_id[rid])
            inserted = True
        if not record["id"].startswith("GA-") or record["id"] not in GA_ORDER:
            output.append(by_id.get(record["id"], record))
    return output


def update_states():
    path = ROOT / "content/states.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["Georgia"] = GA_ORDER
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def document(cards_html, main_html, title, description, canonical, active=""):
    return f'''<!doctype html>
<html lang="en">
{head(title, description, canonical)}
<body class="">
{header(active)}
<main id="main" tabindex="-1">
{main_html}
</main>
{shared_footer_dialog()}
<div class="compare-tray" data-compare-tray hidden></div>
<script src="/assets/js/site.js?v=20260927c" defer></script>
</body>
</html>
'''.replace("{cards}", cards_html)


def write_georgia_state(records):
    by_id = {record["id"]: record for record in records}
    selected = [by_id[rid] for rid in GA_ORDER]
    cards = "".join(card_html(record) for record in selected)
    main = f'''<nav class="breadcrumbs"><a href="/">Home</a> / <a href="/states/">States</a> / Georgia</nav>
<section class="page-heading"><h1>Georgia</h1><p>5 programs in the 2026 edition, plus 2 web additions from current Georgia Department of Revenue guidance. The 3-of-3 fit rating marks the broadest forest-products route within a specific program; lower-rated programs may still warrant review when the project facts match.</p><p><a class="button secondary" href="/sourcebook/#page-82">View this section in the full 2026 Sourcebook</a> <a class="button" href="/search/?state=Georgia">Filter/search Georgia</a></p></section>
<div class="summary-strip"><span>7 programs</span><span>0 refundable</span><span>Easiest: Job Tax Credit</span><span>Top: Jobs, Workforce, Investment</span></div>
<h2 class="list-heading">Programs</h2><section class="program-list">{cards}</section>'''
    path = ROOT / "states/georgia/index.html"
    path.write_text(
        document(cards, main, "Georgia | National Forest Products Tax Credit Sourcebook", "Georgia tax credit programs for forest-products businesses.", "https://tax.lumbermen.org/states/georgia/", "states"),
        encoding="utf-8",
        newline="\n",
    )


def write_detail_pages(records):
    by_id = {record["id"]: record for record in records}
    related = {rid: "".join(card_html(by_id[other]) for other in GA_ORDER if other != rid) for rid in GA_ORDER}
    for rid in ("GA-QJ-001", "GA-CHILD-001"):
        record = by_id[rid]
        detail_json = (
            f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"GovernmentService","name":'
            f'"{esc(record["title"])}","areaServed":"Georgia","url":"https://tax.lumbermen.org{esc(record["url"])}","provider":{{"@type":"Organization","name":"Georgia"}}}}</script>'
        )
        main = f'''<nav class="breadcrumbs"><a href="/">Home</a> / <a href="/states/">States</a> / <a href="/states/georgia/">Georgia</a> / {esc(record["title"])}</nav>
<article class="detail" data-program-id="{esc(record["id"])}" data-program-title="{esc(record["title"])}" data-jurisdiction="Georgia">
<header class="detail-header"><p class="eyebrow">Georgia · {esc(record["activity"])} · {esc(record["id"])}</p><h1>{esc(record["title"])}</h1><p>{esc(record["publication_revision_date"])}.</p></header>
<div class="detail-layout"><div class="detail-main"><section class="benefit-panel"><h2>Credit amount / calculation</h2><p>{esc(record["credit_amount_calculation"])}</p></section><section><h2>Business fit and eligible activity</h2><p>{esc(record["business_fit_and_eligible_activity"])}</p></section><section><h2>Eligibility and practical use</h2><p>{esc(record["eligibility_and_practical_use"])}</p></section><section class="calc-panel"><h2>Illustrative business benefit</h2><p>{esc(record["illustrative_business_benefit"])}</p></section>{timing_section(record)}{source_section(record)}<section><h2>Related programs</h2><div class="program-list compact">{related[rid]}</div></section><aside class="disclaimer">This is a screening guide, not tax advice or a guarantee of eligibility. Confirm current rules with the administering agency and a qualified tax adviser.</aside></div>{georgia_detail_sidebar(record)}</div>
</article>'''
        page = document("", main, f'{record["title"]} | Georgia Tax Credit', record["credit_amount_calculation"], f'https://tax.lumbermen.org{record["url"]}')
        page = page.replace("</head>", detail_json + "</head>")
        out = ROOT / f'credits/georgia/{record["slug"]}/index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8", newline="\n")

    for path in (ROOT / "credits/georgia").glob("*/index.html"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'data-program-id="([^"]+)"', text)
        if not match or match.group(1) not in related:
            continue
        text = re.sub(
            r'<section><h2>Related programs</h2><div class="program-list compact">.*?</div></section>',
            f'<section><h2>Related programs</h2><div class="program-list compact">{related[match.group(1)]}</div></section>',
            text,
            count=1,
            flags=re.S,
        )
        path.write_text(text, encoding="utf-8", newline="\n")


def write_activity_page(records, tag, slug):
    selected = [record for record in records if tag in record.get("activity_tags", [])]
    cards = "".join(card_html(record) for record in selected)
    main = f'''<section class="page-heading"><h1>{esc(tag)}</h1><p>{len(selected)} programs connected to {esc(tag.lower())}. Search results preserve context and do not imply eligibility.</p></section><h2 class="list-heading">Programs</h2><section class="program-list">{cards}</section>'''
    path = ROOT / f"activity/{slug}/index.html"
    path.write_text(
        document(cards, main, f"{tag} Credits | National Forest Products Tax Credit Sourcebook", f"Browse {tag} tax-credit programs for forest-products businesses.", f"https://tax.lumbermen.org/activity/{slug}/", "activity"),
        encoding="utf-8",
        newline="\n",
    )


def update_sitemap():
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    additions = [
        "https://tax.lumbermen.org/credits/georgia/ga-qj-001/",
        "https://tax.lumbermen.org/credits/georgia/ga-child-001/",
    ]
    for loc in additions:
        if loc not in text:
            text = text.replace("</urlset>", f"  <url><loc>{loc}</loc></url>\n</urlset>")
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    programs_path = ROOT / "content/programs.json"
    records = json.loads(programs_path.read_text(encoding="utf-8"))
    records = upsert_programs(records)
    update_records(records)
    validate(records)
    programs_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_states()
    write_min_json(records)
    update_html_files(records)
    write_georgia_state(records)
    write_detail_pages(records)
    write_activity_page(records, "Jobs", "jobs")
    write_activity_page(records, "Workforce", "workforce")
    update_sitemap()
    print("Georgia credits updated.")


if __name__ == "__main__":
    main()
