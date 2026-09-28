import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PDF_URL = "/assets/pdf/NFPTC-2026.pdf"
OLD_PDF_RE = re.compile(r"https://drive\.google\.com/file/d/1uvsSiIreZqcPHlvo2IUM_z4EEoFDDmw6/view\?usp=sharing")


def esc(value):
    return html.escape(str(value or ""), quote=True)


def clean_ws(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_text(value):
    value = clean_ws(value)
    value = re.sub(r"\s+\b[Pp]age(?:\s+\d+)?\s*$", "", value).strip()
    return value


def first_sentence(value):
    value = clean_text(value)
    if not value:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", value)
    return clean_text(parts[0])


def short_figure(value):
    value = clean_text(value)
    if not value:
        return ""
    patterns = [
        r"(?:Up to|Generally|Lesser of|Greater of|For 2026\+?:|Through 2030,|Current statute includes|Regular research-credit method|Machinery credit|Production-based|Per-[^.;]+|[0-9]+(?:\.[0-9]+)?%[^.;]+|\$[0-9,]+[^.;]+|[0-9]+(?:\.[0-9]+)?¢/kWh[^.;]+)",
    ]
    candidate = first_sentence(value)
    for pat in patterns:
        m = re.search(pat, candidate, re.I)
        if m:
            candidate = clean_ws(m.group(0))
            break
    candidate = candidate.rstrip(" .;:")
    if len(candidate) <= 60:
        return candidate
    for sep in [",", ";", " plus ", " with ", " subject to ", " and "]:
        idx = candidate.lower().find(sep.strip() if sep.strip() in [",", ";"] else sep, 0, 60)
        if idx > 20:
            return candidate[:idx].rstrip(" ,;:")
    cut = candidate[:60].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut if len(cut) >= 12 else ""


def make_summary(record):
    candidates = [
        record.get("business_fit_and_eligible_activity"),
        record.get("eligibility_and_practical_use"),
        record.get("illustrative_business_benefit"),
        record.get("timing_first_action"),
    ]
    headline = clean_ws(record.get("headline", "")).lower()
    for value in candidates:
        sentence = first_sentence(value)
        if sentence and not sentence.lower().startswith(headline):
            return sentence
    return first_sentence(record.get("credit_amount_calculation"))


PUBLISHER_MAP = {
    "irs.gov": "Internal Revenue Service",
    "www.irs.gov": "Internal Revenue Service",
    "energy.gov": "U.S. Department of Energy",
    "www.energy.gov": "U.S. Department of Energy",
    "revenue.alabama.gov": "Alabama Department of Revenue",
    "labor.alabama.gov": "Alabama Department of Labor",
    "commerce.alaska.gov": "Alaska Department of Commerce",
    "azcommerce.com": "Arizona Commerce Authority",
    "www.azcommerce.com": "Arizona Commerce Authority",
    "azdor.gov": "Arizona Department of Revenue",
    "www.arkansasedc.com": "Arkansas Economic Development Commission",
    "arkansasedc.com": "Arkansas Economic Development Commission",
    "ftb.ca.gov": "California Franchise Tax Board",
    "www.ftb.ca.gov": "California Franchise Tax Board",
    "leg.colorado.gov": "Colorado General Assembly",
    "www.leg.colorado.gov": "Colorado General Assembly",
    "olls.info": "Colorado General Assembly",
    "sos.state.co.us": "Colorado Secretary of State",
    "www.sos.state.co.us": "Colorado Secretary of State",
    "portal.ct.gov": "Connecticut Department of Revenue Services",
    "business.ct.gov": "Connecticut Business Portal",
    "revenue.delaware.gov": "Delaware Division of Revenue",
    "floridarevenue.com": "Florida Department of Revenue",
    "www.floridarevenue.com": "Florida Department of Revenue",
    "georgia.org": "Georgia Department of Economic Development",
    "dor.georgia.gov": "Georgia Department of Revenue",
    "tax.hawaii.gov": "Hawaii Department of Taxation",
    "tax.idaho.gov": "Idaho State Tax Commission",
    "commerce.idaho.gov": "Idaho Department of Commerce",
    "tax.illinois.gov": "Illinois Department of Revenue",
    "iedc.in.gov": "Indiana Economic Development Corporation",
    "tax.iowa.gov": "Iowa Department of Revenue",
    "www.ksrevenue.gov": "Kansas Department of Revenue",
    "ksrevenue.gov": "Kansas Department of Revenue",
    "revenue.ky.gov": "Kentucky Department of Revenue",
    "heritage.ky.gov": "Kentucky Heritage Council",
    "revenue.louisiana.gov": "Louisiana Department of Revenue",
    "www.maine.gov": "State of Maine",
    "marylandtaxes.gov": "Maryland Comptroller",
    "mass.gov": "Commonwealth of Massachusetts",
    "www.michigan.gov": "State of Michigan",
    "www.revenue.state.mn.us": "Minnesota Department of Revenue",
    "dor.ms.gov": "Mississippi Department of Revenue",
    "revisor.mo.gov": "Missouri Revisor of Statutes",
    "revenue.mt.gov": "Montana Department of Revenue",
    "revenue.nebraska.gov": "Nebraska Department of Revenue",
    "www.nheconomy.com": "New Hampshire Department of Business and Economic Affairs",
    "tax.nh.gov": "New Hampshire Department of Revenue Administration",
    "www.njeda.gov": "New Jersey Economic Development Authority",
    "www.tax.newmexico.gov": "New Mexico Taxation and Revenue Department",
    "esd.ny.gov": "Empire State Development",
    "www.ncdor.gov": "North Carolina Department of Revenue",
    "www.tax.nd.gov": "North Dakota Office of State Tax Commissioner",
    "tax.ohio.gov": "Ohio Department of Taxation",
    "oklahoma.gov": "State of Oklahoma",
    "www.oregon.gov": "State of Oregon",
    "www.pa.gov": "Commonwealth of Pennsylvania",
    "tax.ri.gov": "Rhode Island Division of Taxation",
    "dor.sc.gov": "South Carolina Department of Revenue",
    "www.tn.gov": "State of Tennessee",
    "comptroller.texas.gov": "Texas Comptroller",
    "files.tax.utah.gov": "Utah State Tax Commission",
    "tax.vermont.gov": "Vermont Department of Taxes",
    "www.tax.virginia.gov": "Virginia Tax",
    "dor.wa.gov": "Washington Department of Revenue",
    "tax.wv.gov": "West Virginia State Tax Department",
    "revenue.wi.gov": "Wisconsin Department of Revenue",
}


SPECIFIC_SOURCE_TITLES = {
    ("AR-RD-002", "arkansasedc.com"): "Research and Development Tax Credit",
    ("AR-RD-003", "arkansasedc.com"): "Research and Development Tax Credit",
    ("CT-ME-001", "portal.ct.gov"): "Machinery and Equipment Expenditure Tax Credit",
    ("FL-ABILITY-001", "floridarevenue.com"): "Individuals with Unique Abilities Tax Credit",
    ("KY-HIST-001", "heritage.ky.gov"): "Rehabilitation Tax Credits",
    ("KY-QRF-001", "revenue.ky.gov"): "Qualified Research Facility Tax Credit",
    ("MO-WOOD-001", "revisor.mo.gov"): "Revised Statutes of Missouri, Section 135.305",
    ("WI-RD-001", "revenue.wi.gov"): "Wisconsin Research Credits",
}


def source_label(record_id, source):
    url = source.get("url", "")
    host = urlparse(url).netloc.lower().replace("www.", "")
    publisher = PUBLISHER_MAP.get(host) or PUBLISHER_MAP.get(urlparse(url).netloc.lower()) or clean_ws(source.get("publisher")) or host
    raw = clean_ws(source.get("label", ""))
    raw = raw.replace("�", "-")
    raw = re.sub(r"\b\d{2}[A-Z]{3}\d{4}\b", "", raw)
    raw = re.sub(r"official source", "", raw, flags=re.I)
    raw = clean_ws(raw).strip(" -|")
    title = SPECIFIC_SOURCE_TITLES.get((record_id, host))
    if not title and record_id.startswith("CO-EZ") and ("leg.colorado.gov" in host or "olls.info" in host) and ("title 39" in raw.lower() or "olls.info" in host):
        title = "2026 Colorado Revised Statutes, Title 39, Article 30"
    if not title and record_id.startswith("CO-EZ") and "sos.state.co.us" in host:
        title = "Enterprise Zone Regulations, 1 CCR 201-13"
    if not title and record_id.startswith("CO-EZ") and "chapter 364" in raw.lower():
        title = "2026 Session Law, Chapter 364, Sections 30-32 and 42"
    if not title:
        if "|" in raw:
            title = clean_ws(raw.split("|", 1)[0])
        elif " — " in raw:
            parts = [clean_ws(x) for x in raw.split(" — ") if clean_ws(x)]
            title = parts[-1] if parts and parts[0].lower().startswith(publisher.lower()[:10]) else parts[0]
        elif " - " in raw:
            parts = [clean_ws(x) for x in raw.split(" - ") if clean_ws(x)]
            title = parts[-1] if parts and parts[0].lower().startswith(publisher.lower()[:10]) else parts[0]
        elif raw.lower().startswith(publisher.lower()):
            title = clean_ws(raw[len(publisher):].strip(" -:—"))
        else:
            title = raw
    title = clean_ws(title).strip(" -|—")
    title = re.sub(r"^(?:—|-|\s)+", "", title).strip()
    title = re.sub(r"\s+1 CCR$", " 1 CCR 201-13", title)
    if not title:
        title = "Official program information"
    return f"{publisher} — {title}", publisher


def normalize_sources(record):
    seen = set()
    out = []
    for source in record.get("official_sources") or []:
        url = clean_ws(source.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        label, publisher = source_label(record["id"], source)
        out.append({"label": label, "publisher": publisher, "url": url})
    record["official_sources"] = out


def split_using_credit(record):
    text = record.get("timing_first_action", "")
    if "Using the credit" not in text:
        return
    before, after = text.split("Using the credit", 1)
    record["timing_first_action"] = clean_text(before)
    after = after.lstrip(" :•-")
    after = clean_text(after)
    record["using_the_credit"] = after


def update_records(records):
    key_updates = {
        "CO-EZ-INV-001": dict(refundable="No", refundable_status="no", transferable="Not generally transferable", transferable_status="no", carryforward="14 years"),
        "CO-EZ-TRAIN-001": dict(refundable="No", refundable_status="no", transferable="No general sale/transfer authority", transferable_status="no", carryforward="Not established in the sourcebook"),
        "CO-EZ-JOBS-001": dict(refundable="No", refundable_status="no", transferable="Not generally transferable", transferable_status="no", carryforward="5 years for base/ordinary components; 7 years for enhanced-rural components"),
        "CO-EZ-RD-001": dict(refundable="No", refundable_status="no", transferable="No general sale/transfer authority", transferable_status="no", carryforward="Carry forward until used"),
        "NH-RD-001": dict(refundable="No", refundable_status="no", transferable="No general sale/transfer authority", transferable_status="no", carryforward="5 taxable periods after award"),
        "ID-TRI-001": dict(refundable="No", refundable_status="no"),
        "NE-MICRO-001": dict(refundable="Yes", refundable_status="yes"),
        "NM-RD-001": dict(refundable="Conditional", refundable_status="conditional", carryforward="Not established in the sourcebook"),
        "KS-HPIP-TR-001": dict(carryforward="Not established in the sourcebook"),
    }
    for record in records:
        for key, value in list(record.items()):
            if isinstance(value, str):
                record[key] = clean_text(value)
        for field in ("refundable", "transferable", "carryforward"):
            if not record.get(field):
                record[field] = "Not established in the sourcebook"
        record.update(key_updates.get(record["id"], {}))
        split_using_credit(record)
        normalize_sources(record)
        record["headline"] = short_figure(record.get("credit_amount_calculation"))
        record["summary"] = make_summary(record)
        if record["headline"] and record["summary"].lower().startswith(record["headline"].lower()):
            record["summary"] = make_summary({**record, "headline": ""})


def card_html(record):
    refund = {"yes": "Refundable", "no": "Not refundable", "conditional": "Conditional", "not established": "Not established"}.get(record.get("refundable_status"), "Not established")
    formula = f'\n      <p class="formula">{esc(record.get("headline"))}</p>' if record.get("headline") else ""
    return f'''<article class="program-card" data-program-id="{esc(record["id"])}">
    <a class="card-link" href="{esc(record.get("url"))}">
      <span class="card-top"><span class="jurisdiction-pill">{esc(record.get("state_code") or "FED")}</span><span class="program-id">{esc(record["id"])}</span></span>
      <h3>{esc(record.get("title"))}</h3>{formula}
      <p>{esc(record.get("summary") or record.get("timing_first_action"))}</p>
    </a>
    <div class="badges"><span>Fit {esc(record.get("forest_products_fit_score") or "?")}/3</span><span>Difficulty {esc(record.get("difficulty_score") or "?")}/3</span><span>{esc(refund)}</span></div>
    <button type="button" class="compare-toggle" data-compare-id="{esc(record["id"])}">Compare</button>
  </article>'''


def host_label(url):
    return urlparse(url).netloc.replace("www.", "")


def detail_sidebar(record):
    first = clean_text(record.get("timing_first_action"))
    if len(first) > 105:
        first = first[:105].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."
    return f'''<aside class="detail-sidebar"><h2>Key facts</h2><dl class="key-facts"><div><dt>Refundable</dt><dd>{esc(record.get("refundable") or "Not established in the sourcebook")}</dd></div><div><dt>Transferable</dt><dd>{esc(record.get("transferable") or "Not established in the sourcebook")}</dd></div><div><dt>Carryforward</dt><dd>{esc(record.get("carryforward") or "Not established in the sourcebook")}</dd></div><div><dt>Difficulty</dt><dd>{esc(record.get("difficulty_score"))} of 3 - {esc(record.get("difficulty_label"))}</dd></div><div><dt>Fit</dt><dd>{esc(record.get("forest_products_fit_score"))} of 3 - {esc(record.get("forest_products_fit_label"))}</dd></div><div><dt>First action</dt><dd>{esc(first)}</dd></div></dl><a class="button secondary" href="/sourcebook/#page-{esc(record.get("sourcebook_page"))}">Sourcebook page {esc(record.get("sourcebook_page"))}</a><button type="button" class="compare-toggle" data-compare-id="{esc(record["id"])}">Compare</button><button type="button" data-print>Print</button><button type="button" data-feedback>Report a correction</button></aside>'''


def source_section(record):
    items = []
    for source in record.get("official_sources") or []:
        items.append(f'<li><a href="{esc(source["url"])}" target="_blank" rel="noopener">{esc(source["label"])}</a> <span>({esc(host_label(source["url"]))})</span></li>')
    return '<section><h2>Official sources</h2><ul class="source-list">' + "".join(items) + "</ul></section>"


def timing_section(record):
    section = f'<section class="timing-panel"><h2>Timing / first action</h2><p>{esc(record.get("timing_first_action"))}</p></section>'
    using = record.get("using_the_credit")
    if using:
        pieces = [clean_ws(x.strip(" •-")) for x in re.split(r"\s*[•�]\s*", using) if clean_ws(x.strip(" •-"))]
        if len(pieces) > 1:
            section += '<section><h2>Using the credit</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in pieces) + "</ul></section>"
        else:
            section += f'<section><h2>Using the credit</h2><p>{esc(using)}</p></section>'
    return section


def shared_footer_dialog():
    return f'''<footer class="site-footer">
  <div><h2>About</h2><p><strong>National Forest Products Tax Credit Sourcebook</strong><br>2026 Edition<br>Revised September 24, 2026</p><p>This is a screening guide, not tax advice or a guarantee of eligibility.</p></div>
  <div><h2>Navigate</h2><p><a href="/search/">Search</a><br><a href="/states/">States</a><br><a href="/activity/">Activities</a><br><a href="/updates/">Updates</a><br><a href="/compare/">Compare</a><br><a href="/about/">About</a></p></div>
  <div><h2>Corrections</h2><p>Send corrections, broken links, and new program information to <a href="mailto:steve@northeastforests.com">steve@northeastforests.com</a>.</p><p><a href="{PDF_URL}" download>Full sourcebook</a></p></div>
</footer>
<dialog id="feedbackDialog" aria-labelledby="feedbackTitle">
  <form method="dialog" class="feedback-form" novalidate>
    <button class="dialog-close" value="cancel" aria-label="Close">×</button>
    <h2 id="feedbackTitle">Suggest a correction</h2>
    <p>Submissions are prepared with page context so they can become maintenance items for a future edition.</p>
    <label>Type <select id="feedbackType"><option>Correction</option><option>Broken link</option><option>Missing program</option><option>Question</option><option>Other</option></select></label>
    <label>Message <textarea id="feedbackMessage" required></textarea></label>
    <p class="form-error" id="feedbackError" role="alert" hidden></p>
    <label>Name <input id="feedbackName" autocomplete="name"></label>
    <label>Email <input id="feedbackEmail" type="email" autocomplete="email"></label>
    <p class="form-note">This button opens your email client with the page context filled in.</p>
    <button type="button" id="feedbackEmailButton">Prepare correction email</button>
    <p class="form-note" id="feedbackStatus" role="status" hidden></p>
  </form>
</dialog>'''


def update_html_files(records):
    by_id = {r["id"]: r for r in records}
    cards = {rid: card_html(r) for rid, r in by_id.items()}
    footer_dialog = shared_footer_dialog()
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        text = OLD_PDF_RE.sub(PDF_URL, text)
        text = re.sub(r'(<a class="pdf-link" href="/assets/pdf/NFPTC-2026\.pdf") target="_blank" rel="noopener"', r'\1 download', text)
        text = re.sub(r'(<a class="button secondary" href="/assets/pdf/NFPTC-2026\.pdf") target="_blank" rel="noopener"', r'\1 download', text)
        text = text.replace('href="/assets/pdf/NFPTC-2026.pdf">Download the 2026 Sourcebook', 'href="/assets/pdf/NFPTC-2026.pdf" download>Download the 2026 Sourcebook')
        text = text.replace("href='/assets/pdf/NFPTC-2026.pdf'>View / Download", "href='/assets/pdf/NFPTC-2026.pdf' download>View / Download")
        text = re.sub(r'href="/sourcebook/(#page-\d+)" target="_blank" rel="noopener"', r'href="/sourcebook/\1"', text)
        text = re.sub(r'content="([^"]*?)\s+"', lambda m: f'content="{m.group(1).rstrip()}"', text)
        text = text.replace("/assets/css/styles.css?v=20260927e", "/assets/css/styles.css?v=20260927f")
        text = text.replace("/assets/js/site.js?v=20260927b", "/assets/js/site.js?v=20260927c")
        text = re.sub(
            r'<footer class="site-footer">.*?</dialog>',
            footer_dialog,
            text,
            flags=re.S,
        )
        def replace_card(match):
            return cards.get(match.group(1), match.group(0))
        text = re.sub(r'<article class="program-card" data-program-id="([^"]+)">.*?</article>', replace_card, text, flags=re.S)
        detail = re.search(r'data-program-id="([^"]+)"', text)
        if detail and detail.group(1) in by_id:
            record = by_id[detail.group(1)]
            text = re.sub(r'<section class="timing-panel"><h2>Timing / first action</h2>.*?</section>(?:<section><h2>Using the credit</h2>.*?</section>)?', timing_section(record), text, count=1, flags=re.S)
            text = re.sub(r'<section><h2>Official sources</h2><ul class="source-list">.*?</ul></section>', source_section(record), text, count=1, flags=re.S)
            text = re.sub(r'<aside class="detail-sidebar">.*?</aside>(?=</div>\s*</main>|</div>\s*<footer|</div>\s*<script|</div>\s*$|</div>)', detail_sidebar(record), text, count=1, flags=re.S)
        path.write_text(text, encoding="utf-8", newline="\n")


def write_min_json(records):
    keys = [
        "id", "title", "jurisdiction", "jurisdiction_type", "state_code", "activity", "slug", "url",
        "summary", "headline", "credit_amount_calculation", "timing_first_action", "refundable",
        "transferable", "carryforward", "difficulty_score", "difficulty_label",
        "forest_products_fit_score", "forest_products_fit_label", "activity_tags",
        "business_relevance", "timing_tags", "refundable_status", "transferable_status",
        "search_synonyms", "sourcebook_page",
    ]
    slim = [{k: r.get(k) for k in keys if k in r} for r in records]
    (ROOT / "assets/data/programs.min.json").write_text(json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def update_assets():
    css = ROOT / "assets/css/styles.css"
    text = css.read_text(encoding="utf-8")
    additions = ".program-list:not(.compact){padding:1.5rem clamp(1rem,5vw,4rem)}.detail .program-list:not(.compact),.detail .program-list.compact{padding:0}@media(max-width:900px){.detail-layout{display:flex;flex-direction:column}.detail-sidebar{order:-1;width:100%}}"
    if ".program-list:not(.compact)" not in text:
        text += "\n" + additions
    css.write_text(text, encoding="utf-8", newline="\n")

    site_js = ROOT / "assets/js/site.js"
    text = site_js.read_text(encoding="utf-8").replace('const PDF_URL = "https://drive.google.com/file/d/1uvsSiIreZqcPHlvo2IUM_z4EEoFDDmw6/view?usp=sharing";', f'const PDF_URL = "{PDF_URL}";')
    site_js.write_text(text, encoding="utf-8", newline="\n")

    config = ROOT / "content/site-config.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    data["guidePdfUrl"] = PDF_URL
    config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sitemap = ROOT / "sitemap.xml"
    if sitemap.exists():
        text = sitemap.read_text(encoding="utf-8")
        text = re.sub(r"\s*<url>\s*<loc>https://tax\.lumbermen\.org/404\.html</loc>(?:\s*<lastmod>[^<]+</lastmod>)?\s*</url>", "", text)
        sitemap.write_text(text, encoding="utf-8", newline="\n")

    dest = ROOT / "assets/pdf/NFPTC-2026.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = Path(r"C:\Users\steve\Dropbox\Technical Items\National Tax Credit Guide\National_Forest_Products_Tax_Credit_Sourcebook_2026_Edition.pdf")
    if src.exists():
        shutil.copy2(src, dest)


def validate(records):
    errors = []
    for record in records:
        for key, value in record.items():
            if isinstance(value, str) and re.search(r"\b[Pp]age(?:\s+\d+)?\s*$", value):
                errors.append(f"{record['id']} {key} ends with Page")
        if record.get("headline") and (len(record["headline"]) > 60 or record["headline"].endswith("...")):
            errors.append(f"{record['id']} bad headline")
        if record.get("headline") and record.get("summary", "").lower().startswith(record["headline"].lower()):
            errors.append(f"{record['id']} summary repeats headline")
        urls = [s["url"] for s in record.get("official_sources") or []]
        if len(urls) != len(set(urls)):
            errors.append(f"{record['id']} duplicate source URL")
        for source in record.get("official_sources") or []:
            label = source["label"]
            if "official source" in label.lower() or "\r" in label or "\n" in label or re.search(r"\s{2,}", label) or " — " not in label or "— —" in label or re.search(r"(through|and|or|1 CCR)$", label):
                errors.append(f"{record['id']} bad source label: {label}")
    if errors:
        raise SystemExit("\n".join(errors[:40]))


def main():
    programs_path = ROOT / "content/programs.json"
    records = json.loads(programs_path.read_text(encoding="utf-8"))
    update_records(records)
    validate(records)
    programs_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_min_json(records)
    update_html_files(records)
    update_assets()
    print(f"Updated {len(records)} program records and regenerated static content.")


if __name__ == "__main__":
    main()
