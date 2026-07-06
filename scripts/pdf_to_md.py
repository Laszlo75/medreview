#!/usr/bin/env python3
"""Convert a manuscript PDF to Markdown with page markers for medreview, and
extract rendered page images for figures and tables so reviewers can
actually see plots/charts and verify table cell values/alignment that plain
text extraction is blind to or scrambles.

Usage: python scripts/pdf_to_md.py papers/manuscript.pdf
Writes:
  papers/manuscript.md
      Text with <!-- page N --> markers, unchanged byte-for-byte for the
      body-text stream vs. the previous version of this script. The only
      additions are new HTML-comment lines inserted around each page
      marker: a `<!-- figure image: ... -->` pointer on pages that look
      like they contain a figure, and a `<!-- table image: ... -->` pointer
      on pages with a table caption. Both point to a rendered PNG of that
      page -- neither figures nor tables can be trusted as plain text: a
      vector-drawn chart has no extractable text at all, and PyMuPDF's
      plain-text mode reads a page in geometric/line order, so a
      multi-column table comes out as a flattened dump with column/row
      association scrambled. No table-structure (row/column) extraction is
      attempted -- see _render_table's docstring for why. The flattened
      table text is still emitted below the pointer (unchanged) -- some
      cell values remain greppable/useful even when alignment isn't
      trustworthy. Known limitation shared with figures: a table (or
      figure) that continues onto a following page with no caption of its
      own on that page won't get a second rendered image -- only the
      captioned page is captured.
  papers/manuscript_figures/page-NNN_figK.png (only created if >=1 figure
      is found)
      One rendered PNG per figure page: a tight, padded crop of the page's
      embedded raster image(s) when PyMuPDF finds one large enough (and
      prominent enough) to be a figure -- this also gets a higher effective
      zoom on the actual figure than a whole-page render could, without
      exceeding Claude's vision resize threshold -- or a whole-page render
      as a robust fallback for figures drawn as pure vector paths (many R
      ggplot / matplotlib PDF exports have no embedded raster image at all)
      or for pages where no qualifying raster image was found.
  papers/manuscript_figures/page-NNN_tableK.png (only created if >=1 table
      caption is found; same directory as figure images)
      One whole-page render PNG per page carrying a table caption -- see
      _render_table's docstring for why this is whole-page-only, with no
      bbox-cropped variant. If two table captions appear on the same page
      (e.g. "Table 2" then "Table 3" back to back), one PNG is rendered and
      both captions are named in its pointer comment.

Requires: pip install pymupdf
"""
import re
import sys
from pathlib import Path

import fitz  # pymupdf

# Caption headings anchored at the START of a text line, e.g. "FIGURE 1 |",
# "Figure 1.", "Fig. 2:", "Table 3". Deliberately does NOT match an inline
# mid-sentence reference like "..., Figure 1A. Most patients..." -- that
# would false-positive on pages that only discuss a figure defined
# elsewhere, not the figure's own page. The trailing (?![A-Za-z]) is load-
# bearing: PDF text extraction wraps justified prose at arbitrary points, so
# a sentence like "Figure 1E where they were more likely to go to the high"
# can itself start a line -- rejecting a letter immediately after the digits
# (a panel-suffix, "1E") is what distinguishes that from a real caption like
# "FIGURE 2 | Impact of...", where a space/pipe follows the number instead.
FIGURE_CAPTION_RE = re.compile(r"^\s*fig(?:ure)?s?\.?\s*(\d+)(?![A-Za-z])", re.IGNORECASE)
TABLE_CAPTION_RE = re.compile(r"^\s*tables?\s*(\d+)(?![A-Za-z])", re.IGNORECASE)

# Ignore embedded images smaller than this in either dimension -- filters
# journal logos/icons/watermarks, not real figures.
MIN_IMAGE_DIM_PT = 60
# A qualifying image (or union of images) must also cover at least this
# fraction of the page area. Guards against the case where a page has a
# vector-drawn figure (no raster) PLUS an incidental raster >=MIN_IMAGE_DIM_PT
# (e.g. a ~60x60pt society logo) -- without this, we'd crop to the logo and
# silently miss the actual (vector) figure. Below this ratio, fall back to a
# whole-page render instead.
MIN_IMAGE_AREA_RATIO = 0.10
# Padding (PDF points) added around the union of qualifying embedded-image
# bboxes before cropping, so axis labels/legends right at the image edge
# aren't clipped.
CROP_PAD_PT = 20
# Target long-edge pixel size for rendered images. 1568px is the documented
# Claude vision resize threshold (docs.claude.com/en/docs/build-with-claude/
# vision): anything larger is downscaled before the model sees it, adding
# bytes/latency with no legibility benefit; anything much smaller under-uses
# the available budget on small multi-panel chart labels/error bars.
TARGET_LONG_EDGE_PX = 1568
CROP_MIN_ZOOM, CROP_MAX_ZOOM = 1.5, 4.0
# Whole-page render is also targeted at TARGET_LONG_EDGE_PX (adaptive to the
# actual page size -- Letter/A4/other), capped so an unusually small page
# doesn't get over-zoomed for no reason. Reused as-is for table-page
# rendering (see _render_table): for realistic page sizes (long edge >=
# ~8.7in) this cap never actually binds -- TARGET_LONG_EDGE_PX / long_edge_pt
# already comes out <= FULL_PAGE_MAX_ZOOM -- so a table-specific higher cap
# would not change the rendered zoom anyway. The real ceiling is
# TARGET_LONG_EDGE_PX itself: Claude's vision preprocessing downscales
# anything with a longer edge back to that threshold before the model sees
# it, so rendering source pixels beyond it buys nothing.
FULL_PAGE_MAX_ZOOM = 2.5


def _figure_bbox(page):
    """Union bbox of embedded raster images big enough AND prominent enough
    to be a figure, or None if the page has no such image (e.g. a
    vector-drawn chart, or only a small decorative raster like a logo)."""
    imgs = [
        im for im in page.get_image_info()
        if (im["bbox"][2] - im["bbox"][0]) >= MIN_IMAGE_DIM_PT
        and (im["bbox"][3] - im["bbox"][1]) >= MIN_IMAGE_DIM_PT
    ]
    if not imgs:
        return None
    x0 = min(im["bbox"][0] for im in imgs)
    y0 = min(im["bbox"][1] for im in imgs)
    x1 = max(im["bbox"][2] for im in imgs)
    y1 = max(im["bbox"][3] for im in imgs)
    bbox = fitz.Rect(x0, y0, x1, y1)
    page_area = page.rect.width * page.rect.height
    if page_area <= 0 or (bbox.width * bbox.height) / page_area < MIN_IMAGE_AREA_RATIO:
        return None
    return bbox


def _render_whole_page(page, out_path) -> None:
    """Render the entire `page` to `out_path` as PNG, targeted at
    TARGET_LONG_EDGE_PX long edge (zoom capped at FULL_PAGE_MAX_ZOOM so an
    unusually small page doesn't get over-zoomed for no reason). Shared by
    _render_figure's vector-chart fallback and _render_table (tables always
    render the whole page -- see _render_table)."""
    long_edge_pt = max(page.rect.width, page.rect.height)
    zoom = min(FULL_PAGE_MAX_ZOOM, TARGET_LONG_EDGE_PX / long_edge_pt)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(out_path)


def _render_figure(page, out_path) -> None:
    """Render `page` to `out_path` as PNG: a tight padded crop around any
    qualifying embedded raster image (higher effective zoom on the figure
    itself), else the whole page (safe fallback for vector-only charts, or
    pages whose only raster content isn't prominent enough to trust)."""
    bbox = _figure_bbox(page)
    if bbox is None:
        _render_whole_page(page, out_path)
        return
    clip = fitz.Rect(
        bbox.x0 - CROP_PAD_PT, bbox.y0 - CROP_PAD_PT,
        bbox.x1 + CROP_PAD_PT, bbox.y1 + CROP_PAD_PT,
    ) & page.rect
    long_edge_pt = max(clip.width, clip.height)
    zoom = max(CROP_MIN_ZOOM, min(CROP_MAX_ZOOM, TARGET_LONG_EDGE_PX / long_edge_pt))
    pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(zoom, zoom))
    pix.save(out_path)


def _render_table(page, out_path) -> None:
    """Render `page` to `out_path` as PNG: the whole page, unconditionally.

    Unlike _render_figure, this does NOT attempt a bbox-cropped render.
    Evaluated and rejected:
    - PyMuPDF's page.find_tables() (default "lines" strategy, ruling-line
      based) finds 0 tables on this project's sample paper -- its tables
      are borderless, common in journal layouts. The whitespace-based
      "text" strategy does find one, but its bbox covered ~78% of the page
      area on every table page tested (including pages that mix table
      content with ordinary body prose) -- a table-caption page tends to
      already be dominated by the table, unlike a figure page that
      typically has margin/whitespace/prose around a smaller image. Even
      when it fires, cropping to that bbox would only buy ~10-15% extra
      linear zoom -- not the large jump bbox-cropping gives a figure, and
      not enough to reliably turn a borderline-legible dense table legible.
    - find_tables() is a text-layout heuristic (it guesses structure from
      whitespace, not ground truth), unlike _figure_bbox's embedded-raster
      metadata, which is exact. A wrong or partial bbox could clip real
      table content -- worse than a whole-page image that merely isn't
      maximally zoomed.
    Revisit only if a future corpus shows table bboxes reliably much
    smaller than the page. If whole-page legibility proves inadequate even
    for word/label-shaped cells on a densely packed table, the better
    escalation is rendering the page as two (or more) overlapping
    left/right column-strip crops instead -- each its own <=1568px image,
    roughly doubling effective glyph density -- not find_tables()
    cropping, which the area-ratio math above shows wouldn't help."""
    _render_whole_page(page, out_path)


def main() -> None:
    pdf_path = Path(sys.argv[1])
    out_path = pdf_path.with_suffix(".md")
    figures_dir = pdf_path.parent / f"{pdf_path.stem}_figures"

    doc = fitz.open(pdf_path)
    parts = []
    n_figures = 0
    n_tables = 0
    captioned_pages = set()

    for i, page in enumerate(doc, start=1):
        parts.append(f"\n<!-- page {i} -->\n")

        text = page.get_text("text")

        fig_match = None
        table_labels = []
        for line in text.split("\n"):
            if fig_match is None:
                m = FIGURE_CAPTION_RE.match(line)
                if m:
                    fig_match = m
            m2 = TABLE_CAPTION_RE.match(line)
            if m2:
                table_labels.append(m2.group(1))

        if fig_match is not None:
            captioned_pages.add(i)
            label = re.sub(r"[^A-Za-z0-9]", "", fig_match.group(1))
            img_path = figures_dir / f"page-{i:03d}_fig{label}.png"
            try:
                figures_dir.mkdir(exist_ok=True)
                _render_figure(page, img_path)
                n_figures += 1
                parts.append(
                    f"<!-- figure image: {img_path.resolve()} "
                    f"(rendered from this page; open with Read if the "
                    f"segment's focus concerns a plot/curve/chart whose "
                    f"visual pattern matters -- e.g. Kaplan-Meier curves, "
                    f"forest plots, calibration/ROC plots -- not needed if "
                    f"the caption/text already fully describes it) -->\n"
                )
            except Exception as exc:  # a single corrupt page shouldn't kill the run
                print(f"Warning: could not render figure image for page {i}: {exc}",
                      file=sys.stderr)

        table_ids = list(dict.fromkeys(table_labels))  # de-dupe, keep first-seen order
        if table_ids:
            # One render per PAGE, not per label: if "Table 2" and "Table 3"
            # are both captioned on this page, one PNG covers both rather
            # than rendering the same page twice under two names.
            label = re.sub(r"[^A-Za-z0-9]", "", table_ids[0])
            img_path = figures_dir / f"page-{i:03d}_table{label}.png"
            try:
                figures_dir.mkdir(exist_ok=True)
                _render_table(page, img_path)
                n_tables += 1
                table_names = ", ".join(f"Table {t}" for t in table_ids)
                parts.append(
                    f"<!-- table image: {img_path.resolve()} "
                    f"(rendered from this page -- shows {table_names}; open "
                    f"with Read to verify exact cell values and column/row "
                    f"alignment before quoting a number from the flattened "
                    f"text below -- plain-text extraction reads this page "
                    f"in geometric order, so a multi-column table comes out "
                    f"as a flattened dump with column/row association "
                    f"scrambled) -->\n"
                )
            except Exception as exc:  # a single corrupt page shouldn't kill the run
                print(f"Warning: could not render table image for page {i}: {exc}",
                      file=sys.stderr)

        parts.append(text)

    out_path.write_text("".join(parts), encoding="utf-8")

    # Diagnostic only -- does not change the .md output. Pages with a large,
    # prominent embedded image but no caption match on the SAME page are a
    # known gap: some journals put a figure image and its caption on
    # different pages. Flag it so a human can sanity-check the PDF once.
    uncaptioned_image_pages = [
        i for i, page in enumerate(doc, start=1)
        if _figure_bbox(page) is not None and i not in captioned_pages
    ]
    if len(uncaptioned_image_pages) > n_figures:
        print(
            f"Note: page(s) {uncaptioned_image_pages} have a large embedded "
            f"image but no figure-caption text of their own -- if this "
            f"paper's figures and captions sit on different pages, some "
            f"figures may not have been captured. Skim the PDF to check.",
            file=sys.stderr,
        )

    msg = f"Wrote {out_path} ({len(doc)} pages)"
    if n_figures:
        msg += f", {n_figures} figure image(s) in {figures_dir}/"
    if n_tables:
        msg += f", {n_tables} table image(s) in {figures_dir}/"
    print(msg)


if __name__ == "__main__":
    main()
