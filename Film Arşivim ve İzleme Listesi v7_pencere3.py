import json
import os
import re
import sys

input_bookmarks = "bookmarks.html"
input_details = "details.js"
input_prev_html = "favorilerim.html"

def normalize_url(url):
    if not url:
        return ""
    clean = url.lower().strip()
    clean = re.sub(r'^https?://', '', clean)
    clean = re.sub(r'^www\.', '', clean)
    clean = clean.split("?")[0].split("#")[0]
    if clean.endswith("/"):
        clean = clean[:-1]
    clean = re.sub(r'-\d+b?$', '', clean)
    return clean

def main():
    print("=" * 65)
    print("   ANA KOD.PY - PAGING & LAZY GROUPS v49")
    print("=" * 65)

    existing_url_to_id = {}
    max_existing_id = 0

    if os.path.exists(input_prev_html):
        print(f"[1/4] '{input_prev_html}' okunuyor ve mevcut film_ID'ler taranıyor...")
        try:
            with open(input_prev_html, "r", encoding="utf-8", errors="ignore") as f:
                prev_content = f.read()

            m_movies = re.search(r'const\s+allMovies\s*=\s*JSON\.parse\(decodeURIComponent\(\'(.*?)\'\)\);', prev_content, re.DOTALL)
            if not m_movies:
                m_movies = re.search(r'const\s+allMovies\s*=\s*(\[.*?\]);', prev_content, re.DOTALL)

            if m_movies:
                movies_json_str = m_movies.group(1)
                if not movies_json_str.startswith("["):
                    import urllib.parse
                    movies_json_str = urllib.parse.unquote(movies_json_str)
                movies_list = json.loads(movies_json_str)
                for m in movies_list:
                    url = m.get("web_scraper_start_url") or m.get("url")
                    fid = m.get("film_ID") or m.get("id")
                    if url and fid is not None:
                        norm = normalize_url(url)
                        existing_url_to_id[norm] = int(fid)
                        if int(fid) > max_existing_id:
                            max_existing_id = int(fid)
            print(f" -> Önceki favorilerim.html'den {len(existing_url_to_id)} filmin ID'si korundu. (Son ID: {max_existing_id})")
        except Exception as e:
            print(f"[HATA]: Önceki '{input_prev_html}' okunurken hata: {e}")

    print(f"\n[2/4] '{input_bookmarks}' okunuyor...")
    if not os.path.exists(input_bookmarks):
        print(f"[HATA]: '{input_bookmarks}' bulunamadı!")
        sys.exit(1)

    with open(input_bookmarks, "r", encoding="utf-8", errors="ignore") as f:
        bm_content = f.read()

    pattern = re.compile(r'<A\s+HREF="([^"]+)"[^>]*ADD_DATE="(\d+)"[^>]*>(.*?)</A>', re.IGNORECASE)
    bookmarks_list = []
    seen_urls = set()

    for match in pattern.finditer(bm_content):
        raw_url = match.group(1)
        raw_title = match.group(3).strip()
        norm_url = normalize_url(raw_url)

        if norm_url not in seen_urls:
            seen_urls.add(norm_url)
            bookmarks_list.append({
                "url": raw_url,
                "norm_url": norm_url,
                "title": raw_title
            })

    print(f" -> bookmarks.html içinde toplam {len(bookmarks_list)} film tespit edildi.")

    print(f"\n[3/4] '{input_details}' okunuyor ve zengin veriler korunuyor...")
    details_map = {}
    if os.path.exists(input_details):
        with open(input_details, "r", encoding="utf-8") as f:
            d_content = f.read()
            if "const allFilms =" in d_content:
                j_str = d_content.split("const allFilms =")[1].strip().rstrip(";")
                try:
                    raw_dt = json.loads(j_str)
                    for item in raw_dt:
                        u = item.get("web_scraper_start_url") or item.get("url") or ""
                        n_u = normalize_url(u)
                        if n_u:
                            details_map[n_u] = item
                except Exception as ex:
                    print(f" -> details.js parse uyarısı: {ex}")

    current_next_id = max_existing_id + 1
    details_js_list = []

    for bm in bookmarks_list:
        norm_u = bm["norm_url"]

        if norm_u in existing_url_to_id:
            assigned_id = existing_url_to_id[norm_u]
        else:
            assigned_id = current_next_id
            existing_url_to_id[norm_u] = assigned_id
            current_next_id += 1

        poster_path = f"posters/{assigned_id}.webp"

        if norm_u in details_map:
            film_entry = details_map[norm_u]
        else:
            film_entry = {
                "web_scraper_order": False,
                "web_scraper_start_url": bm["url"],
                "film_name": bm["title"],
                "imdb_score": None,
                "duration_mins": None,
                "year": None,
                "movie_summary": None,
                "country": None,
                "actor1": None,
                "actor2": None,
                "actor3": None,
                "actor4": None,
                "actor5": None,
                "actor6": None,
                "actor7": None,
            }

        film_entry["film_ID"] = assigned_id
        film_entry["poster"] = poster_path

        details_js_list.append(film_entry)

    out_js = "const allFilms = " + json.dumps(details_js_list, indent=4, ensure_ascii=False) + ";\n"
    with open(input_details, "w", encoding="utf-8") as f:
        f.write(out_js)
    print(f" -> '{input_details}' güncellendi (Toplam {len(details_js_list)} film).")

    print(f"\n[4/4] '{input_prev_html}' üretiliyor...")

    html_template = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Film Arşivim ve İzleme Listesi</title>
<style>
  :root {
    --bg-color: #121212;
    --card-bg: #1e1e1e;
    --text-color: #e0e0e0;
    --accent-color: #e50914;
    --border-color: #333;
  }
  body { background-color: var(--bg-color); color: var(--text-color); font-family: Arial, sans-serif; margin: 0; padding: 20px; overflow-x: clip; transition: background-color 0.2s ease, padding-right 0.22s ease; }
  body.multi-select-page-bg { background-color: #199e46; }
  body.sidebar-open-filter { padding-right: 310px; }
  body.sidebar-open-genre-add { padding-right: 700px; }

  input[type="number"] {
    -moz-appearance: textfield;
  }
  input[type="number"]::-webkit-outer-spin-button,
  input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  .header-container {
    position: sticky;
    top: 0;
    z-index: 1000;
    background-color: inherit;
    padding-top: 4px;
    padding-bottom: 11px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 14px;
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    background: #181818;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    align-items: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
  }

  .controls-bottom-row {
    flex-basis: 100%;
    order: 50;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    align-items: center;
    padding-top: 6px;
    margin-top: 2px;
    border-top: 1px solid #282828;
  }

  input, select, button, a.btn-link { padding: 6px 10px; background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
  input:focus, select:focus { border-color: var(--accent-color); outline: none; }
  button, a.btn-link { cursor: pointer; font-weight: bold; transition: background 0.2s, border-color 0.2s, color 0.2s; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  button.active, a.btn-link.active { background: var(--accent-color); color: #fff; border-color: var(--accent-color); }

  .btn-go { padding: 3px 8px; background: #333; color: #fff; border: 1px solid #555; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer; line-height: 1.3; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; }
  .btn-go:hover { background: var(--accent-color); border-color: var(--accent-color); color: #fff; }
  .btn-go.is-open, .btn-go.is-simple, .btn-go.is-side-by-side { background: #10b981; color: #052e16; border-color: #6ee7b7; }

  .right-sidebar-panel {
    display: none;
    position: fixed;
    top: 0;
    right: 0;
    width: 290px;
    height: 100vh;
    background: #161616;
    border-left: 1px solid #333;
    box-shadow: -6px 0 24px rgba(0,0,0,0.75);
    z-index: 2500;
    flex-direction: column;
    padding: 12px;
    box-sizing: border-box;
    gap: 10px;
  }
  .right-sidebar-panel.open {
    display: flex;
  }
  .right-sidebar-panel.genre-add-mode {
    width: 680px;
    max-width: 96vw;
  }
  .right-sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2c2c2c;
    padding-bottom: 8px;
    font-size: 13px;
    font-weight: bold;
    color: #f5c518;
    gap: 8px;
  }
  .right-sidebar-close-btn {
    background: #262626;
    color: #e5e7eb;
    border: 1px solid #444;
    padding: 3px 8px;
    font-size: 11px;
    border-radius: 4px;
    flex-shrink: 0;
  }
  .right-sidebar-close-btn:hover {
    background: #dc2626;
    color: #fff;
    border-color: #dc2626;
  }
  .sidebar-genre-listbox {
    flex: 1;
    overflow-y: auto;
    background: #121212;
    border: 1px solid #3a3a3a;
    border-radius: 5px;
    padding: 5px;
    display: flex;
    flex-direction: column;
    gap: 3px;
    box-sizing: border-box;
  }
  .sidebar-genre-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 7px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 11.5px;
    line-height: 1.2;
    user-select: none;
    border: 1px solid #1f1f1f;
    background: #181818;
    color: #e0e0e0;
    box-sizing: border-box;
  }
  .sidebar-genre-item:hover {
    background: #1f2937;
    border-color: #374151;
  }
  .sidebar-genre-item.checked-row {
    background: #10b981;
    border-color: #34d399;
    color: #052e16;
    font-weight: bold;
  }
  .sidebar-genre-item input[type="checkbox"] {
    width: 12px;
    height: 12px;
    accent-color: #10b981;
    cursor: pointer;
    margin: 0;
    flex-shrink: 0;
  }
  .sidebar-genre-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .sidebar-genre-add-body {
    flex: 1;
    min-height: 0;
    display: none;
    flex-direction: column;
    gap: 8px;
  }
  .right-sidebar-panel.genre-add-mode .sidebar-genre-add-body {
    display: flex;
  }
  .right-sidebar-panel.genre-add-mode #sidebarGenreListbox {
    display: none;
  }
  .sidebar-4col-checkbox-list {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    background: #121212;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 4px;
    align-content: start;
  }
  .sidebar-genre-preview-box {
    background: #151515;
    border: 1px solid #333;
    border-radius: 5px;
    padding: 7px 9px;
    max-height: 125px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 3px;
    font-size: 11px;
    color: #bbb;
    flex-shrink: 0;
  }

  .last-id-container { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #bbb; background: #111; padding: 3px 7px; border-radius: 4px; border: 1px solid #333; }
  .last-id-container input { width: 52px; padding: 3px 5px; text-align: center; font-weight: bold; color: #f5c518; }

  .search-box-wrap { display: inline-flex; align-items: center; gap: 3px; }
  .btn-search { padding: 5px 8px; background: #262626; color: #e0e0e0; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; cursor: pointer; line-height: 1.2; }
  .btn-search:hover { background: var(--accent-color); color: #fff; border-color: #fff; }

  .filter-slider-container {
    display: flex;
    flex-direction: column;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
    color: var(--text-color);
    min-width: 155px;
    box-sizing: border-box;
  }
  .filter-slider-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
    color: #f5c518;
    margin-bottom: 4px;
  }
  .filter-sliders-wrapper {
    position: relative;
    height: 18px;
    display: flex;
    align-items: center;
  }
  .filter-sliders-wrapper::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 4px;
    background: #4b5563;
    border-radius: 2px;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
  }
  .filter-sliders-wrapper input[type="range"] {
    position: absolute;
    width: 100%;
    background: none;
    pointer-events: none;
    -webkit-appearance: none;
    margin: 0;
    padding: 0;
    border: none;
  }
  .filter-sliders-wrapper input[type="range"]::-webkit-slider-thumb {
    pointer-events: auto;
    -webkit-appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--accent-color);
    cursor: pointer;
    border: 2px solid #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.5);
  }
  .filter-sliders-wrapper input[type="range"]::-moz-range-thumb {
    pointer-events: auto;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--accent-color);
    cursor: pointer;
    border: 2px solid #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.5);
  }

  .btn-group-toggle { background: #1e293b; color: #93c5fd; border: 1px solid #3b82f6; font-size: 11px; padding: 5px 9px; display: none; }
  .btn-group-toggle:hover { background: #2563eb; color: #fff; }
  .btn-group-toggle.visible { display: inline-flex !important; }

  .linked-sort-container {
    display: none;
    align-items: center;
    gap: 5px;
    background: #1e293b;
    border: 1px solid #3b82f6;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    color: #93c5fd;
  }
  .linked-sort-container.visible { display: inline-flex !important; }

  .film-count-badge { background: #111; color: #f5c518; border: 1px solid #333; padding: 4px 9px; border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap; }

  .pagination-bar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 6px;
    margin: 12px 0;
    padding: 8px 12px;
    background: #181818;
    border: 1px solid var(--border-color);
    border-radius: 8px;
  }
  .pagination-bar.hidden-bar {
    display: none;
  }
  .page-btn {
    padding: 5px 10px;
    font-size: 12px;
    background: #222;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    min-width: 34px;
  }
  .page-btn:hover:not(:disabled) {
    background: #333;
    border-color: var(--accent-color);
  }
  .page-btn.active-page {
    background: var(--accent-color);
    color: #fff;
    border-color: var(--accent-color);
  }
  .page-info-text {
    font-size: 12px;
    color: #f5c518;
    font-weight: bold;
    margin: 0 6px;
  }

  .relation-banner {
    display: none;
    justify-content: center;
    align-items: center;
    gap: 12px;
    background: #1e293b;
    color: #93c5fd;
    border: 1px solid #3b82f6;
    padding: 8px 16px;
    border-radius: 6px;
    margin-top: 10px;
    font-size: 13px;
    font-weight: bold;
  }
  .relation-banner.visible { display: flex; }
  .btn-clear-relation { background: #dc2626; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; }
  .btn-clear-relation:hover { background: #b91c1c; }

  .movie-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); row-gap: 10px; column-gap: 20px; }

  .group-section-wrapper {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    margin-top: 2px;
    margin-bottom: 1px;
  }
  .group-section-header {
    background: #1e293b;
    color: #93c5fd;
    padding: 5px 12px;
    min-height: 24px;
    font-size: 13px;
    font-weight: bold;
    border-radius: 5px;
    border: 1px solid #3b82f6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;
    box-sizing: border-box;
  }
  .group-section-header:hover {
    background: #2563eb;
    color: #fff;
  }
  .group-collapse-icon {
    font-size: 11px;
    font-weight: bold;
    margin-left: 8px;
    cursor: pointer;
  }
  .group-movies-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    row-gap: 8px;
    column-gap: 20px;
    margin-top: 2px;
    margin-bottom: 2px;
    padding-left: 5px;
    border-left: 2px dashed #3b82f6;
  }
  .group-movies-container.collapsed {
    display: none !important;
  }

  .movie-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; overflow: visible; display: flex; flex-direction: column; position: relative; transition: transform 0.2s; }
  .movie-card:hover { transform: translateY(-4px); border-color: #555; z-index: 30; }
  .movie-card.highlight {
    outline: 4px solid #e50914;
    box-shadow: 0 0 18px rgba(229, 9, 20, 0.85);
    z-index: 25;
  }

  body.simple-view .card-user-actions,
  body.simple-view .card-relation-bar,
  body.simple-view .domain-container,
  body.simple-view .summary-text,
  body.simple-view #toggleGenreAddSidebarBtn,
  body.simple-view #showHiddenLabel,
  body.simple-view #multiSelectLabel,
  body.simple-view #recentMoviesDropdown,
  body.simple-view #editorLinkBtn,
  body.simple-view #exportDataBtn,
  body.simple-view #importDataBtn,
  body.simple-view #domainFilter,
  body.simple-view #countryFilter,
  body.simple-view #sortSelect1,
  body.simple-view #sortSelect2,
  body.simple-view .filter-slider-container {
    display: none !important;
  }
  body.simple-view .controls {
    flex-wrap: nowrap;
    justify-content: center;
    gap: 6px;
    padding: 8px 10px;
  }
  body.simple-view .controls > *,
  body.simple-view .controls-bottom-row > * {
    flex-shrink: 0;
    white-space: nowrap;
  }
  body.simple-view .controls-bottom-row {
    flex-basis: auto;
    order: 0;
    flex-wrap: nowrap;
    gap: 6px;
    padding-top: 0;
    margin-top: 0;
    border-top: none;
  }
  body.simple-view .controls-bottom-row .last-id-container,
  body.simple-view .controls-bottom-row .film-count-badge {
    order: -1;
  }
  body.simple-view.sidebar-open-genre-add {
    padding-right: 20px;
  }
  body.simple-view .movie-title {
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    height: 18px;
    -webkit-line-clamp: unset;
    -webkit-box-orient: unset;
  }
  body.simple-view .add-movie-to-genre-card {
    min-height: 360px;
  }

  .add-movie-to-genre-card {
    background: rgba(16, 185, 129, 0.05);
    border: 2px dashed #10b981;
    border-radius: 6px;
    min-height: 450px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    cursor: pointer;
    color: #10b981;
    transition: all 0.2s ease;
    user-select: none;
    box-sizing: border-box;
    padding: 20px;
  }
  .add-movie-to-genre-card:hover {
    background: rgba(16, 185, 129, 0.14);
    border-color: #34d399;
    color: #ffffff;
    transform: translateY(-4px);
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.2);
  }
  .add-movie-plus-circle {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.16);
    border: 2px solid #10b981;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    font-weight: bold;
    line-height: 1;
    transition: transform 0.2s, background 0.2s;
  }
  .add-movie-to-genre-card:hover .add-movie-plus-circle {
    background: #10b981;
    color: #fff;
    transform: scale(1.08);
  }
  .add-movie-label {
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 0.4px;
    text-align: center;
  }

  .bulk-add-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    overflow-y: auto;
    max-height: 62vh;
    padding: 8px;
    background: #121212;
    border: 1px solid #333;
    border-radius: 6px;
  }
  .bulk-movie-item {
    position: relative;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 6px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    cursor: pointer;
    transition: border-color 0.15s, transform 0.15s, background 0.15s;
    user-select: none;
  }
  .bulk-movie-item:hover {
    border-color: #10b981;
    transform: translateY(-2px);
  }
  .bulk-movie-item.selected {
    border: 2px solid #10b981;
    background: #064e3b;
  }
  .bulk-movie-item.hidden-card {
    opacity: 0.65;
    border-color: #7f1d1d;
  }
  .bulk-movie-cb {
    position: absolute;
    top: 6px;
    right: 6px;
    z-index: 5;
    width: 17px;
    height: 17px;
    accent-color: #10b981;
    cursor: pointer;
    margin: 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.8);
  }
  .bulk-movie-poster {
    width: 100%;
    height: 165px;
    object-fit: cover;
    display: block;
    background: #0d0d0d;
  }
  .bulk-movie-info {
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 3px;
    font-size: 11px;
  }
  .bulk-movie-title {
    color: #fff;
    font-weight: bold;
    line-height: 1.25;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 28px;
  }
  .bulk-movie-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #f5c518;
    font-size: 10px;
    font-weight: bold;
  }

  .watchlist-group {
    position: absolute;
    top: 5px;
    left: 5px;
    z-index: 10;
    display: flex;
    gap: 3px;
    background: rgba(0, 0, 0, 0.65);
    padding: 3px 5px;
    border-radius: 4px;
    backdrop-filter: blur(2px);
  }
  .watchlist-checkbox {
    width: 11px;
    height: 11px;
    cursor: pointer;
    accent-color: var(--accent-color);
    opacity: 0.9;
  }
  .watchlist-checkbox:hover { opacity: 1; transform: scale(1.15); }

  .card-position-badge {
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 11;
    background: rgba(0, 0, 0, 0.78);
    color: #f5c518;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: bold;
    line-height: 1.1;
    backdrop-filter: blur(2px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.6);
    white-space: nowrap;
    pointer-events: none;
  }

  .glorious-group {
    position: absolute;
    top: 5px;
    right: 5px;
    z-index: 10;
    background: rgba(0, 0, 0, 0.75);
    padding: 3px 5px;
    border-radius: 4px;
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
  }
  .glorious-checkbox {
    width: 11px;
    height: 11px;
    cursor: pointer;
    accent-color: #f5c518;
    opacity: 0.9;
  }
  .glorious-checkbox:hover { opacity: 1; transform: scale(1.15); }

  .select-id-radio-wrap {
    position: absolute;
    bottom: 6px;
    left: 6px;
    z-index: 10;
    background: rgba(0, 0, 0, 0.7);
    padding: 3px 5px;
    border-radius: 4px;
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    box-sizing: border-box;
  }
  .select-id-radio {
    width: 12px;
    height: 12px;
    cursor: pointer;
    accent-color: #f5c518;
    margin: 0;
  }

  .poster-badges-right {
    position: absolute;
    top: 32px;
    right: 5px;
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: flex-end;
    pointer-events: none;
  }
  .poster-badges-right > * {
    pointer-events: auto;
  }

  .relation-badge-btn {
    background: rgba(37, 99, 235, 0.9);
    color: #fff;
    border: 1px solid rgba(147, 197, 253, 0.6);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    backdrop-filter: blur(2px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.6);
    white-space: nowrap;
  }
  .relation-badge-btn:hover { background: #1d4ed8; transform: scale(1.05); }
  .relation-badge-btn.active-group { background: #f5c518; color: #000; border-color: #fff; }

  .remake-badge-btn {
    background: rgba(139, 92, 246, 0.9);
    color: #fff;
    border: 1px solid rgba(221, 214, 254, 0.6);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    backdrop-filter: blur(2px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.6);
    white-space: nowrap;
  }
  .remake-badge-btn:hover { background: #7c3aed; transform: scale(1.05); }
  .remake-badge-btn.active-group { background: #f5c518; color: #000; border-color: #fff; }

  .genre-badge-btn {
    background: rgba(16, 185, 129, 0.9);
    color: #fff;
    border: 1px solid rgba(167, 243, 208, 0.6);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    backdrop-filter: blur(2px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.6);
    white-space: nowrap;
  }
  .genre-badge-btn:hover { background: #059669; transform: scale(1.05); }
  .genre-badge-btn.active-group { background: #f5c518; color: #000; border-color: #fff; }

  .poster-badges-bottom {
    position: absolute;
    bottom: 6px;
    left: 33px;
    right: 36px;
    z-index: 9;
    display: flex;
    flex-direction: column-reverse;
    gap: 3px;
    align-items: center;
    justify-content: center;
    pointer-events: none;
  }
  .poster-badges-bottom > * {
    pointer-events: auto;
  }

  .poster-group-name-badge {
    color: #ffffff;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: center;
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    box-sizing: border-box;
    cursor: default;
    box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  }

  .card-user-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #141414;
    padding: 6px 8px;
    border-top: 1px solid var(--border-color);
    font-size: 11px;
  }
  .watched-label { display: flex; align-items: center; gap: 3px; cursor: pointer; color: #ccc; flex-shrink: 0; }
  .watched-checkbox { width: 13px; height: 13px; accent-color: #28a745; cursor: pointer; }
  .score-container { display: flex; align-items: center; gap: 3px; color: #f5c518; flex-shrink: 0; }
  .score-input { width: 36px; padding: 2px 3px; text-align: center; background: #222; color: #f5c518; border: 1px solid #444; border-radius: 3px; font-weight: bold; font-size: 11px; }

  .card-relation-bar {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 3px;
    background: #101010;
    padding: 5px 6px;
    border-top: 1px solid #262626;
    border-bottom: 1px solid var(--border-color);
    font-size: 10px;
    color: #9ca3af;
  }
  .relation-input-wrap { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
  .relation-label {
    display: inline-block;
    width: 62px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .relation-input {
    width: 35px;
    padding: 2px 2px;
    text-align: center;
    background: #1f1f1f;
    color: #93c5fd;
    border: 1px solid #374151;
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
  }
  .relation-input::placeholder { color: #555; font-weight: normal; font-size: 9px; }

  .btn-add-group {
    background: #1e3a8a;
    color: #93c5fd;
    border: 1px solid #3b82f6;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 10px;
    cursor: pointer;
    font-weight: bold;
    flex-shrink: 0;
  }
  .btn-add-group:hover { background: #2563eb; color: #fff; }

  .btn-add-remake {
    background: #5b21b6;
    color: #ddd6fe;
    border: 1px solid #7c3aed;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 10px;
    cursor: pointer;
    font-weight: bold;
    flex-shrink: 0;
  }
  .btn-add-remake:hover { background: #7c3aed; color: #fff; }

  .btn-add-genre {
    background: #065f46;
    color: #a7f3d0;
    border: 1px solid #10b981;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 10px;
    cursor: pointer;
    font-weight: bold;
    flex-shrink: 0;
  }
  .btn-add-genre:hover { background: #059669; color: #fff; }

  .genre-tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    margin-top: 2px;
  }
  .genre-tag-pill {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: #064e3b;
    color: #a7f3d0;
    border: 1px solid #10b981;
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 9px;
    max-width: 100%;
  }
  .genre-tag-pill span.g-pill-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 145px;
    cursor: pointer;
  }
  .genre-tag-pill span.g-pill-text:hover {
    text-decoration: underline;
    color: #fff;
  }
  .genre-tag-remove-btn {
    background: transparent;
    border: none;
    color: #fca5a5;
    font-weight: bold;
    font-size: 10px;
    padding: 0 2px;
    cursor: pointer;
    line-height: 1;
  }
  .genre-tag-remove-btn:hover {
    color: #ef4444;
    transform: scale(1.2);
  }

  .btn-unlink {
    flex-shrink: 0;
    background: transparent;
    color: #ef4444;
    border: 1px solid #7f1d1d;
    padding: 1px 5px;
    font-size: 10px;
    border-radius: 3px;
    cursor: pointer;
  }
  .btn-unlink:hover { background: #7f1d1d; color: #fff; }

  .poster-wrapper {
    position: relative;
    width: 100%;
    height: 290px;
    border-radius: 6px 6px 0 0;
    overflow: hidden;
  }
  .poster-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .hide-movie-btn {
    position: absolute;
    bottom: 6px;
    right: 6px;
    z-index: 10;
    background: rgba(0, 0, 0, 0.72);
    color: #e5e7eb;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
    line-height: 1;
    cursor: pointer;
    backdrop-filter: blur(2px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.6);
    opacity: 0.85;
    transition: opacity 0.15s, background 0.15s, transform 0.15s;
  }
  .hide-movie-btn:hover {
    opacity: 1;
    background: rgba(220, 38, 38, 0.9);
    color: #fff;
    border-color: #fca5a5;
    transform: scale(1.08);
  }
  .hide-movie-btn.is-hidden {
    background: rgba(220, 38, 38, 0.92);
    color: #fff;
    border-color: #fff;
    opacity: 1;
  }
  .movie-card.hidden-card {
    opacity: 0.65;
    border-color: #7f1d1d;
  }
  .show-hidden-label {
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 12px;
    font-weight: bold;
    color: var(--text-color);
    cursor: pointer;
    user-select: none;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }
  .show-hidden-label:hover {
    border-color: var(--accent-color);
  }
  .show-hidden-checkbox {
    width: 14px;
    height: 14px;
    accent-color: var(--accent-color);
    cursor: pointer;
    margin: 0;
  }
  #multiSelectCheckbox {
    accent-color: #10b981;
  }
  .card-details { padding: 10px; display: flex; flex-direction: column; flex-grow: 1; font-size: 12px; gap: 4px; overflow: hidden; }
  .domain-container { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-bottom: -1px; white-space: nowrap; overflow: hidden; }
  .domain-left { display: flex; align-items: center; gap: 3px; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
  .domain-badge { color: #60a5fa; font-size: 11px; font-weight: bold; cursor: pointer; text-decoration: underline; }
  .domain-badge:hover { color: #93c5fd; }
  .alt-url-link { color: #93c5fd; font-size: 11px; text-decoration: none; font-weight: bold; }
  .alt-url-link:hover { color: #fff; text-decoration: underline; }
  .country-badge { color: #9ca3af; font-size: 10px; font-weight: bold; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; max-width: 95px; text-align: right; }

  .movie-title { color: #fff; text-decoration: none; font-weight: bold; font-size: 13px; line-height: 1.3; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; height: 34px; }
  .movie-title:hover { color: var(--accent-color); }
  .meta-info { color: #f5c518; font-weight: bold; margin-top: 2px; display: flex; justify-content: space-between; align-items: center; }
  .film-id-badge { background: #333; color: #aaa; padding: 1px 6px; border-radius: 4px; font-size: 11px; }
  .summary-text { color: #aaa; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; font-size: 12px; line-height: 16px; height: 32px; max-height: 32px; margin-top: 2px; }
  .actors-text { color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-style: italic; height: 16px; margin-top: auto; }

  .single-grid-list {
    width: 100%;
    height: 850px;
    overflow-x: auto;
    overflow-y: hidden;
    background: #121212;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px;
    box-sizing: border-box;
    display: grid;
    grid-auto-flow: column;
    grid-template-rows: repeat(35, minmax(0, 1fr));
    grid-auto-columns: 165px;
    gap: 3px;
  }
  .single-grid-item {
    display: flex;
    align-items: center;
    padding: 1px 6px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 11px;
    line-height: 1.15;
    user-select: none;
    border: 1px solid #1f1f1f;
    background: #181818;
    height: 100%;
    box-sizing: border-box;
  }
  .single-grid-item:hover {
    background: #1f2937;
    border-color: #374151;
  }
  .single-grid-item.active-row {
    background: #1e3a8a;
    border-color: #3b82f6;
    color: #fff;
    font-weight: bold;
  }

  .multi-checkbox-list {
    width: 100%;
    height: 850px;
    overflow-x: auto;
    overflow-y: hidden;
    background: #121212;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px;
    box-sizing: border-box;
    display: grid;
    grid-auto-flow: column;
    grid-template-rows: repeat(35, minmax(0, 1fr));
    grid-auto-columns: 165px;
    gap: 3px;
  }
  .multi-checkbox-item {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 1px 6px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 11px;
    line-height: 1.15;
    user-select: none;
    border: 1px solid #1f1f1f;
    background: #181818;
    height: 100%;
    box-sizing: border-box;
  }
  .multi-checkbox-item:hover {
    background: #1f2937;
    border-color: #374151;
  }
  .multi-checkbox-item.checked-row {
    background: #10b981;
    border-color: #34d399;
    color: #052e16;
    font-weight: bold;
  }
  .multi-checkbox-item.active-row {
    outline: 2px solid #3b82f6;
    border-color: #60a5fa;
  }
  .multi-checkbox-item.checked-row.active-row {
    background: #059669;
    color: #ffffff;
    font-weight: bold;
  }
  .multi-checkbox-item input[type="checkbox"] {
    width: 12px;
    height: 12px;
    accent-color: #10b981;
    cursor: pointer;
    margin: 0;
    flex-shrink: 0;
  }
  .multi-checkbox-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
</head>
<body>

<div class="header-container">
  <div class="controls">
    <div class="search-box-wrap">
      <input type="text" id="searchInput" placeholder="Ara (ör: ali ak || veli)..." style="width: 165px;">
      <button type="button" id="searchBtn" class="btn-search" title="Ara (veya Enter'a basın)">🔍</button>
    </div>

    <select id="domainFilter"><option value="">Tüm Domainler</option></select>

    <div class="filter-slider-container" title="Film Yıl Aralığı Filtresi">
      <div class="filter-slider-header">
        <span>Yıl Aralığı:</span>
        <span id="yearRangeLabel">Tümü</span>
      </div>
      <div class="filter-sliders-wrapper">
        <input type="range" id="minYearRange" min="1900" max="2030" value="1900">
        <input type="range" id="maxYearRange" min="1900" max="2030" value="2030">
      </div>
    </div>

    <select id="countryFilter"><option value="">Tüm Ülkeler</option></select>

    <div class="filter-slider-container" title="Film Süre Aralığı Filtresi (Dakika)">
      <div class="filter-slider-header">
        <span>Süre (dk):</span>
        <span id="durationRangeLabel">Tümü</span>
      </div>
      <div class="filter-sliders-wrapper">
        <input type="range" id="minDurationRange" min="0" max="300" value="0">
        <input type="range" id="maxDurationRange" min="0" max="300" value="300">
      </div>
    </div>

    <div class="filter-slider-container" title="IMDb Puan Aralığı Filtresi">
      <div class="filter-slider-header">
        <span>IMDb Puanı:</span>
        <span id="imdbRangeLabel">Tümü</span>
      </div>
      <div class="filter-sliders-wrapper">
        <input type="range" id="minImdbRange" min="0" max="10" step="0.1" value="0">
        <input type="range" id="maxImdbRange" min="0" max="10" step="0.1" value="10">
      </div>
    </div>

    <div class="filter-slider-container" title="Kendi Puanım Aralığı Filtresi">
      <div class="filter-slider-header">
        <span>Puanlarım:</span>
        <span id="myScoreRangeLabel">Tümü</span>
      </div>
      <div class="filter-sliders-wrapper">
        <input type="range" id="minMyScoreRange" min="0" max="10" step="0.1" value="0">
        <input type="range" id="maxMyScoreRange" min="0" max="10" step="0.1" value="10">
      </div>
    </div>

    <select id="sortSelect1">
      <option value="default">1. Sıralama</option>
      <option value="imdb_desc">IMDb (Yüksek -> Düşük)</option>
      <option value="imdb_asc">IMDb (Düşük -> Yüksek)</option>
      <option value="year_desc">Yıl (En Yeni)</option>
      <option value="year_asc">Yıl (En Eski)</option>
      <option value="title_asc">İsim (A-Z)</option>
      <option value="title_desc">İsim (Z-A)</option>
    </select>

    <select id="sortSelect2">
      <option value="default">2. Sıralama</option>
      <option value="imdb_desc">IMDb (Yüksek -> Düşük)</option>
      <option value="imdb_asc">IMDb (Düşük -> Yüksek)</option>
      <option value="year_desc">Yıl (En Yeni)</option>
      <option value="year_asc">Yıl (En Eski)</option>
      <option value="title_asc">İsim (A-Z)</option>
      <option value="title_desc">İsim (Z-A)</option>
    </select>

    <select id="watchlistDropdown" style="font-weight: bold; background: #1a1a1a; color: #f5c518; border-color: #444;">
      <option value="all">📁 Tüm Arşiv</option>
      <option value="list1">📌 İzleme Listem 1</option>
      <option value="list2">📌 İzleme Listem 2</option>
      <option value="list3">📌 İzleme Listem 3</option>
      <option value="watched">✅ İzlediklerim</option>
      <option value="glorious">⭐ Muhteşem Filmler</option>
      <option value="linked_only">🎬 Seri Filmler</option>
      <option value="remake_only">🎥 Remake-Benzer Filmler</option>
      <option value="genre_only">🏷️ Türler</option>
      <option value="no_genre">🏷️ Türü Olmayanlar</option>
    </select>

    <div class="linked-sort-container" id="linkedSortContainer">
      <span>Grup Sıralama:</span>
      <select id="linkedGroupsSortSelect" style="background:#121212; color:#e0e0e0; border:1px solid #444; padding:4px; border-radius:3px; font-size:11px;">
        <option value="default">Varsayılan</option>
        <option value="alpha_asc">Alfabetik (A-Z)</option>
        <option value="alpha_desc">Alfabetik (Z-A)</option>
        <option value="count_asc">Film Sayısı (Artan)</option>
        <option value="count_desc">Film Sayısı (Azalan)</option>
      </select>
    </div>

    <label class="show-hidden-label" id="showHiddenLabel" title="Gizlenen filmleri göster/aramalara dahil et">
      <input type="checkbox" id="showHiddenCheckbox" class="show-hidden-checkbox">
      <span>👁️ Gizli Olanları Göster</span>
    </label>

    <label class="show-hidden-label" id="multiSelectLabel" title="Aktifken bir filme tür eklediğinizde veya kaldırdığınızda, filtrelere göre listelenen tüm filmlere uygular">
      <input type="checkbox" id="multiSelectCheckbox" class="show-hidden-checkbox">
      <span>☑️ Çoklu Seçim</span>
    </label>

    <div class="last-id-container">
      <span>Son ID:</span>
      <input type="number" id="lastIdInput" min="1" placeholder="ID">
      <button class="btn-go" id="goBtn">Go</button>
    </div>

    <select id="recentMoviesDropdown" title="Linkine son tıklanan 30 film (Seçildiğinde Tüm Arşiv'e geçip ilgili filme kaydırır)">
      <option value="">🕒 Geçmiş (Son 30)</option>
    </select>

    <button type="button" id="toggleAllGroupsBtn" class="btn-group-toggle" title="Tüm grupları aç/kapat">📂 Tümünü Aç</button>

    <span class="film-count-badge" title="Listelenen film sayısı">🎬 <span id="countDisplay">__COUNT_PLACEHOLDER__</span> Film</span>

    <div class="controls-bottom-row">
      <button type="button" id="toggleFilmSearchSidebarBtn" class="btn-go" title="Sağ yan panelde türlere göre film ara">🔍 Film Ara</button>
      <button type="button" id="toggleGenreAddSidebarBtn" class="btn-go" title="Sağ yan panelde (4 kolon) seçili filme tür ekle/yönet">🏷️ Tür Ekle</button>
      <button type="button" id="toggleRelatedSideBySideBtn" class="btn-go" title="Seri veya remake ilişkili filmleri filtre/aramaya dahil edip ilk filmin yanına sırala">🔗 İlişkililer Yanyana</button>
      <a href="film_editor.html" target="_blank" class="btn-go" id="editorLinkBtn" title="details.js Veri Düzenleyicisini Aç">🎬 Film Editörü</a>
      <button type="button" class="btn-go" id="toggleViewModeBtn" title="Sade Görünüm ve Kompleks Görünüm arasında geçiş yap">Sade Görünüm</button>
      <button type="button" class="btn-go" id="resetFiltersBtn" title="Sıralamalar hariç tüm filtreleri, aramayı ve aktif grup seçimini sıfırla">🧹 Filtreleri Temizle</button>
      <button type="button" class="btn-go" id="exportDataBtn" title="Tüm izleme listeleri, puanlar ve grup bağlantılarını JSON olarak indir">💾 Yedekle</button>
      <button type="button" class="btn-go" id="importDataBtn" title="Daha önce alınan JSON yedeğini geri yükle">📂 Geri Yükle</button>
      <input type="file" id="importFileInput" accept=".json" style="display: none;">
    </div>
  </div>

  <div class="relation-banner" id="relationBanner">
    <span id="relationBannerText">🔗 Grup Gösteriliyor</span>
    <button class="btn-clear-relation" id="clearRelationBtn">✕ Filtreyi Kaldır</button>
  </div>
</div>

<!-- Sağ Yan Panel (Film Ara veya 4 Kolon Tür Ekle) -->
<aside id="filmSearchSidebarPanel" class="right-sidebar-panel" aria-label="Sağ Yan Panel">
  <div class="right-sidebar-header">
    <span id="sidebarPanelTitle">🏷️ Türlere Göre Filtrele</span>
    <button type="button" id="closeFilmSearchSidebarBtn" class="right-sidebar-close-btn" title="Paneli Kapat">✕</button>
  </div>
  <div id="sidebarGenreListbox" class="sidebar-genre-listbox"></div>

  <div id="sidebarGenreAddBody" class="sidebar-genre-add-body">
    <div style="display:flex; gap:6px; align-items:center;">
      <input type="text" id="sidebarGenreSearchInput" placeholder="Tür ara..." style="flex:1; background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px 8px; border-radius:4px; font-size:12px;">
      <select id="sidebarGenreSortSelect" style="background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px; border-radius:4px; font-size:11px;">
        <option value="alpha_asc">Alfabetik (A-Z)</option>
        <option value="alpha_desc">Alfabetik (Z-A)</option>
        <option value="default">Varsayılan</option>
        <option value="count_asc">Film Sayısı (Artan)</option>
        <option value="count_desc">Film Sayısı (Azalan)</option>
      </select>
    </div>

    <div id="sidebarGenre4ColList" class="sidebar-4col-checkbox-list"></div>

    <div class="sidebar-genre-preview-box">
      <div style="font-weight:bold; color:#f5c518; border-bottom:1px solid #2b2b2b; padding-bottom:3px; margin-bottom:2px;">
        🎬 Grubun Filmleri (<span id="sidebarPreviewGroupCount">0</span>)
      </div>
      <div id="sidebarGroupPreviewList" style="display:flex; flex-direction:column; gap:3px;">
        <span style="color:#666; font-style:italic;">Bir tür seçin...</span>
      </div>
    </div>

    <div style="display:flex; gap:6px; align-items:center;">
      <input type="text" id="sidebarNewGenreInput" placeholder="Yeni tür adı..." style="flex:1; min-width:110px; background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px 8px; border-radius:4px; font-size:11.5px;">
      <button type="button" id="sidebarCreateGenreBtn" style="background:#059669; color:#fff; border:none; padding:5px 9px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:11px; white-space:nowrap;">Yeni Tür Ekle</button>
    </div>

    <div style="display:flex; gap:6px; align-items:center;">
      <input type="text" id="sidebarRenameGenreInput" placeholder="Seçili tür adı..." style="flex:1; min-width:110px; background:#121212; color:#f5c518; border:1px solid #444; padding:5px 8px; border-radius:4px; font-size:11.5px;">
      <button type="button" id="sidebarRenameGenreBtn" style="background:#d97706; color:#fff; border:none; padding:5px 9px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:11px; white-space:nowrap;">Adı Değiştir</button>
    </div>

    <div style="display:flex; justify-content:flex-end; gap:8px; border-top:1px solid #2c2c2c; padding-top:7px;">
      <button type="button" id="sidebarCancelGenreAddBtn" style="background:#333; color:#fff; border:1px solid #555; padding:5px 12px; border-radius:4px; cursor:pointer; font-size:11.5px;">Kapat</button>
      <button type="button" id="sidebarConfirmGenreAddBtn" style="background:#10b981; color:#fff; border:none; padding:5px 14px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:11.5px;">Ekle</button>
    </div>
  </div>
</aside>

<div class="pagination-bar" id="paginationTopBar"></div>
<div class="movie-grid" id="movieGridContainer"></div>
<div class="pagination-bar" id="paginationBottomBar"></div>

<!-- URL Düzenleme Popup Modal -->
<div id="urlPopupModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; justify-content:center; align-items:center;">
  <div style="background:#1e1e1e; border:1px solid #333; padding:20px; border-radius:8px; width:500px; max-width:90%; color:#e0e0e0; box-shadow:0 4px 20px rgba(0,0,0,0.8);">
    <h3 style="margin-top:0; color:#f5c518;">Film URL Yönetimi (ID: <span id="popupMovieId"></span>)</h3>
    <p style="font-size:12px; color:#aaa; margin-bottom:10px;">İlk satır ana URL'dir. Altına ekleyeceğiniz her yeni satır alternatif URL (URL2, URL3...) olarak kaydedilir.</p>
    <textarea id="urlPopupTextarea" rows="8" style="width:100%; background:#121212; color:#e0e0e0; border:1px solid #444; padding:8px; border-radius:4px; font-family:monospace; font-size:12px; box-sizing:border-box;"></textarea>
    <div style="margin-top:15px; display:flex; justify-content:flex-end; gap:8px;">
      <button type="button" onclick="closeUrlPopup()" style="background:#333; color:#fff; border:1px solid #555; padding:6px 12px; border-radius:4px; cursor:pointer;">İptal</button>
      <button type="button" onclick="saveUrlPopup()" style="background:#e50914; color:#fff; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; font-weight:bold;">Kaydet</button>
    </div>
  </div>
</div>

<!-- Yeni Grup Oluşturulurken İsim Verme Popup Modal -->
<div id="groupNamePopupModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; justify-content:center; align-items:center;">
  <div style="background:#1e1e1e; border:1px solid #333; padding:20px; border-radius:8px; width:450px; max-width:90%; color:#e0e0e0; box-shadow:0 4px 20px rgba(0,0,0,0.8);">
    <h3 style="margin-top:0; color:#f5c518;" id="groupNameModalTitle">📁 Yeni Grup Adı Belirle</h3>
    <p style="font-size:12px; color:#aaa; margin-bottom:10px;">Bu yeni grup için bir isim girin:</p>
    <input type="text" id="groupNameInput" style="width:100%; background:#121212; color:#e0e0e0; border:1px solid #444; padding:8px; border-radius:4px; font-size:13px; box-sizing:border-box; margin-bottom:15px;">
    <div style="display:flex; justify-content:flex-end; gap:8px;">
      <button type="button" onclick="closeGroupNamePopup(false)" style="background:#333; color:#fff; border:1px solid #555; padding:6px 12px; border-radius:4px; cursor:pointer;">Atla</button>
      <button type="button" onclick="closeGroupNamePopup(true)" style="background:#e50914; color:#fff; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; font-weight:bold;">Kaydet</button>
    </div>
  </div>
</div>

<!-- Grup Seçim Modal -->
<div id="groupSelectPopupModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:9999; justify-content:center; align-items:center;">
  <div style="background:#1e1e1e; border:1px solid #333; padding:12px 16px; border-radius:8px; width:1470px; max-width:98%; max-height:98vh; overflow-y:auto; color:#e0e0e0; box-shadow:0 4px 20px rgba(0,0,0,0.85);">
    <div style="display:flex; gap:14px;">
      <div style="flex: 1; min-width: 0; display:flex; flex-direction:column;">
        <div style="display:flex; gap:6px; margin-bottom:8px;">
          <input type="text" id="groupSearchInput" placeholder="Grup ara..." style="flex:1; background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px 8px; border-radius:4px; font-size:12px; box-sizing:border-box;">
          <select id="groupPopupSortSelect" style="background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px; border-radius:4px; font-size:11px;">
            <option value="default">Varsayılan</option>
            <option value="alpha_asc">Alfabetik (A-Z)</option>
            <option value="alpha_desc">Alfabetik (Z-A)</option>
            <option value="count_asc">Film Sayısı (Artan)</option>
            <option value="count_desc">Film Sayısı (Azalan)</option>
          </select>
        </div>
        <div id="groupSelectDropdown" class="single-grid-list"></div>
        <div id="groupSelectCheckboxList" class="multi-checkbox-list" style="display:none;"></div>
      </div>

      <div style="width: 252px; flex-shrink: 0; background: #151515; border: 1px solid #333; border-radius: 6px; padding: 10px 12px; display: flex; flex-direction: column;">
        <div style="font-size: 12px; font-weight: bold; color: #f5c518; margin-bottom: 6px; border-bottom: 1px solid #333; padding-bottom: 5px;">🎬 Grubun Filmleri (<span id="previewGroupCount">0</span>)</div>
        <div id="groupPreviewList" style="flex: 1; overflow-y: auto; max-height: 850px; display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: #bbb;">
          <span style="color: #666; font-style: italic; padding: 10px; text-align: center;">Soldan bir grup seçin...</span>
        </div>
      </div>
    </div>

    <div style="margin-top:8px; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px; border-top:1px solid #2c2c2c; padding-top:8px;">
      <div style="display:flex; align-items:center; gap:6px; flex: 1 1 250px;">
        <input type="text" id="newGroupInPopupInput" placeholder="Yeni grup adı..." style="flex:1; min-width:130px; background:#121212; color:#e0e0e0; border:1px solid #444; padding:5px 9px; border-radius:4px; font-size:12px;">
        <button type="button" id="createNewGroupInPopupBtn" style="background:#059669; color:#fff; border:none; padding:5px 11px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:12px; white-space:nowrap;">Yeni Tür Ekle</button>
      </div>

      <div style="display:flex; align-items:center; gap:6px; flex: 1 1 250px;">
        <input type="text" id="renameGroupInPopupInput" placeholder="Seçili grup adı..." style="flex:1; min-width:130px; background:#121212; color:#f5c518; border:1px solid #444; padding:5px 9px; border-radius:4px; font-size:12px;">
        <button type="button" id="renameGroupInPopupBtn" style="background:#d97706; color:#fff; border:none; padding:5px 11px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:12px; white-space:nowrap;">Adı Değiştir</button>
      </div>

      <div style="display:flex; align-items:center; gap:8px; justify-content:flex-end;">
        <button type="button" id="closeGroupSelectModalBtn" style="background:#333; color:#fff; border:1px solid #555; padding:5px 14px; border-radius:4px; cursor:pointer;">İptal</button>
        <button type="button" id="confirmGroupSelectBtn" style="background:#3b82f6; color:#fff; border:none; padding:5px 14px; border-radius:4px; cursor:pointer; font-weight:bold;">Ekle</button>
      </div>
    </div>
  </div>
</div>

<!-- Tür Sayfasından Toplu Film Ekleme Modal -->
<div id="bulkAddMoviesToGenreModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.78); z-index:9999; justify-content:center; align-items:center;">
  <div style="background:#1e1e1e; border:1px solid #333; padding:20px; border-radius:8px; width:1140px; max-width:96%; color:#e0e0e0; box-shadow:0 6px 28px rgba(0,0,0,0.85); display:flex; flex-direction:column; gap:12px;">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px;">
      <h3 style="margin:0; color:#10b981;" id="bulkAddGenreModalTitle">🏷️ Türe Film Ekle</h3>
      <span style="font-size:12px; color:#f5c518; font-weight:bold;" id="bulkAddSelectedCountBadge">Seçili: 0 Film</span>
    </div>

    <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center; background:#141414; padding:10px; border-radius:6px; border:1px solid #2e2e2e;">
      <input type="text" id="bulkSearchInput" placeholder="Film adı, oyuncu, özet (||)..." style="width:190px;">
      <select id="bulkDomainFilter"><option value="">Tüm Domainler</option></select>
      <div style="display:flex; align-items:center; gap:4px; background:#1e1e1e; border:1px solid #333; padding:4px 8px; border-radius:4px; font-size:11px;">
        <span style="color:#f5c518; font-weight:bold;">Yıl:</span>
        <input type="number" id="bulkMinYear" placeholder="Min" style="width:54px; padding:3px 5px; text-align:center;">
        <span>-</span>
        <input type="number" id="bulkMaxYear" placeholder="Max" style="width:54px; padding:3px 5px; text-align:center;">
      </div>
      <div style="display:flex; align-items:center; gap:4px; background:#1e1e1e; border:1px solid #333; padding:4px 8px; border-radius:4px; font-size:11px;">
        <span style="color:#f5c518; font-weight:bold;">IMDb:</span>
        <input type="number" id="bulkMinImdb" step="0.1" min="0" max="10" placeholder="Min" style="width:48px; padding:3px 5px; text-align:center;">
        <span>-</span>
        <input type="number" id="bulkMaxImdb" step="0.1" min="0" max="10" placeholder="Max" style="width:48px; padding:3px 5px; text-align:center;">
      </div>
      <select id="bulkSortSelect">
        <option value="default">Sıralama: Varsayılan</option>
        <option value="imdb_desc">IMDb (Yüksek -> Düşük)</option>
        <option value="imdb_asc">IMDb (Düşük -> Yüksek)</option>
        <option value="year_desc">Yıl (En Yeni)</option>
        <option value="year_asc">Yıl (En Eski)</option>
        <option value="title_asc">İsim (A-Z)</option>
        <option value="title_desc">İsim (Z-A)</option>
      </select>
      <label class="show-hidden-label" title="Gizlenen filmleri göster/aramalara dahil et" style="padding:4px 8px; font-size:11px;">
        <input type="checkbox" id="bulkShowHiddenCheckbox" class="show-hidden-checkbox">
        <span>👁️ Gizlileri Göster</span>
      </label>
      <button type="button" id="bulkResetFiltersBtn" style="background:#2d1b1b; color:#fca5a5; border:1px solid #7f1d1d; font-size:11px;">Filtreleri Sıfırla</button>
      <span style="margin-left:auto; font-size:11px; color:#aaa;" id="bulkFilteredCountLabel">0 Film</span>
    </div>

    <div id="bulkMoviesGrid" class="bulk-add-grid"></div>

    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #333; padding-top:10px;">
      <span style="font-size:11px; color:#9ca3af;">* Bir film seçildiğinde bağlı olduğu Seri ve Remake zincirindeki filmler de anında otomatik seçilir.</span>
      <div style="display:flex; gap:8px;">
        <button type="button" id="closeBulkAddModalBtn" style="background:#333; color:#fff; border:1px solid #555; padding:7px 14px;">İptal</button>
        <button type="button" id="confirmBulkAddBtn" style="background:#10b981; color:#fff; border:none; padding:7px 16px; font-weight:bold;">Seçilenleri Ekle</button>
      </div>
    </div>
  </div>
</div>

<script>
  const allMovies = JSON.parse(decodeURIComponent('__MOVIES_JSON_PLACEHOLDER__'));
  const validMovieIds = new Set(allMovies.map(m => String(m.film_ID)));

  const PAGE_SIZE = 60;
  let currentPage = 1;
  let activeOrderedMovieIds = [];
  let activeGroupedDataCache = new Map();
  let persistentHighlightedMovieId = null;

  let watchlist1State = {};
  let watchlist2State = {};
  let watchlist3State = {};
  let watchedState = {};
  let gloriousState = {};
  let myScoreState = {};
  let hiddenMoviesState = {};
  let recentMoviesState = [];
  let isSimpleViewMode = false;
  let isRelatedSideBySideMode = false;
  let currentlyRenderedMovieIds = [];

  let seriesMoviesGroupsState = [];
  let seriesGroupsNamesState = {};

  let remakeMoviesGroupsState = [];
  let remakeGroupsNamesState = {};

  let genreMoviesGroupsState = [];
  let genreGroupsNamesState = {};

  let sidebarSelectedGenreKeys = new Set();
  let sidebarMode = null; // null | "filter" | "genre_add"
  let sidebarTargetMovieId = null;
  let sidebarGenreTempCreatedKeys = [];
  let sidebarGenreSelectedKeys = new Set();
  let sidebarGenreFocusedKey = null;

  let alternativeUrlsState = {};
  let activeRelationFilterSet = null;
  let currentPopupMovieId = null;

  let pendingGroupSource = null;
  let pendingGroupTarget = null;
  let pendingGroupType = null;
  let activeMovieIdForGroupSelect = null;
  let activeGroupSelectType = null;
  let cachedGroupListForPopup = [];
  let tempCreatedGroupKeysInPopup = [];
  let selectedGenreKeysInPopup = new Set();
  let focusedGenreKeyInPopup = null;
  let selectedSingleGroupIndexInPopup = null;

  let targetGenreKeyForBulkAdd = null;
  let bulkSelectedMovieIds = new Set();

  let minGlobalYear = 1900;
  let maxGlobalYear = 2030;
  let minGlobalDuration = 0;
  let maxGlobalDuration = 300;

  function renderMoviesPreservingScroll() {
    const savedScrollY = window.scrollY;
    renderMovies(false, true);
    requestAnimationFrame(() => {
      window.scrollTo({ top: savedScrollY, behavior: 'instant' });
    });
  }

  function applyPersistentHighlight() {
    document.querySelectorAll(".movie-card.highlight").forEach(el => {
      el.classList.remove("highlight");
    });
    if (!persistentHighlightedMovieId) return;
    const targetElem = document.querySelector(`[data-movie-id-card="${String(persistentHighlightedMovieId)}"]`);
    if (targetElem) {
      targetElem.classList.add("highlight");
    }
  }

  function syncCardRadioSelection(movieId) {
    const fid = String(movieId || "").trim();
    document.querySelectorAll('input[name="selectedMovieRadio"]').forEach(radio => {
      const card = radio.closest(".movie-card");
      radio.checked = !!(fid && card && card.dataset.movieIdCard === fid);
    });
  }

  function getCheckedRadioMovieId() {
    const checkedRadio = document.querySelector('input[name="selectedMovieRadio"]:checked');
    if (!checkedRadio) return null;
    const card = checkedRadio.closest(".movie-card");
    const fid = card && card.dataset.movieIdCard ? String(card.dataset.movieIdCard).trim() : "";
    return fid && validMovieIds.has(fid) ? fid : null;
  }

  function updateMultiSelectUI() {
    const cb = document.getElementById("multiSelectCheckbox");
    if (!cb) return;
    document.body.classList.toggle("multi-select-page-bg", !!cb.checked);
  }

  function applyRelatedSideBySideUI() {
    const btn = document.getElementById("toggleRelatedSideBySideBtn");
    if (!btn) return;
    btn.classList.toggle("is-side-by-side", !!isRelatedSideBySideMode);
  }

  function toggleRelatedSideBySide() {
    isRelatedSideBySideMode = !isRelatedSideBySideMode;
    applyRelatedSideBySideUI();
    renderMovies(false);
  }

  function getTargetMovieIdsForGenreAction(seedMovieId) {
    const multiCb = document.getElementById("multiSelectCheckbox");
    if (multiCb && multiCb.checked) {
      const ids = Array.from(new Set(currentlyRenderedMovieIds.map(String)));
      if (ids.length > 0) return ids;
    }
    return [String(seedMovieId)];
  }

  function syncSimpleViewControlsPlacement() {
    const bottomRow = document.querySelector(".controls-bottom-row");
    const controls = document.querySelector(".controls");
    const lastIdBox = document.querySelector(".last-id-container");
    const countBadge = document.querySelector(".film-count-badge");
    const recentDrop = document.getElementById("recentMoviesDropdown");
    const toggleGroupsBtn = document.getElementById("toggleAllGroupsBtn");
    if (!bottomRow || !controls || !lastIdBox || !countBadge) return;

    if (isSimpleViewMode) {
      if (lastIdBox.parentElement !== bottomRow) {
        bottomRow.prepend(lastIdBox);
      }
      if (countBadge.parentElement !== bottomRow) {
        lastIdBox.insertAdjacentElement("afterend", countBadge);
      }
    } else {
      if (lastIdBox.parentElement !== controls) {
        if (recentDrop && recentDrop.parentElement === controls) {
          controls.insertBefore(lastIdBox, recentDrop);
        } else {
          controls.insertBefore(lastIdBox, bottomRow);
        }
      }
      if (countBadge.parentElement !== controls) {
        if (toggleGroupsBtn && toggleGroupsBtn.parentElement === controls) {
          toggleGroupsBtn.insertAdjacentElement("afterend", countBadge);
        } else {
          controls.insertBefore(countBadge, bottomRow);
        }
      }
    }
  }

  function applyViewModeUI() {
    const btn = document.getElementById("toggleViewModeBtn");
    if (isSimpleViewMode) {
      if (sidebarMode === "genre_add") {
        setSidebarMode(null);
      }
      document.body.classList.add("simple-view");
      if (btn) {
        btn.innerText = "Kompleks Görünüm";
        btn.classList.add("is-simple");
      }
    } else {
      document.body.classList.remove("simple-view");
      if (btn) {
        btn.innerText = "Sade Görünüm";
        btn.classList.remove("is-simple");
      }
    }
    syncSimpleViewControlsPlacement();
  }

  function toggleViewMode() {
    isSimpleViewMode = !isSimpleViewMode;
    try {
      localStorage.setItem("archive_simple_view_mode", isSimpleViewMode ? "1" : "0");
    } catch (e) {}
    applyViewModeUI();
  }

  try {
    isSimpleViewMode = localStorage.getItem("archive_simple_view_mode") === "1";
  } catch (e) {
    isSimpleViewMode = false;
  }
  applyViewModeUI();

  function cleanupSidebarTempGenres() {
    if (!sidebarGenreTempCreatedKeys || sidebarGenreTempCreatedKeys.length === 0) return;
    sidebarGenreTempCreatedKeys.forEach(tKey => {
      const idx = genreMoviesGroupsState.findIndex(g => g[0] === tKey);
      if (idx !== -1 && genreMoviesGroupsState[idx].slice(1).length < 1) {
        genreMoviesGroupsState.splice(idx, 1);
        delete genreGroupsNamesState[tKey];
      }
    });
    sidebarGenreTempCreatedKeys = [];
  }

  function applySidebarGenreSelectionImmediately(genreKey, isChecked) {
    if (!genreKey) return;

    if (isChecked) {
      sidebarGenreSelectedKeys.add(genreKey);
    } else {
      sidebarGenreSelectedKeys.delete(genreKey);
    }

    const targetId = getCheckedRadioMovieId();
    if (!targetId) {
      alert("Seçili film yok");
      loadMovieGenresIntoSidebar();
      return;
    }

    const batchMovieIds = getTargetMovieIdsForGenreAction(targetId);
    const isMultiMode = !!(document.getElementById("multiSelectCheckbox")?.checked);

    if (isChecked) {
      batchMovieIds.forEach(mId => propagateGenreToRelatedMovies(mId, genreKey, false));
      const tempIdx = sidebarGenreTempCreatedKeys.indexOf(genreKey);
      if (tempIdx !== -1) {
        sidebarGenreTempCreatedKeys.splice(tempIdx, 1);
      }
      saveGenreGroups();
    } else {
      if (isMultiMode) {
        batchMovieIds.forEach(mId => unlinkMovie(mId, "genre", genreKey, false));
      } else {
        unlinkMovie(targetId, "genre", genreKey, false);
      }
      saveGenreGroups();
    }

    const grpObj = genreMoviesGroupsState.find(g => g[0] === genreKey);
    if (sidebarGenreFocusedKey === genreKey) {
      updateSidebarGenrePreview(grpObj ? grpObj.slice(1) : null);
    }

    renderMoviesPreservingScroll();
  }

  function loadMovieGenresIntoSidebar() {
    const checkedId = getCheckedRadioMovieId();
    sidebarTargetMovieId = checkedId;
    sidebarGenreSelectedKeys = new Set();
    sidebarGenreFocusedKey = null;

    const titleEl = document.getElementById("sidebarPanelTitle");
    if (!checkedId) {
      if (titleEl && sidebarMode === "genre_add") {
        titleEl.innerText = "🏷️ Tür Ekle — Seçili film yok";
      }
      const listEl = document.getElementById("sidebarGenre4ColList");
      if (listEl) {
        listEl.innerHTML = `<div style="grid-column:1/-1; color:#fca5a5; padding:12px; font-size:11.5px;">Seçili film yok</div>`;
      }
      updateSidebarGenrePreview(null);
      const renameEl = document.getElementById("sidebarRenameGenreInput");
      if (renameEl) renameEl.value = "";
      return;
    }

    const existingGenres = getGenreGroupsForMovie(checkedId);
    existingGenres.forEach(g => sidebarGenreSelectedKeys.add(g[0]));
    if (existingGenres.length > 0) {
      sidebarGenreFocusedKey = existingGenres[0][0];
    }

    const movieObj = allMovies.find(m => String(m.film_ID) === String(checkedId));
    if (titleEl && sidebarMode === "genre_add") {
      titleEl.innerText = movieObj
        ? `🏷️ Tür Ekle — ${movieObj.film_name} (ID: ${checkedId})`
        : `🏷️ Tür Ekle (ID: ${checkedId})`;
    }

    renderSidebar4ColGenreList(sidebarGenreFocusedKey);
  }

  function setSidebarMode(mode) {
    if (sidebarMode === "genre_add" && mode !== "genre_add") {
      cleanupSidebarTempGenres();
      saveGenreGroups();
    }

    if (sidebarMode === "filter" && mode !== "filter") {
      sidebarSelectedGenreKeys.clear();
    }

    sidebarMode = mode;
    const panel = document.getElementById("filmSearchSidebarPanel");
    const filterBtn = document.getElementById("toggleFilmSearchSidebarBtn");
    const genreAddBtn = document.getElementById("toggleGenreAddSidebarBtn");
    const titleEl = document.getElementById("sidebarPanelTitle");

    document.body.classList.remove("sidebar-open-filter", "sidebar-open-genre-add");
    if (panel) {
      panel.classList.remove("open", "genre-add-mode");
    }
    if (filterBtn) filterBtn.classList.remove("is-open");
    if (genreAddBtn) genreAddBtn.classList.remove("is-open");

    if (mode === "filter") {
      if (panel) panel.classList.add("open");
      document.body.classList.add("sidebar-open-filter");
      if (filterBtn) filterBtn.classList.add("is-open");
      if (titleEl) titleEl.innerText = "🏷️ Türlere Göre Filtrele";
      renderMovies(false);
    } else if (mode === "genre_add") {
      if (panel) panel.classList.add("open", "genre-add-mode");
      document.body.classList.add("sidebar-open-genre-add");
      if (genreAddBtn) genreAddBtn.classList.add("is-open");
      const searchEl = document.getElementById("sidebarGenreSearchInput");
      if (searchEl) searchEl.value = "";
      const newEl = document.getElementById("sidebarNewGenreInput");
      if (newEl) newEl.value = "";
      const renameEl = document.getElementById("sidebarRenameGenreInput");
      if (renameEl) renameEl.value = "";
      const sortEl = document.getElementById("sidebarGenreSortSelect");
      if (sortEl) sortEl.value = "alpha_asc";

      if (!getCheckedRadioMovieId()) {
        alert("Seçili film yok");
      }
      loadMovieGenresIntoSidebar();
    } else {
      renderMovies(false);
    }
  }

  function updateSidebarGenrePreview(memberIds) {
    const previewListEl = document.getElementById("sidebarGroupPreviewList");
    const countEl = document.getElementById("sidebarPreviewGroupCount");
    if (!previewListEl || !countEl) return;

    const showHidden = document.getElementById("showHiddenCheckbox").checked;
    const visibleMemberIds = memberIds ? (showHidden ? memberIds : memberIds.filter(id => !hiddenMoviesState[id])) : [];

    countEl.innerText = visibleMemberIds.length;
    if (visibleMemberIds.length === 0) {
      previewListEl.innerHTML = `<span style="color:#666; font-style:italic;">Bu türde henüz film yok</span>`;
      return;
    }

    let htmlContent = "";
    visibleMemberIds.forEach(mId => {
      const movieObj = allMovies.find(m => String(m.film_ID) === String(mId));
      const mName = movieObj ? movieObj.film_name : `Film #${mId}`;
      const mYear = movieObj && movieObj.year ? `(${movieObj.year})` : "";
      const mImdb = movieObj && movieObj.imdb_score ? `⭐ ${movieObj.imdb_score}` : "";

      htmlContent += `
        <div style="background:#1e1e1e; border:1px solid #333; padding:3px 7px; border-radius:3px; display:flex; justify-content:space-between; align-items:center; gap:6px;">
          <span style="color:#fff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(mName)}">${escapeHtml(mName)} ${mYear}</span>
          <span style="color:#f5c518; font-size:10px; flex-shrink:0;">${mImdb}</span>
        </div>
      `;
    });
    previewListEl.innerHTML = htmlContent;
  }

  function getSidebarGenreItems() {
    const showHidden = document.getElementById("showHiddenCheckbox").checked;
    const items = [];
    genreMoviesGroupsState.forEach((g, idx) => {
      if (!Array.isArray(g) || g.length === 0) return;
      const gKey = g[0];
      const memberIds = g.slice(1);
      const visibleMembers = showHidden ? memberIds : memberIds.filter(id => !hiddenMoviesState[id]);
      const isTemp = sidebarGenreTempCreatedKeys.includes(gKey);
      if (!isTemp && visibleMembers.length < 1) return;

      const gName = getGenreGroupName(g);
      items.push({
        originalIndex: idx,
        groupKey: gKey,
        name: gName,
        rawName: gName,
        count: visibleMembers.length,
        members: memberIds
      });
    });
    return items;
  }

  function setFocusedSidebarGenreRow(groupKey) {
    sidebarGenreFocusedKey = groupKey;
    const items = getSidebarGenreItems();
    const matched = items.find(i => i.groupKey === groupKey);
    updateSidebarGenrePreview(matched ? matched.members : null);

    const renameEl = document.getElementById("sidebarRenameGenreInput");
    if (renameEl) {
      renameEl.value = matched ? matched.rawName : "";
    }

    const listEl = document.getElementById("sidebarGenre4ColList");
    if (listEl) {
      listEl.querySelectorAll(".multi-checkbox-item").forEach(row => {
        row.classList.toggle("active-row", row.dataset.groupKey === groupKey);
      });
    }
  }

  function renderSidebar4ColGenreList(selectTargetKey = null) {
    const listEl = document.getElementById("sidebarGenre4ColList");
    if (!listEl) return;

    const query = (document.getElementById("sidebarGenreSearchInput")?.value || "").toLowerCase().trim();
    const sortVal = document.getElementById("sidebarGenreSortSelect")?.value || "alpha_asc";

    let items = getSidebarGenreItems();
    if (query) {
      items = items.filter(i => i.name.toLowerCase().includes(query));
    }

    items.sort((a, b) => {
      if (sortVal === "alpha_asc") return a.rawName.localeCompare(b.rawName, "tr");
      if (sortVal === "alpha_desc") return b.rawName.localeCompare(a.rawName, "tr");
      if (sortVal === "default") return a.originalIndex - b.originalIndex;
      if (sortVal === "count_asc") return (a.count - b.count) || a.rawName.localeCompare(b.rawName, "tr");
      if (sortVal === "count_desc") return (b.count - a.count) || b.rawName.localeCompare(a.rawName, "tr");
      return 0;
    });

    listEl.innerHTML = "";
    if (items.length === 0) {
      listEl.innerHTML = `<div style="grid-column:1/-1; color:#888; padding:12px; font-style:italic; font-size:11px;">Eşleşen tür bulunamadı</div>`;
      updateSidebarGenrePreview(null);
      const renameEl = document.getElementById("sidebarRenameGenreInput");
      if (renameEl) renameEl.value = "";
      return;
    }

    if (selectTargetKey && items.some(i => i.groupKey === selectTargetKey)) {
      sidebarGenreFocusedKey = selectTargetKey;
    } else if (!sidebarGenreFocusedKey || !items.some(i => i.groupKey === sidebarGenreFocusedKey)) {
      sidebarGenreFocusedKey = items[0].groupKey;
    }

    const frag = document.createDocumentFragment();
    items.forEach(item => {
      const isChecked = sidebarGenreSelectedKeys.has(item.groupKey);
      const row = document.createElement("div");
      row.className = "multi-checkbox-item"
        + (isChecked ? " checked-row" : "")
        + (item.groupKey === sidebarGenreFocusedKey ? " active-row" : "");
      row.style.height = "auto";
      row.style.padding = "4px 6px";
      row.dataset.groupKey = item.groupKey;

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = isChecked;

      cb.addEventListener("change", (e) => {
        e.stopPropagation();
        row.classList.toggle("checked-row", cb.checked);
        setFocusedSidebarGenreRow(item.groupKey);
        applySidebarGenreSelectionImmediately(item.groupKey, cb.checked);
      });

      const lbl = document.createElement("span");
      lbl.className = "multi-checkbox-label";
      lbl.textContent = item.name;
      lbl.title = item.name;

      row.appendChild(cb);
      row.appendChild(lbl);

      row.addEventListener("click", (e) => {
        if (e.target !== cb) {
          cb.checked = !cb.checked;
          row.classList.toggle("checked-row", cb.checked);
          setFocusedSidebarGenreRow(item.groupKey);
          applySidebarGenreSelectionImmediately(item.groupKey, cb.checked);
        } else {
          setFocusedSidebarGenreRow(item.groupKey);
        }
      });

      frag.appendChild(row);
    });

    listEl.appendChild(frag);
    setFocusedSidebarGenreRow(sidebarGenreFocusedKey);
  }

  function createNewGenreInSidebar() {
    const inputEl = document.getElementById("sidebarNewGenreInput");
    const newName = inputEl ? inputEl.value.trim() : "";
    if (!newName) {
      alert("Lütfen yeni tür için bir ad yazın.");
      if (inputEl) inputEl.focus();
      return;
    }

    const existing = genreMoviesGroupsState.find(g =>
      (genreGroupsNamesState[g[0]] || "").trim().toLowerCase() === newName.toLowerCase()
    );

    if (existing) {
      const exKey = existing[0];
      if (inputEl) inputEl.value = "";
      const searchEl = document.getElementById("sidebarGenreSearchInput");
      if (searchEl) searchEl.value = "";
      sidebarGenreFocusedKey = exKey;
      applySidebarGenreSelectionImmediately(exKey, true);
      renderSidebar4ColGenreList(exKey);
      return;
    }

    const newKey = generateUniqueGroupKey("genre");
    genreMoviesGroupsState.push([newKey]);
    genreGroupsNamesState[newKey] = newName;
    sidebarGenreTempCreatedKeys.push(newKey);
    sidebarGenreFocusedKey = newKey;

    if (inputEl) inputEl.value = "";
    const searchEl = document.getElementById("sidebarGenreSearchInput");
    if (searchEl) searchEl.value = "";

    const targetId = getCheckedRadioMovieId();
    if (targetId) {
      applySidebarGenreSelectionImmediately(newKey, true);
    } else {
      sidebarGenreSelectedKeys.add(newKey);
      saveGenreGroups();
    }
    renderSidebar4ColGenreList(newKey);
  }

  function renameFocusedGenreInSidebar() {
    const renameEl = document.getElementById("sidebarRenameGenreInput");
    const newName = renameEl ? renameEl.value.trim() : "";
    if (!newName) {
      alert("Tür adı boş olamaz.");
      if (renameEl) renameEl.focus();
      return;
    }
    if (!sidebarGenreFocusedKey) {
      alert("Lütfen önce listeden adı değiştirilecek bir tür seçin.");
      return;
    }

    genreGroupsNamesState[sidebarGenreFocusedKey] = newName;
    saveGenreGroups();
    renderSidebar4ColGenreList(sidebarGenreFocusedKey);
    updateRelationBanner();
    renderMoviesPreservingScroll();
  }

  function confirmSidebarGenreAdd() {
    const targetId = getCheckedRadioMovieId();
    if (!targetId) {
      alert("Seçili film yok");
      loadMovieGenresIntoSidebar();
      return;
    }

    const batchMovieIds = getTargetMovieIdsForGenreAction(targetId);
    const isMultiMode = !!(document.getElementById("multiSelectCheckbox")?.checked);
    const currentAssignedKeys = new Set(getGenreGroupsForMovie(targetId).map(g => g[0]));

    sidebarGenreSelectedKeys.forEach(gKey => {
      if (isMultiMode || !currentAssignedKeys.has(gKey)) {
        batchMovieIds.forEach(mId => propagateGenreToRelatedMovies(mId, gKey, false));
      }
    });

    if (!isMultiMode) {
      currentAssignedKeys.forEach(oldKey => {
        if (!sidebarGenreSelectedKeys.has(oldKey)) {
          unlinkMovie(targetId, "genre", oldKey, false);
        }
      });
    }

    cleanupSidebarTempGenres();
    saveGenreGroups();
    renderMoviesPreservingScroll();
    loadMovieGenresIntoSidebar();
  }

  function getMovieGenreKeySet(movieId) {
    const gs = getGenreGroupsForMovie(movieId);
    const keySet = new Set();
    gs.forEach(g => {
      if (Array.isArray(g) && g.length >= 2) {
        keySet.add(g[0]);
      }
    });
    return keySet;
  }

  function renderSidebarGenreListbox(candidateMovies, showHidden) {
    const listbox = document.getElementById("sidebarGenreListbox");
    if (!listbox) return;

    const existingKeys = new Set(genreMoviesGroupsState.map(g => g[0]));
    sidebarSelectedGenreKeys = new Set(Array.from(sidebarSelectedGenreKeys).filter(k => existingKeys.has(k)));

    const coOccurringGenreKeys = new Set();
    (candidateMovies || []).forEach(movie => {
      const mGenres = getGenreGroupsForMovie(movie.film_ID);
      mGenres.forEach(g => {
        if (Array.isArray(g) && g.length >= 2) {
          const visibleMembers = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
          if (visibleMembers.length >= 1) {
            coOccurringGenreKeys.add(g[0]);
          }
        }
      });
    });

    const visibleGenreKeySet = new Set(coOccurringGenreKeys);
    sidebarSelectedGenreKeys.forEach(k => visibleGenreKeySet.add(k));

    const items = [];
    genreMoviesGroupsState.forEach(g => {
      if (!Array.isArray(g) || g.length < 2) return;
      const gKey = g[0];
      if (!visibleGenreKeySet.has(gKey)) return;
      const visibleMembers = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
      if (visibleMembers.length < 1 && !sidebarSelectedGenreKeys.has(gKey)) return;

      items.push({
        groupKey: gKey,
        name: getGenreGroupName(g)
      });
    });

    items.sort((a, b) => a.name.localeCompare(b.name, "tr"));

    listbox.innerHTML = "";
    if (items.length === 0) {
      listbox.innerHTML = `<div style="color:#888; padding:10px; font-size:11px; font-style:italic;">Gösterilecek tür bulunamadı</div>`;
      return;
    }

    const frag = document.createDocumentFragment();
    items.forEach(item => {
      const isChecked = sidebarSelectedGenreKeys.has(item.groupKey);
      const row = document.createElement("div");
      row.className = "sidebar-genre-item" + (isChecked ? " checked-row" : "");
      row.dataset.groupKey = item.groupKey;

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = isChecked;

      const toggleSelection = () => {
        if (cb.checked) {
          sidebarSelectedGenreKeys.add(item.groupKey);
        } else {
          sidebarSelectedGenreKeys.delete(item.groupKey);
        }
        renderMovies(false);
      };

      cb.addEventListener("change", (e) => {
        e.stopPropagation();
        toggleSelection();
      });

      row.addEventListener("click", (e) => {
        if (e.target !== cb) {
          cb.checked = !cb.checked;
          toggleSelection();
        }
      });

      const lbl = document.createElement("span");
      lbl.className = "sidebar-genre-label";
      lbl.textContent = item.name;
      lbl.title = item.name;

      row.appendChild(cb);
      row.appendChild(lbl);
      frag.appendChild(row);
    });

    listbox.appendChild(frag);
  }

  function generateUniqueGroupKey(type) {
    let prefix = "g_";
    let groupsList = genreMoviesGroupsState;
    let namesObj = genreGroupsNamesState;

    if (type === "series") {
      prefix = "s_";
      groupsList = seriesMoviesGroupsState;
      namesObj = seriesGroupsNamesState;
    } else if (type === "remake") {
      prefix = "r_";
      groupsList = remakeMoviesGroupsState;
      namesObj = remakeGroupsNamesState;
    }

    let maxNum = 0;
    const regex = new RegExp("^" + prefix + "(\\d+)$");

    groupsList.forEach(g => {
      if (Array.isArray(g) && g.length > 0) {
        const m = String(g[0]).match(regex);
        if (m) {
          const n = parseInt(m[1], 10);
          if (n > maxNum) maxNum = n;
        }
      }
    });

    Object.keys(namesObj || {}).forEach(k => {
      const m = String(k).match(regex);
      if (m) {
        const n = parseInt(m[1], 10);
        if (n > maxNum) maxNum = n;
      }
    });

    return prefix + (maxNum + 1);
  }

  function cleanAndSanitizeGroups(groupsArray, namesObj, minFilmCount, type) {
    if (!Array.isArray(groupsArray)) return { groups: [], names: {} };
    const safeNames = (typeof namesObj === "object" && namesObj !== null) ? namesObj : {};
    const cleanedGroups = [];
    const cleanedNames = {};
    const usedKeys = new Set();

    groupsArray.forEach(rawGroup => {
      if (!Array.isArray(rawGroup) || rawGroup.length === 0) return;

      let key = String(rawGroup[0]);
      let rawMembers = rawGroup.slice(1).map(String);

      if (/^\d+$/.test(key)) {
        rawMembers = rawGroup.map(String);
        key = generateUniqueGroupKey(type);
      }

      while (usedKeys.has(key)) {
        key = key + "_dup";
      }
      usedKeys.add(key);

      const uniqueMembers = Array.from(new Set(rawMembers)).filter(id => id !== key);

      if (uniqueMembers.length >= minFilmCount) {
        cleanedGroups.push([key, ...uniqueMembers]);
        if (safeNames[key]) {
          cleanedNames[key] = safeNames[key];
        }
      }
    });

    return { groups: cleanedGroups, names: cleanedNames };
  }

  try {
    const r1 = localStorage.getItem("watchlist_ids");
    if (r1) watchlist1State = JSON.parse(r1);

    const r2 = localStorage.getItem("watchlist_ids2");
    if (r2) watchlist2State = JSON.parse(r2);

    const r3 = localStorage.getItem("watchlist_ids3");
    if (r3) watchlist3State = JSON.parse(r3);

    const rWatched = localStorage.getItem("watched_ids");
    if (rWatched) watchedState = JSON.parse(rWatched);

    const rGlorious = localStorage.getItem("glorious_movie_ids");
    if (rGlorious) gloriousState = JSON.parse(rGlorious);

    const rScore = localStorage.getItem("myscore_ids");
    if (rScore) myScoreState = JSON.parse(rScore);

    const rHidden = localStorage.getItem("hidden_movie_ids");
    if (rHidden) hiddenMoviesState = JSON.parse(rHidden);

    const rRecent = localStorage.getItem("recent_clicked_movies");
    if (rRecent) {
      const parsedRecent = JSON.parse(rRecent);
      if (Array.isArray(parsedRecent)) {
        recentMoviesState = parsedRecent.slice(0, 30);
      }
    }

    const rGroups = localStorage.getItem("series_movies_groups");
    const rGroupNames = localStorage.getItem("series_groups_names");
    if (rGroups) {
      const parsedG = JSON.parse(rGroups);
      const parsedN = rGroupNames ? JSON.parse(rGroupNames) : {};
      const res = cleanAndSanitizeGroups(parsedG, parsedN, 1, "series");
      seriesMoviesGroupsState = res.groups;
      seriesGroupsNamesState = res.names;
    }

    const rRemakeGroups = localStorage.getItem("remake_movies_groups");
    const rRemakeNames = localStorage.getItem("remake_groups_names");
    if (rRemakeGroups) {
      const parsedG = JSON.parse(rRemakeGroups);
      const parsedN = rRemakeNames ? JSON.parse(rRemakeNames) : {};
      const res = cleanAndSanitizeGroups(parsedG, parsedN, 1, "remake");
      remakeMoviesGroupsState = res.groups;
      remakeGroupsNamesState = res.names;
    }

    const rGenreGroups = localStorage.getItem("genre_movies_groups");
    const rGenreNames = localStorage.getItem("genre_groups_names");
    if (rGenreGroups) {
      const parsedG = JSON.parse(rGenreGroups);
      const parsedN = rGenreNames ? JSON.parse(rGenreNames) : {};
      const res = cleanAndSanitizeGroups(parsedG, parsedN, 1, "genre");
      genreMoviesGroupsState = res.groups;
      genreGroupsNamesState = res.names;
    }

    const rAltUrls = localStorage.getItem("alternative_urls_map");
    if (rAltUrls) {
      const parsedAlt = JSON.parse(rAltUrls);
      if (typeof parsedAlt === "object" && parsedAlt !== null) {
        alternativeUrlsState = parsedAlt;
      }
    }
  } catch (e) {
    watchlist1State = {};
    watchlist2State = {};
    watchlist3State = {};
    watchedState = {};
    gloriousState = {};
    myScoreState = {};
    hiddenMoviesState = {};
    recentMoviesState = [];
    seriesMoviesGroupsState = [];
    seriesGroupsNamesState = {};
    remakeMoviesGroupsState = [];
    remakeGroupsNamesState = {};
    genreMoviesGroupsState = [];
    genreGroupsNamesState = {};
    alternativeUrlsState = {};
  }

  function openUrlPopup(movieId) {
    currentPopupMovieId = String(movieId);
    document.getElementById("popupMovieId").innerText = currentPopupMovieId;
    const movie = allMovies.find(m => String(m.film_ID) === currentPopupMovieId);
    if (!movie) return;
    const mainUrl = movie.web_scraper_start_url || movie.url || "";
    const altList = alternativeUrlsState[currentPopupMovieId] || [];
    let lines = [mainUrl, ...altList];
    document.getElementById("urlPopupTextarea").value = lines.join("\n");
    document.getElementById("urlPopupModal").style.display = "flex";
  }

  function closeUrlPopup() {
    document.getElementById("urlPopupModal").style.display = "none";
    currentPopupMovieId = null;
  }

  function saveUrlPopup() {
    if (!currentPopupMovieId) return;
    const text = document.getElementById("urlPopupTextarea").value;
    const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
    if (lines.length > 0) {
      const mainUrl = lines[0];
      const altUrls = lines.slice(1);

      const movie = allMovies.find(m => String(m.film_ID) === currentPopupMovieId);
      if (movie) {
        movie.web_scraper_start_url = mainUrl;
      }
      if (altUrls.length > 0) {
        alternativeUrlsState[currentPopupMovieId] = altUrls;
      } else {
        delete alternativeUrlsState[currentPopupMovieId];
      }
      try {
        localStorage.setItem("alternative_urls_map", JSON.stringify(alternativeUrlsState));
      } catch(e) {}
    }
    closeUrlPopup();
    renderMoviesPreservingScroll();
  }

  function saveSeriesGroups() {
    try {
      const res = cleanAndSanitizeGroups(seriesMoviesGroupsState, seriesGroupsNamesState, 1, "series");
      seriesMoviesGroupsState = res.groups;
      seriesGroupsNamesState = res.names;
      localStorage.setItem("series_movies_groups", JSON.stringify(seriesMoviesGroupsState));
      localStorage.setItem("series_groups_names", JSON.stringify(seriesGroupsNamesState));
    } catch (e) {}
  }

  function saveRemakeGroups() {
    try {
      const res = cleanAndSanitizeGroups(remakeMoviesGroupsState, remakeGroupsNamesState, 1, "remake");
      remakeMoviesGroupsState = res.groups;
      remakeGroupsNamesState = res.names;
      localStorage.setItem("remake_movies_groups", JSON.stringify(remakeMoviesGroupsState));
      localStorage.setItem("remake_groups_names", JSON.stringify(remakeGroupsNamesState));
    } catch (e) {}
  }

  function saveGenreGroups() {
    try {
      const res = cleanAndSanitizeGroups(genreMoviesGroupsState, genreGroupsNamesState, 1, "genre");
      genreMoviesGroupsState = res.groups;
      genreGroupsNamesState = res.names;
      localStorage.setItem("genre_movies_groups", JSON.stringify(genreMoviesGroupsState));
      localStorage.setItem("genre_groups_names", JSON.stringify(genreGroupsNamesState));
    } catch (e) {}
  }

  function getSeriesGroupForMovie(movieId) {
    const fid = String(movieId);
    return seriesMoviesGroupsState.find(g => g.slice(1).includes(fid)) || null;
  }

  function getRemakeGroupForMovie(movieId) {
    const fid = String(movieId);
    return remakeMoviesGroupsState.find(g => g.slice(1).includes(fid)) || null;
  }

  function getGenreGroupsForMovie(movieId) {
    const fid = String(movieId);
    return genreMoviesGroupsState.filter(g => g.slice(1).includes(fid));
  }

  function getSeriesGroupName(groupArray) {
    if (!groupArray || groupArray.length === 0) return "";
    const key = groupArray[0];
    if (seriesGroupsNamesState[key]) return seriesGroupsNamesState[key];
    return `Seri Grup (${groupArray.slice(1).join(", ")})`;
  }

  function getRemakeGroupName(groupArray) {
    if (!groupArray || groupArray.length === 0) return "";
    const key = groupArray[0];
    if (remakeGroupsNamesState[key]) return remakeGroupsNamesState[key];
    return `Remake Grup (${groupArray.slice(1).join(", ")})`;
  }

  function getGenreGroupName(groupArray) {
    if (!groupArray || groupArray.length === 0) return "";
    const key = groupArray[0];
    if (genreGroupsNamesState[key]) return genreGroupsNamesState[key];
    return `Tür Grup (${groupArray.slice(1).join(", ")})`;
  }

  function findCommonSubstring(str1, str2) {
    if (!str1 || !str2) return "";
    let s1 = str1.toLowerCase();
    let s2 = str2.toLowerCase();
    let maxSub = "";
    for (let i = 0; i < s1.length; i++) {
      for (let j = i + 3; j <= s1.length; j++) {
        let sub = s1.substring(i, j).trim();
        if (sub.length > 2 && s2.includes(sub)) {
          if (sub.length > maxSub.length) {
            maxSub = sub;
          }
        }
      }
    }
    if (maxSub.length > 2) {
      return maxSub.charAt(0).toUpperCase() + maxSub.slice(1);
    }
    return "";
  }

  function getTransitiveRelatedMovieIds(startMovieId) {
    const startId = String(startMovieId);
    const visited = new Set([startId]);
    const queue = [startId];
    const allRelationGroups = [...seriesMoviesGroupsState, ...remakeMoviesGroupsState];

    while (queue.length > 0) {
      const currentId = queue.shift();
      for (const group of allRelationGroups) {
        if (!Array.isArray(group) || group.length < 2) continue;
        const members = group.slice(1).map(String);
        if (members.includes(currentId)) {
          for (const mId of members) {
            if (!visited.has(mId)) {
              visited.add(mId);
              queue.push(mId);
            }
          }
        }
      }
    }
    return Array.from(visited);
  }

  function propagateGenreToRelatedMovies(movieId, targetGenreKey, shouldSave = true) {
    if (!targetGenreKey) return;
    const genreGroup = genreMoviesGroupsState.find(g => g[0] === targetGenreKey);
    if (!genreGroup) return;

    const relatedIds = getTransitiveRelatedMovieIds(movieId);
    let addedAny = false;

    relatedIds.forEach(relId => {
      if (!genreGroup.slice(1).includes(relId)) {
        genreGroup.push(relId);
        addedAny = true;
      }
    });

    if (addedAny && shouldSave) {
      saveGenreGroups();
    }
  }

  function syncGenresAcrossRelatedCluster(seedMovieId, shouldSave = true) {
    const clusterIds = getTransitiveRelatedMovieIds(seedMovieId);
    if (clusterIds.length <= 1) return false;

    let changed = false;
    genreMoviesGroupsState.forEach(g => {
      if (!Array.isArray(g) || g.length < 2) return;
      const members = g.slice(1).map(String);
      const hasAnyFromCluster = clusterIds.some(cid => members.includes(cid));
      if (hasAnyFromCluster) {
        clusterIds.forEach(cid => {
          if (!g.slice(1).includes(cid)) {
            g.push(cid);
            changed = true;
          }
        });
      }
    });

    if (changed && shouldSave) {
      saveGenreGroups();
    }
    return changed;
  }

  function syncAllConnectedGenres() {
    const processed = new Set();
    let anyChanged = false;
    const allRelationGroups = [...seriesMoviesGroupsState, ...remakeMoviesGroupsState];

    allRelationGroups.forEach(group => {
      if (!Array.isArray(group) || group.length < 2) return;
      group.slice(1).forEach(rawId => {
        const fid = String(rawId);
        if (!processed.has(fid)) {
          const cluster = getTransitiveRelatedMovieIds(fid);
          cluster.forEach(cid => processed.add(cid));
          if (syncGenresAcrossRelatedCluster(fid, false)) {
            anyChanged = true;
          }
        }
      });
    });

    if (anyChanged) {
      saveGenreGroups();
    }
  }

  syncAllConnectedGenres();

  function linkMovies(sourceId, targetIdInput, type) {
    const src = String(sourceId).trim();
    const rawTargets = String(targetIdInput).split(',').map(s => s.trim()).filter(Boolean);
    if (rawTargets.length === 0) return;

    let currentMembers = [];
    if (type === 'series') {
      const g = getSeriesGroupForMovie(src);
      currentMembers = g ? g.slice(1) : [];
    } else if (type === 'remake') {
      const g = getRemakeGroupForMovie(src);
      currentMembers = g ? g.slice(1) : [];
    } else {
      const gs = getGenreGroupsForMovie(src);
      gs.forEach(g => currentMembers.push(...g.slice(1)));
    }

    const newTargets = rawTargets.filter(t => t !== src && !currentMembers.includes(t));
    const tgt = newTargets.length > 0 ? newTargets[0] : rawTargets[0];

    if (!tgt || isNaN(tgt)) return;
    if (src === tgt) {
      alert("Bir filmi kendisine bağlayamazsınız.");
      return;
    }
    if (!validMovieIds.has(tgt)) {
      alert(`ID: ${tgt} arşivde bulunamadı!`);
      return;
    }

    if (type === 'genre') {
      const tgtGroups = getGenreGroupsForMovie(tgt);
      const batchMovieIds = getTargetMovieIdsForGenreAction(src);
      if (tgtGroups.length === 0) {
        pendingGroupSource = src;
        pendingGroupTarget = tgt;
        pendingGroupType = 'genre';

        const m1 = allMovies.find(m => String(m.film_ID) === src);
        const m2 = allMovies.find(m => String(m.film_ID) === tgt);
        let suggestedName = (m1 && m2) ? findCommonSubstring(m1.film_name, m2.film_name) : "";

        document.getElementById("groupNameModalTitle").innerText = "🏷️ Yeni Türler Grubu Adı Belirle";
        document.getElementById("groupNameInput").value = suggestedName;
        document.getElementById("groupNamePopupModal").style.display = "flex";
        setTimeout(() => document.getElementById("groupNameInput").focus(), 100);
      } else {
        const targetGroup = tgtGroups[0];
        batchMovieIds.forEach(mId => {
          if (!targetGroup.slice(1).includes(mId)) {
            targetGroup.push(mId);
          }
          propagateGenreToRelatedMovies(mId, targetGroup[0], false);
        });
        propagateGenreToRelatedMovies(tgt, targetGroup[0], false);
        saveGenreGroups();
        renderMoviesPreservingScroll();
      }
      return;
    }

    let groupsList = (type === 'series') ? seriesMoviesGroupsState : remakeMoviesGroupsState;
    const srcGroupIdx = groupsList.findIndex(g => g.slice(1).includes(src));
    const tgtGroupIdx = groupsList.findIndex(g => g.slice(1).includes(tgt));

    const isBrandNewGroupCreation = (srcGroupIdx === -1 && tgtGroupIdx === -1);

    if (isBrandNewGroupCreation) {
      pendingGroupSource = src;
      pendingGroupTarget = tgt;
      pendingGroupType = type;

      const m1 = allMovies.find(m => String(m.film_ID) === src);
      const m2 = allMovies.find(m => String(m.film_ID) === tgt);
      let suggestedName = (m1 && m2) ? findCommonSubstring(m1.film_name, m2.film_name) : "";

      const modalTitle = (type === 'series')
        ? "🎬 Yeni Seri Filmler Grubu Adı Belirle"
        : "🎥 Yeni Remake-Benzer Filmler Grubu Adı Belirle";

      document.getElementById("groupNameModalTitle").innerText = modalTitle;
      document.getElementById("groupNameInput").value = suggestedName;
      document.getElementById("groupNamePopupModal").style.display = "flex";
      setTimeout(() => document.getElementById("groupNameInput").focus(), 100);
    } else {
      executeLinkingWithoutPrompt(src, tgt, type);
    }
  }

  function executeLinkingWithoutPrompt(src, tgt, type, customName = null) {
    if (type === 'genre') {
      const newKey = generateUniqueGroupKey('genre');
      const batchMovieIds = getTargetMovieIdsForGenreAction(src);
      const initialMembers = Array.from(new Set([tgt, ...batchMovieIds]));
      const newGroup = [newKey, ...initialMembers];
      genreMoviesGroupsState.push(newGroup);
      if (customName) {
        genreGroupsNamesState[newKey] = customName;
      }
      initialMembers.forEach(mId => propagateGenreToRelatedMovies(mId, newKey, false));
      saveGenreGroups();
      renderMoviesPreservingScroll();
      return;
    }

    let groupsList = (type === 'series') ? seriesMoviesGroupsState : remakeMoviesGroupsState;
    let namesState = (type === 'series') ? seriesGroupsNamesState : remakeGroupsNamesState;

    const srcGroupIdx = groupsList.findIndex(g => g.slice(1).includes(src));
    const tgtGroupIdx = groupsList.findIndex(g => g.slice(1).includes(tgt));
    let affectedGroup = null;

    if (srcGroupIdx !== -1 && tgtGroupIdx !== -1) {
      if (srcGroupIdx !== tgtGroupIdx) {
        const keepKey = groupsList[srcGroupIdx][0];
        const dropKey = groupsList[tgtGroupIdx][0];
        const keptName = namesState[keepKey] || namesState[dropKey] || customName;

        const mergedMembers = Array.from(new Set([
          ...groupsList[srcGroupIdx].slice(1),
          ...groupsList[tgtGroupIdx].slice(1)
        ]));

        delete namesState[dropKey];
        const filteredGroups = groupsList.filter((_, idx) => idx !== srcGroupIdx && idx !== tgtGroupIdx);
        affectedGroup = [keepKey, ...mergedMembers];
        filteredGroups.push(affectedGroup);

        if (type === 'series') seriesMoviesGroupsState = filteredGroups;
        else remakeMoviesGroupsState = filteredGroups;

        if (keptName) namesState[keepKey] = keptName;
      } else {
        affectedGroup = groupsList[srcGroupIdx];
      }
    } else if (srcGroupIdx !== -1) {
      if (!groupsList[srcGroupIdx].slice(1).includes(tgt)) {
        groupsList[srcGroupIdx].push(tgt);
      }
      affectedGroup = groupsList[srcGroupIdx];
    } else if (tgtGroupIdx !== -1) {
      if (!groupsList[tgtGroupIdx].slice(1).includes(src)) {
        groupsList[tgtGroupIdx].push(src);
      }
      affectedGroup = groupsList[tgtGroupIdx];
    } else {
      const newKey = generateUniqueGroupKey(type);
      affectedGroup = [newKey, src, tgt];
      groupsList.push(affectedGroup);
      if (customName) {
        namesState[newKey] = customName;
      }
    }

    if (type === 'series') saveSeriesGroups();
    else saveRemakeGroups();

    syncGenresAcrossRelatedCluster(src, true);

    if (activeRelationFilterSet && activeRelationFilterSet.type === type && (activeRelationFilterSet.set.has(src) || activeRelationFilterSet.set.has(tgt))) {
      const updatedGroup = (type === 'series') ? getSeriesGroupForMovie(src) : getRemakeGroupForMovie(src);
      activeRelationFilterSet = updatedGroup ? { type: type, groupKey: updatedGroup[0], set: new Set(updatedGroup.slice(1)) } : null;
      updateRelationBanner();
    }

    renderMoviesPreservingScroll();
  }

  function closeGroupNamePopup(save) {
    const customName = document.getElementById("groupNameInput").value.trim();
    const src = pendingGroupSource;
    const tgt = pendingGroupTarget;
    const type = pendingGroupType;

    document.getElementById("groupNamePopupModal").style.display = "none";
    pendingGroupSource = null;
    pendingGroupTarget = null;
    pendingGroupType = null;

    if (!src || !tgt || !type) return;
    executeLinkingWithoutPrompt(src, tgt, type, save ? customName : null);
  }

  function openBulkAddMoviesToGenrePopup(genreKey) {
    const genreGroup = genreMoviesGroupsState.find(g => g[0] === genreKey);
    if (!genreGroup) return;

    targetGenreKeyForBulkAdd = genreKey;
    bulkSelectedMovieIds = new Set();

    const gName = getGenreGroupName(genreGroup);
    document.getElementById("bulkAddGenreModalTitle").innerText = `🏷️ "${gName}" Türüne Film Ekle`;
    document.getElementById("bulkSearchInput").value = "";
    document.getElementById("bulkMinYear").value = "";
    document.getElementById("bulkMaxYear").value = "";
    document.getElementById("bulkMinImdb").value = "";
    document.getElementById("bulkMaxImdb").value = "";
    document.getElementById("bulkSortSelect").value = "imdb_desc";
    document.getElementById("bulkShowHiddenCheckbox").checked = false;

    const bulkDomainSel = document.getElementById("bulkDomainFilter");
    const mainDomainSel = document.getElementById("domainFilter");
    if (bulkDomainSel && mainDomainSel) {
      bulkDomainSel.innerHTML = mainDomainSel.innerHTML;
      bulkDomainSel.value = "";
    }

    updateBulkSelectedCountBadge();
    renderBulkAddMoviesGrid();

    document.getElementById("bulkAddMoviesToGenreModal").style.display = "flex";
    setTimeout(() => document.getElementById("bulkSearchInput").focus(), 100);
  }

  function closeBulkAddMoviesToGenrePopup() {
    document.getElementById("bulkAddMoviesToGenreModal").style.display = "none";
    targetGenreKeyForBulkAdd = null;
    bulkSelectedMovieIds = new Set();
  }

  function updateBulkSelectedCountBadge() {
    const badge = document.getElementById("bulkAddSelectedCountBadge");
    if (badge) {
      badge.innerText = `Seçili: ${bulkSelectedMovieIds.size} Film`;
    }
  }

  function applyBulkSelectionCascade(movieId, shouldSelect) {
    const genreGroup = genreMoviesGroupsState.find(g => g[0] === targetGenreKeyForBulkAdd);
    const existingMemberSet = new Set(genreGroup ? genreGroup.slice(1).map(String) : []);
    const relatedIds = getTransitiveRelatedMovieIds(movieId);

    relatedIds.forEach(relId => {
      const idStr = String(relId);
      if (existingMemberSet.has(idStr)) return;

      if (shouldSelect) {
        bulkSelectedMovieIds.add(idStr);
      } else {
        bulkSelectedMovieIds.delete(idStr);
      }

      const cardEl = document.querySelector(`#bulkMoviesGrid .bulk-movie-item[data-bulk-movie-id="${idStr}"]`);
      if (cardEl) {
        const cbEl = cardEl.querySelector(".bulk-movie-cb");
        if (shouldSelect) {
          cardEl.classList.add("selected");
          if (cbEl) cbEl.checked = true;
        } else {
          cardEl.classList.remove("selected");
          if (cbEl) cbEl.checked = false;
        }
      }
    });

    updateBulkSelectedCountBadge();
  }

  function renderBulkAddMoviesGrid() {
    const gridEl = document.getElementById("bulkMoviesGrid");
    if (!gridEl || !targetGenreKeyForBulkAdd) return;

    const genreGroup = genreMoviesGroupsState.find(g => g[0] === targetGenreKeyForBulkAdd);
    const existingMemberSet = new Set(genreGroup ? genreGroup.slice(1).map(String) : []);
    const showHidden = document.getElementById("bulkShowHiddenCheckbox").checked;

    const searchVal = document.getElementById("bulkSearchInput").value.toLowerCase().trim();
    const searchTerms = searchVal ? searchVal.split("||").map(t => t.trim()).filter(Boolean) : [];
    const domainVal = document.getElementById("bulkDomainFilter").value;

    const minYearRaw = document.getElementById("bulkMinYear").value.trim();
    const maxYearRaw = document.getElementById("bulkMaxYear").value.trim();
    const minYear = minYearRaw !== "" ? parseInt(minYearRaw, 10) : null;
    const maxYear = maxYearRaw !== "" ? parseInt(maxYearRaw, 10) : null;

    const minImdbRaw = document.getElementById("bulkMinImdb").value.trim();
    const maxImdbRaw = document.getElementById("bulkMaxImdb").value.trim();
    const minImdb = minImdbRaw !== "" ? parseFloat(minImdbRaw) : null;
    const maxImdb = maxImdbRaw !== "" ? parseFloat(maxImdbRaw) : null;

    const sortVal = document.getElementById("bulkSortSelect").value;

    let filteredList = allMovies.filter(movie => {
      const fid = String(movie.film_ID);
      if (existingMemberSet.has(fid)) return false;

      if (hiddenMoviesState[fid] && !showHidden) return false;

      if (domainVal && getDomain(movie.web_scraper_start_url) !== domainVal) return false;

      if (minYear !== null && !isNaN(minYear)) {
        const y = parseInt(movie.year, 10);
        if (isNaN(y) || y < minYear) return false;
      }
      if (maxYear !== null && !isNaN(maxYear)) {
        const y = parseInt(movie.year, 10);
        if (isNaN(y) || y > maxYear) return false;
      }

      if (minImdb !== null && !isNaN(minImdb)) {
        const sc = parseFloat(movie.imdb_score);
        if (isNaN(sc) || sc < minImdb) return false;
      }
      if (maxImdb !== null && !isNaN(maxImdb)) {
        const sc = parseFloat(movie.imdb_score);
        if (isNaN(sc) || sc > maxImdb) return false;
      }

      if (searchTerms.length > 0) {
        const name = (movie.film_name || "").toLowerCase();
        const summary = (movie.movie_summary || "").toLowerCase();
        const actors = getActorsString(movie).toLowerCase();
        const idStr = fid.toLowerCase();
        const matched = searchTerms.some(term =>
          name.includes(term) || summary.includes(term) || actors.includes(term) || idStr === term
        );
        if (!matched) return false;
      }

      return true;
    });

    if (sortVal !== "default") {
      filteredList.sort((a, b) => compareByCriteria(a, b, sortVal));
    }

    const countLbl = document.getElementById("bulkFilteredCountLabel");
    if (countLbl) countLbl.innerText = `${filteredList.length} Film`;

    gridEl.innerHTML = "";
    if (filteredList.length === 0) {
      gridEl.innerHTML = `<div style="grid-column: 1 / -1; text-align:center; padding:30px; color:#888; font-style:italic;">Eklenecek uygun film bulunamadı.</div>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    filteredList.forEach(movie => {
      const fid = String(movie.film_ID);
      const isSelected = bulkSelectedMovieIds.has(fid);
      const isHidden = !!hiddenMoviesState[fid];

      const itemEl = document.createElement("div");
      itemEl.className = "bulk-movie-item" + (isSelected ? " selected" : "") + (isHidden ? " hidden-card" : "");
      itemEl.dataset.bulkMovieId = fid;

      const posterUrl = movie.poster || "";
      const imdbTxt = movie.imdb_score ? `⭐ ${movie.imdb_score}` : "⭐ -";
      const yearTxt = movie.year ? String(movie.year) : "-";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.className = "bulk-movie-cb";
      cb.checked = isSelected;

      cb.addEventListener("click", (e) => {
        e.stopPropagation();
        applyBulkSelectionCascade(fid, cb.checked);
      });

      itemEl.addEventListener("click", () => {
        const nextState = !bulkSelectedMovieIds.has(fid);
        applyBulkSelectionCascade(fid, nextState);
      });

      itemEl.innerHTML = `
        <img class="bulk-movie-poster" src="${escapeHtml(posterUrl)}" alt="${escapeHtml(movie.film_name)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/160x220?text=Afi%C5%9F+Yok';">
        <div class="bulk-movie-info">
          <div class="bulk-movie-title" title="${escapeHtml(movie.film_name)}">${escapeHtml(movie.film_name)}</div>
          <div class="bulk-movie-meta">
            <span>${imdbTxt}</span>
            <span>ID: ${fid}</span>
            <span>${yearTxt}</span>
          </div>
        </div>
      `;

      itemEl.prepend(cb);
      fragment.appendChild(itemEl);
    });

    gridEl.appendChild(fragment);
  }

  function confirmBulkAddMoviesToGenre() {
    if (!targetGenreKeyForBulkAdd) {
      closeBulkAddMoviesToGenrePopup();
      return;
    }

    const gKey = targetGenreKeyForBulkAdd;

    if (bulkSelectedMovieIds.size > 0) {
      bulkSelectedMovieIds.forEach(fid => {
        propagateGenreToRelatedMovies(fid, gKey, false);
      });
      saveGenreGroups();

      if (activeRelationFilterSet && activeRelationFilterSet.type === 'genre' && activeRelationFilterSet.groupKey === gKey) {
        const updatedGroup = genreMoviesGroupsState.find(g => g[0] === gKey);
        if (updatedGroup) {
          activeRelationFilterSet.set = new Set(updatedGroup.slice(1));
          updateRelationBanner();
        }
      }
    }

    closeBulkAddMoviesToGenrePopup();
    renderMoviesPreservingScroll();
  }

  function rebuildCachedGroupListForPopup(selectTargetKey = null) {
    const type = activeGroupSelectType;
    if (!type) return;

    let groupsList = null;
    if (type === 'series') groupsList = seriesMoviesGroupsState;
    else if (type === 'remake') groupsList = remakeMoviesGroupsState;
    else groupsList = genreMoviesGroupsState;

    const showHidden = document.getElementById("showHiddenCheckbox").checked;
    cachedGroupListForPopup = [];

    if (groupsList && Array.isArray(groupsList) && groupsList.length > 0) {
      groupsList.forEach((g, idx) => {
        if (!g || !Array.isArray(g) || g.length === 0) return;

        const gKey = g[0];
        const memberIds = g.slice(1);
        const visibleMembers = showHidden ? memberIds : memberIds.filter(id => !hiddenMoviesState[id]);
        const isNewlyCreatedInThisPopup = tempCreatedGroupKeysInPopup.includes(gKey);
        const minLimit = 1;

        if (!isNewlyCreatedInThisPopup && visibleMembers.length < minLimit) return;

        let gName = "";
        if (type === 'series') gName = getSeriesGroupName(g);
        else if (type === 'remake') gName = getRemakeGroupName(g);
        else gName = getGenreGroupName(g);

        cachedGroupListForPopup.push({
          index: idx,
          originalIndex: idx,
          groupKey: gKey,
          name: gName,
          rawName: gName,
          count: visibleMembers.length,
          members: memberIds
        });
      });
    }

    filterAndSortGroupSelectDropdown(selectTargetKey);
  }

  function openGroupSelectPopup(movieId, type) {
    activeMovieIdForGroupSelect = String(movieId);
    activeGroupSelectType = type;
    tempCreatedGroupKeysInPopup = [];
    selectedGenreKeysInPopup = new Set();
    focusedGenreKeyInPopup = null;
    selectedSingleGroupIndexInPopup = null;

    const searchInputEl = document.getElementById("groupSearchInput");
    if (searchInputEl) searchInputEl.value = "";

    const newGroupInputEl = document.getElementById("newGroupInPopupInput");
    if (newGroupInputEl) newGroupInputEl.value = "";

    const renameInputEl = document.getElementById("renameGroupInPopupInput");
    if (renameInputEl) renameInputEl.value = "";

    const singleGridEl = document.getElementById("groupSelectDropdown");
    const checkboxListEl = document.getElementById("groupSelectCheckboxList");

    if (type === 'genre') {
      if (singleGridEl) singleGridEl.style.display = "none";
      if (checkboxListEl) checkboxListEl.style.display = "grid";

      const existingGenres = getGenreGroupsForMovie(activeMovieIdForGroupSelect);
      existingGenres.forEach(g => selectedGenreKeysInPopup.add(g[0]));
      if (existingGenres.length > 0) {
        focusedGenreKeyInPopup = existingGenres[0][0];
      }
    } else {
      if (singleGridEl) singleGridEl.style.display = "grid";
      if (checkboxListEl) checkboxListEl.style.display = "none";
    }

    const createBtnEl = document.getElementById("createNewGroupInPopupBtn");
    if (createBtnEl) {
      if (type === 'series') {
        createBtnEl.innerText = "Yeni Seri Ekle";
        createBtnEl.style.background = "#2563eb";
      } else if (type === 'remake') {
        createBtnEl.innerText = "Yeni Remake Ekle";
        createBtnEl.style.background = "#7c3aed";
      } else {
        createBtnEl.innerText = "Yeni Tür Ekle";
        createBtnEl.style.background = "#059669";
      }
    }

    const sortSelEl = document.getElementById("groupPopupSortSelect");
    if (sortSelEl) sortSelEl.value = (type === 'genre') ? "alpha_asc" : "default";

    rebuildCachedGroupListForPopup(focusedGenreKeyInPopup);

    const popupModal = document.getElementById("groupSelectPopupModal");
    if (popupModal) {
      popupModal.style.display = "flex";
    }
    setTimeout(() => {
      if (searchInputEl) searchInputEl.focus();
    }, 100);
  }

  function createNewGroupFromPopup() {
    const type = activeGroupSelectType;
    if (!type) return;

    const inputEl = document.getElementById("newGroupInPopupInput");
    const newName = inputEl ? inputEl.value.trim() : "";
    if (!newName) {
      alert("Lütfen yeni grup için bir ad yazın.");
      if (inputEl) inputEl.focus();
      return;
    }

    let groupsList = null;
    let namesObj = null;
    if (type === 'series') {
      groupsList = seriesMoviesGroupsState;
      namesObj = seriesGroupsNamesState;
    } else if (type === 'remake') {
      groupsList = remakeMoviesGroupsState;
      namesObj = remakeGroupsNamesState;
    } else {
      groupsList = genreMoviesGroupsState;
      namesObj = genreGroupsNamesState;
    }

    const existingEntry = groupsList.find(g => {
      const k = g[0];
      return (namesObj[k] || "").trim().toLowerCase() === newName.toLowerCase();
    });

    if (existingEntry) {
      const exKey = existingEntry[0];
      if (type === 'genre') {
        selectedGenreKeysInPopup.add(exKey);
        focusedGenreKeyInPopup = exKey;
      }
      if (inputEl) inputEl.value = "";
      const searchEl = document.getElementById("groupSearchInput");
      if (searchEl) searchEl.value = "";
      rebuildCachedGroupListForPopup(exKey);
      return;
    }

    const newKey = generateUniqueGroupKey(type);
    groupsList.push([newKey]);
    namesObj[newKey] = newName;
    tempCreatedGroupKeysInPopup.push(newKey);

    if (type === 'genre') {
      selectedGenreKeysInPopup.add(newKey);
      focusedGenreKeyInPopup = newKey;
    }

    if (inputEl) inputEl.value = "";
    const searchEl = document.getElementById("groupSearchInput");
    if (searchEl) searchEl.value = "";

    rebuildCachedGroupListForPopup(newKey);
  }

  function renameSelectedGroupInPopup() {
    const type = activeGroupSelectType;
    if (!type) return;

    const renameInputEl = document.getElementById("renameGroupInPopupInput");
    if (!renameInputEl) return;

    const newName = renameInputEl.value.trim();
    if (!newName) {
      alert("Grup adı boş olamaz.");
      renameInputEl.focus();
      return;
    }

    let targetKey = null;
    let namesObj = null;

    if (type === 'genre') {
      targetKey = focusedGenreKeyInPopup;
      namesObj = genreGroupsNamesState;
      if (!targetKey) {
        alert("Lütfen önce soldaki listeden adı değiştirilecek bir tür satırına tıklayın.");
        return;
      }
    } else {
      if (selectedSingleGroupIndexInPopup === null || isNaN(selectedSingleGroupIndexInPopup)) {
        alert("Lütfen önce soldaki listeden adı değiştirilecek bir grup seçin.");
        return;
      }
      const groupIdx = parseInt(selectedSingleGroupIndexInPopup, 10);
      const groupsList = (type === 'series') ? seriesMoviesGroupsState : remakeMoviesGroupsState;
      namesObj = (type === 'series') ? seriesGroupsNamesState : remakeGroupsNamesState;
      const group = groupsList[groupIdx];
      if (!group || group.length === 0) return;
      targetKey = group[0];
    }

    namesObj[targetKey] = newName;

    if (type === 'series') saveSeriesGroups();
    else if (type === 'remake') saveRemakeGroups();
    else saveGenreGroups();

    rebuildCachedGroupListForPopup(targetKey);
    updateRelationBanner();
    renderMoviesPreservingScroll();
  }

  function setFocusedGenreRow(groupKey) {
    focusedGenreKeyInPopup = groupKey;
    const matchedItem = cachedGroupListForPopup.find(item => item.groupKey === groupKey);
    updateGroupPreview(matchedItem ? matchedItem.members : null);

    const renameInputEl = document.getElementById("renameGroupInPopupInput");
    if (renameInputEl) {
      renameInputEl.value = matchedItem ? matchedItem.rawName : "";
    }

    const checkboxListEl = document.getElementById("groupSelectCheckboxList");
    if (checkboxListEl) {
      checkboxListEl.querySelectorAll(".multi-checkbox-item").forEach(row => {
        if (row.dataset.groupKey === groupKey) {
          row.classList.add("active-row");
        } else {
          row.classList.remove("active-row");
        }
      });
    }
  }

  function setFocusedSingleGroupRow(groupIndex) {
    selectedSingleGroupIndexInPopup = groupIndex;
    const matchedItem = cachedGroupListForPopup.find(item => item.index === groupIndex);
    updateGroupPreview(matchedItem ? matchedItem.members : null);

    const renameInputEl = document.getElementById("renameGroupInPopupInput");
    if (renameInputEl) {
      renameInputEl.value = matchedItem ? matchedItem.rawName : "";
    }

    const singleGridEl = document.getElementById("groupSelectDropdown");
    if (singleGridEl) {
      singleGridEl.querySelectorAll(".single-grid-item").forEach(row => {
        if (parseInt(row.dataset.groupIndex, 10) === groupIndex) {
          row.classList.add("active-row");
        } else {
          row.classList.remove("active-row");
        }
      });
    }
  }

  function filterAndSortGroupSelectDropdown(selectTargetKey = null) {
    const queryEl = document.getElementById("groupSearchInput");
    const sortValEl = document.getElementById("groupPopupSortSelect");
    const query = queryEl ? queryEl.value.toLowerCase().trim() : "";
    const sortVal = sortValEl ? sortValEl.value : "default";

    let list = [...cachedGroupListForPopup];

    if (query) {
      list = list.filter(item => item.name.toLowerCase().includes(query));
    }

    list.sort((a, b) => {
      if (sortVal === "alpha_asc") {
        return a.rawName.localeCompare(b.rawName);
      } else if (sortVal === "alpha_desc") {
        return b.rawName.localeCompare(a.rawName);
      } else if (sortVal === "default") {
        return a.originalIndex - b.originalIndex;
      } else if (sortVal === "count_asc") {
        if (a.count !== b.count) return a.count - b.count;
        return a.rawName.localeCompare(b.rawName);
      } else if (sortVal === "count_desc") {
        if (a.count !== b.count) return b.count - a.count;
        return b.rawName.localeCompare(a.rawName);
      }
      return 0;
    });

    if (activeGroupSelectType === 'genre') {
      const checkboxListEl = document.getElementById("groupSelectCheckboxList");
      if (!checkboxListEl) return;
      checkboxListEl.innerHTML = "";

      if (list.length === 0) {
        checkboxListEl.innerHTML = `<div style="color:#888; padding:12px; font-style:italic;">Eşleşen tür bulunamadı</div>`;
        updateGroupPreview(null);
        const renameInputEl = document.getElementById("renameGroupInPopupInput");
        if (renameInputEl) renameInputEl.value = "";
        return;
      }

      if (selectTargetKey && list.some(i => i.groupKey === selectTargetKey)) {
        focusedGenreKeyInPopup = selectTargetKey;
      } else if (!focusedGenreKeyInPopup || !list.some(i => i.groupKey === focusedGenreKeyInPopup)) {
        focusedGenreKeyInPopup = list[0].groupKey;
      }

      list.forEach(item => {
        const isCheckedInitially = selectedGenreKeysInPopup.has(item.groupKey);
        const row = document.createElement("div");
        row.className = "multi-checkbox-item"
          + (isCheckedInitially ? " checked-row" : "")
          + (item.groupKey === focusedGenreKeyInPopup ? " active-row" : "");
        row.dataset.groupKey = item.groupKey;

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = isCheckedInitially;
        cb.addEventListener("change", (e) => {
          e.stopPropagation();
          if (cb.checked) {
            selectedGenreKeysInPopup.add(item.groupKey);
            row.classList.add("checked-row");
          } else {
            selectedGenreKeysInPopup.delete(item.groupKey);
            row.classList.remove("checked-row");
          }
          setFocusedGenreRow(item.groupKey);
        });

        const lbl = document.createElement("span");
        lbl.className = "multi-checkbox-label";
        lbl.textContent = item.name;
        lbl.title = item.name;

        row.appendChild(cb);
        row.appendChild(lbl);

        row.addEventListener("click", (e) => {
          if (e.target !== cb) {
            cb.checked = !cb.checked;
            if (cb.checked) {
              selectedGenreKeysInPopup.add(item.groupKey);
              row.classList.add("checked-row");
            } else {
              selectedGenreKeysInPopup.delete(item.groupKey);
              row.classList.remove("checked-row");
            }
          }
          setFocusedGenreRow(item.groupKey);
        });

        checkboxListEl.appendChild(row);
      });

      setFocusedGenreRow(focusedGenreKeyInPopup);
      return;
    }

    const singleGridEl = document.getElementById("groupSelectDropdown");
    if (!singleGridEl) return;
    singleGridEl.innerHTML = "";

    if (list.length === 0) {
      singleGridEl.innerHTML = `<div style="color:#888; padding:12px; font-style:italic;">Eşleşen grup bulunamadı</div>`;
      selectedSingleGroupIndexInPopup = null;
      updateGroupPreview(null);
      const renameInputEl = document.getElementById("renameGroupInPopupInput");
      if (renameInputEl) renameInputEl.value = "";
    } else {
      let targetItem = list[0];
      if (selectTargetKey) {
        const found = list.find(i => i.groupKey === selectTargetKey);
        if (found) targetItem = found;
      } else if (selectedSingleGroupIndexInPopup !== null) {
        const found = list.find(i => i.index === selectedSingleGroupIndexInPopup);
        if (found) targetItem = found;
      }

      list.forEach(item => {
        const cell = document.createElement("div");
        cell.className = "single-grid-item" + (item.index === targetItem.index ? " active-row" : "");
        cell.dataset.groupIndex = item.index;
        cell.title = item.name;

        const lbl = document.createElement("span");
        lbl.className = "multi-checkbox-label";
        lbl.textContent = item.name;

        cell.appendChild(lbl);
        cell.addEventListener("click", () => {
          setFocusedSingleGroupRow(item.index);
        });

        singleGridEl.appendChild(cell);
      });

      setFocusedSingleGroupRow(targetItem.index);
    }
  }

  function updateGroupPreview(memberIds) {
    const previewListEl = document.getElementById("groupPreviewList");
    const countEl = document.getElementById("previewGroupCount");
    if (!previewListEl || !countEl) return;

    const showHidden = document.getElementById("showHiddenCheckbox").checked;
    const visibleMemberIds = memberIds ? (showHidden ? memberIds : memberIds.filter(id => !hiddenMoviesState[id])) : [];

    if (visibleMemberIds.length === 0) {
      countEl.innerText = "0";
      previewListEl.innerHTML = `<span style="color: #666; font-style: italic; padding: 10px; text-align: center;">Bu grupta henüz film yok</span>`;
      return;
    }

    countEl.innerText = visibleMemberIds.length;
    let htmlContent = "";

    visibleMemberIds.forEach(mId => {
      const movieObj = allMovies.find(m => String(m.film_ID) === String(mId));
      const mName = movieObj ? movieObj.film_name : `Film #${mId}`;
      const mYear = movieObj && movieObj.year ? `(${movieObj.year})` : "";
      const mImdb = movieObj && movieObj.imdb_score ? `⭐ ${movieObj.imdb_score}` : "";

      htmlContent += `
        <div style="background: #1e1e1e; border: 1px solid #333; padding: 5px 9px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
          <span style="color: #fff; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px;" title="${escapeHtml(mName)}">${escapeHtml(mName)} ${mYear}</span>
          <span style="color: #f5c518; font-size: 10px; flex-shrink: 0;">${mImdb}</span>
        </div>
      `;
    });

    previewListEl.innerHTML = htmlContent;
  }

  function cleanupUnusedTempGroupsInPopup() {
    if (!tempCreatedGroupKeysInPopup || tempCreatedGroupKeysInPopup.length === 0) return;

    tempCreatedGroupKeysInPopup.forEach(tKey => {
      if (tKey.startsWith("s_")) {
        const idx = seriesMoviesGroupsState.findIndex(g => g[0] === tKey);
        if (idx !== -1 && seriesMoviesGroupsState[idx].slice(1).length < 1) {
          seriesMoviesGroupsState.splice(idx, 1);
          delete seriesGroupsNamesState[tKey];
        }
      } else if (tKey.startsWith("r_")) {
        const idx = remakeMoviesGroupsState.findIndex(g => g[0] === tKey);
        if (idx !== -1 && remakeMoviesGroupsState[idx].slice(1).length < 1) {
          remakeMoviesGroupsState.splice(idx, 1);
          delete remakeGroupsNamesState[tKey];
        }
      } else if (tKey.startsWith("g_")) {
        const idx = genreMoviesGroupsState.findIndex(g => g[0] === tKey);
        if (idx !== -1 && genreMoviesGroupsState[idx].slice(1).length < 1) {
          genreMoviesGroupsState.splice(idx, 1);
          delete genreGroupsNamesState[tKey];
        }
      }
    });

    tempCreatedGroupKeysInPopup = [];
  }

  function closeGroupSelectPopup() {
    cleanupUnusedTempGroupsInPopup();
    const popupModal = document.getElementById("groupSelectPopupModal");
    if (popupModal) {
      popupModal.style.display = "none";
    }
    activeMovieIdForGroupSelect = null;
    activeGroupSelectType = null;
    cachedGroupListForPopup = [];
    selectedGenreKeysInPopup = new Set();
    focusedGenreKeyInPopup = null;
    selectedSingleGroupIndexInPopup = null;
  }

  function confirmGroupSelect() {
    if (!activeMovieIdForGroupSelect || !activeGroupSelectType) {
      closeGroupSelectPopup();
      return;
    }

    const movieIdToAdd = activeMovieIdForGroupSelect;
    const type = activeGroupSelectType;

    if (type === 'genre') {
      const batchMovieIds = getTargetMovieIdsForGenreAction(movieIdToAdd);
      const isMultiMode = !!(document.getElementById("multiSelectCheckbox")?.checked);
      const currentAssignedKeys = new Set(getGenreGroupsForMovie(movieIdToAdd).map(g => g[0]));

      selectedGenreKeysInPopup.forEach(gKey => {
        if (isMultiMode || !currentAssignedKeys.has(gKey)) {
          batchMovieIds.forEach(mId => propagateGenreToRelatedMovies(mId, gKey, false));
        }
      });

      if (!isMultiMode) {
        currentAssignedKeys.forEach(oldKey => {
          if (!selectedGenreKeysInPopup.has(oldKey)) {
            unlinkMovie(movieIdToAdd, 'genre', oldKey, false);
          }
        });
      }

      closeGroupSelectPopup();
      saveGenreGroups();
      renderMoviesPreservingScroll();
      return;
    }

    if (selectedSingleGroupIndexInPopup === null || isNaN(selectedSingleGroupIndexInPopup)) {
      closeGroupSelectPopup();
      return;
    }
    const idx = parseInt(selectedSingleGroupIndexInPopup, 10);

    const groupsList = (type === 'series') ? seriesMoviesGroupsState : remakeMoviesGroupsState;
    const group = groupsList[idx];
    if (!group || group.length === 0) {
      closeGroupSelectPopup();
      return;
    }

    const targetGroupKey = group[0];

    const existingGroup = (type === 'series') ? getSeriesGroupForMovie(movieIdToAdd) : getRemakeGroupForMovie(movieIdToAdd);
    if (existingGroup && existingGroup[0] !== targetGroupKey) {
      unlinkMovie(movieIdToAdd, type, existingGroup[0], false);
    }

    if (!group.slice(1).includes(movieIdToAdd)) {
      group.push(movieIdToAdd);
    }

    closeGroupSelectPopup();

    if (type === 'series') saveSeriesGroups();
    else saveRemakeGroups();

    syncGenresAcrossRelatedCluster(movieIdToAdd, true);
    renderMoviesPreservingScroll();
  }

  function unlinkMovie(movieId, type, specificGroupKey = null, shouldRender = true) {
    const fid = String(movieId);
    let groupsList = null;
    let namesState = null;

    if (type === 'series') {
      groupsList = seriesMoviesGroupsState;
      namesState = seriesGroupsNamesState;
    } else if (type === 'remake') {
      groupsList = remakeMoviesGroupsState;
      namesState = remakeGroupsNamesState;
    } else {
      groupsList = genreMoviesGroupsState;
      namesState = genreGroupsNamesState;
    }

    const idx = specificGroupKey
      ? groupsList.findIndex(g => g[0] === specificGroupKey && g.slice(1).includes(fid))
      : groupsList.findIndex(g => g.slice(1).includes(fid));

    if (idx === -1) return;

    const group = groupsList[idx];
    const groupKey = group[0];

    const idsToRemove = new Set();
    if (type === 'genre') {
      const targetSeeds = getTargetMovieIdsForGenreAction(fid);
      targetSeeds.forEach(seedId => {
        getTransitiveRelatedMovieIds(seedId).forEach(relId => idsToRemove.add(String(relId)));
      });
    } else {
      idsToRemove.add(fid);
    }

    const filteredMembers = group.slice(1).filter(id => !idsToRemove.has(String(id)));
    groupsList[idx] = [groupKey, ...filteredMembers];

    const minFilmLimit = 1;
    const remainingFilmCount = filteredMembers.length;

    if (remainingFilmCount < minFilmLimit) {
      delete namesState[groupKey];
      groupsList.splice(idx, 1);
    }

    if (type === 'series') saveSeriesGroups();
    else if (type === 'remake') saveRemakeGroups();
    else saveGenreGroups();

    if (activeRelationFilterSet && activeRelationFilterSet.type === type && activeRelationFilterSet.groupKey === groupKey) {
      idsToRemove.forEach(remId => activeRelationFilterSet.set.delete(remId));
      if (activeRelationFilterSet.set.size < minFilmLimit) {
        activeRelationFilterSet = null;
      }
      updateRelationBanner();
    }

    if (shouldRender) {
      renderMoviesPreservingScroll();
    }
  }

  function filterByRelationGroup(movieId, type, specificGroupKey = null) {
    let group = null;
    if (type === 'series') {
      group = getSeriesGroupForMovie(movieId);
    } else if (type === 'remake') {
      group = getRemakeGroupForMovie(movieId);
    } else {
      const allGenres = getGenreGroupsForMovie(movieId);
      group = specificGroupKey
        ? allGenres.find(g => g[0] === specificGroupKey)
        : (allGenres.length > 0 ? allGenres[0] : null);
    }

    if (!group) return;
    const gKey = group[0];

    if (activeRelationFilterSet && activeRelationFilterSet.type === type && activeRelationFilterSet.groupKey === gKey) {
      clearRelationFilter();
      return;
    }

    currentPage = 1;
    activeRelationFilterSet = { type: type, groupKey: gKey, set: new Set(group.slice(1)) };
    updateRelationBanner();
    renderMovies(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function clearRelationFilter() {
    currentPage = 1;
    activeRelationFilterSet = null;
    updateRelationBanner();
    renderMovies(false);
  }

  function updateRelationBanner() {
    const banner = document.getElementById("relationBanner");
    const bannerText = document.getElementById("relationBannerText");
    if (activeRelationFilterSet && activeRelationFilterSet.set.size > 0) {
      const showHidden = document.getElementById("showHiddenCheckbox").checked;
      const visibleIds = Array.from(activeRelationFilterSet.set).filter(id => showHidden || !hiddenMoviesState[id]);
      const minLimit = 1;
      if (visibleIds.length < minLimit) {
        activeRelationFilterSet = null;
        banner.classList.remove("visible");
        return;
      }
      const type = activeRelationFilterSet.type;
      const gKey = activeRelationFilterSet.groupKey;
      let groupsList = null;
      if (type === 'series') groupsList = seriesMoviesGroupsState;
      else if (type === 'remake') groupsList = remakeMoviesGroupsState;
      else groupsList = genreMoviesGroupsState;

      const groupObj = groupsList.find(g => g[0] === gKey);

      let gName = "Grup";
      let prefixIcon = "🔗";
      if (type === 'series') {
        gName = groupObj ? getSeriesGroupName(groupObj) : "Seri Filmler";
        prefixIcon = "🎬";
      } else if (type === 'remake') {
        gName = groupObj ? getRemakeGroupName(groupObj) : "Remake Filmler";
        prefixIcon = "🎥";
      } else {
        gName = groupObj ? getGenreGroupName(groupObj) : "Türler";
        prefixIcon = "🏷️";
      }

      bannerText.innerText = `${prefixIcon} ${gName} (${visibleIds.length} Film)`;
      banner.classList.add("visible");
    } else {
      banner.classList.remove("visible");
    }
  }

  function selectMovieIdFromCardRadio(movieId) {
    const fid = String(movieId).trim();
    if (!fid) return;
    try {
      localStorage.setItem("last_clicked_movie_id", fid);
      document.getElementById("lastIdInput").value = fid;
      syncCardRadioSelection(fid);
      saveStateToStorage();
      addRecentMovie(fid);
    } catch (e) {}
    if (sidebarMode === "genre_add") {
      loadMovieGenresIntoSidebar();
    }
    scrollToMovie(fid, true);
  }

  function exportUserData() {
    try {
      const sRes = cleanAndSanitizeGroups(seriesMoviesGroupsState, seriesGroupsNamesState, 1, "series");
      seriesMoviesGroupsState = sRes.groups;
      seriesGroupsNamesState = sRes.names;

      const rRes = cleanAndSanitizeGroups(remakeMoviesGroupsState, remakeGroupsNamesState, 1, "remake");
      remakeMoviesGroupsState = rRes.groups;
      remakeGroupsNamesState = rRes.names;

      const gRes = cleanAndSanitizeGroups(genreMoviesGroupsState, genreGroupsNamesState, 1, "genre");
      genreMoviesGroupsState = gRes.groups;
      genreGroupsNamesState = gRes.names;

      const payload = {
        exported_at: new Date().toISOString(),
        watchlist_ids: watchlist1State,
        watchlist_ids2: watchlist2State,
        watchlist_ids3: watchlist3State,
        watched_ids: watchedState,
        glorious_movie_ids: gloriousState,
        myscore_ids: myScoreState,
        hidden_movie_ids: hiddenMoviesState,
        recent_clicked_movies: recentMoviesState,
        series_movies_groups: seriesMoviesGroupsState,
        series_groups_names: seriesGroupsNamesState,
        remake_movies_groups: remakeMoviesGroupsState,
        remake_groups_names: remakeGroupsNamesState,
        genre_movies_groups: genreMoviesGroupsState,
        genre_groups_names: genreGroupsNamesState,
        alternative_urls_map: alternativeUrlsState
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const dateStamp = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = `film_arsivim_yedek_${dateStamp}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Yedek oluşturulurken hata oluştu: " + e.message);
    }
  }

  function importUserData(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(evt) {
      try {
        const data = JSON.parse(evt.target.result);
        if (typeof data !== "object" || data === null) {
          throw new Error("Geçersiz yedek dosyası formatı.");
        }

        if (data.watchlist_ids) {
          watchlist1State = data.watchlist_ids;
          localStorage.setItem("watchlist_ids", JSON.stringify(watchlist1State));
        }
        if (data.watchlist_ids2) {
          watchlist2State = data.watchlist_ids2;
          localStorage.setItem("watchlist_ids2", JSON.stringify(watchlist2State));
        }
        if (data.watchlist_ids3) {
          watchlist3State = data.watchlist_ids3;
          localStorage.setItem("watchlist_ids3", JSON.stringify(watchlist3State));
        }
        if (data.watched_ids) {
          watchedState = data.watched_ids;
          localStorage.setItem("watched_ids", JSON.stringify(watchedState));
        }
        if (data.glorious_movie_ids) {
          gloriousState = data.glorious_movie_ids;
          localStorage.setItem("glorious_movie_ids", JSON.stringify(gloriousState));
        }
        if (data.myscore_ids) {
          myScoreState = data.myscore_ids;
          localStorage.setItem("myscore_ids", JSON.stringify(myScoreState));
        }
        if (data.hidden_movie_ids) {
          hiddenMoviesState = data.hidden_movie_ids;
          localStorage.setItem("hidden_movie_ids", JSON.stringify(hiddenMoviesState));
        }
        if (Array.isArray(data.recent_clicked_movies)) {
          recentMoviesState = data.recent_clicked_movies.slice(0, 30);
          localStorage.setItem("recent_clicked_movies", JSON.stringify(recentMoviesState));
          renderRecentDropdown();
        }
        if (Array.isArray(data.series_movies_groups)) {
          const res = cleanAndSanitizeGroups(data.series_movies_groups, data.series_groups_names || {}, 1, "series");
          seriesMoviesGroupsState = res.groups;
          seriesGroupsNamesState = res.names;
        }
        saveSeriesGroups();

        if (Array.isArray(data.remake_movies_groups)) {
          const res = cleanAndSanitizeGroups(data.remake_movies_groups, data.remake_groups_names || {}, 1, "remake");
          remakeMoviesGroupsState = res.groups;
          remakeGroupsNamesState = res.names;
        }
        saveRemakeGroups();

        if (Array.isArray(data.genre_movies_groups)) {
          const res = cleanAndSanitizeGroups(data.genre_movies_groups, data.genre_groups_names || {}, 1, "genre");
          genreMoviesGroupsState = res.groups;
          genreGroupsNamesState = res.names;
        }
        saveGenreGroups();

        syncAllConnectedGenres();

        if (data.alternative_urls_map) {
          alternativeUrlsState = data.alternative_urls_map;
          localStorage.setItem("alternative_urls_map", JSON.stringify(alternativeUrlsState));
        }

        sidebarSelectedGenreKeys.clear();
        currentPage = 1;
        activeRelationFilterSet = null;
        updateRelationBanner();
        renderMovies(false);
        if (sidebarMode === "genre_add") {
          loadMovieGenresIntoSidebar();
        }
        alert("Yedek verileri başarıyla içe aktarıldı!");
      } catch (err) {
        alert("Yedek dosyası okunamadı: " + err.message);
      }
    };
    reader.readAsText(file);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function getDomain(url) {
    if (!url) return "";
    try {
      let cleanUrl = url.toLowerCase().trim();
      if (!cleanUrl.includes("://")) cleanUrl = "http://" + cleanUrl;
      const parsed = new URL(cleanUrl);
      let hostname = parsed.hostname;
      if (hostname.startsWith("www.")) {
        hostname = hostname.substring(4);
      }
      return hostname;
    } catch (e) {
      return "";
    }
  }

  function initFilters() {
    try {
      const domains = new Set();
      const years = new Set();
      const countries = new Set();
      const durations = new Set();

      allMovies.forEach(m => {
        const d = getDomain(m.web_scraper_start_url);
        if (d) domains.add(d);
        if (m.year) {
          const yNum = parseInt(m.year, 10);
          if (!isNaN(yNum)) years.add(yNum);
        }
        if (m.duration_mins) {
          const dNum = parseInt(m.duration_mins, 10);
          if (!isNaN(dNum)) durations.add(dNum);
        }
        if (m.country) {
          m.country.split(',').forEach(c => countries.add(c.trim()));
        }
      });

      const domainSel = document.getElementById("domainFilter");
      Array.from(domains).sort().forEach(d => {
        domainSel.innerHTML += `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`;
      });

      if (years.size > 0) {
        minGlobalYear = Math.min(...Array.from(years));
        maxGlobalYear = Math.max(...Array.from(years));
      } else {
        minGlobalYear = 1950;
        maxGlobalYear = 2026;
      }

      const minYearRange = document.getElementById("minYearRange");
      const maxYearRange = document.getElementById("maxYearRange");
      minYearRange.min = minGlobalYear;
      minYearRange.max = maxGlobalYear;
      minYearRange.value = minGlobalYear;

      maxYearRange.min = minGlobalYear;
      maxYearRange.max = maxGlobalYear;
      maxYearRange.value = maxGlobalYear;

      if (durations.size > 0) {
        minGlobalDuration = 0;
        maxGlobalDuration = Math.max(...Array.from(durations));
        if (maxGlobalDuration < 180) maxGlobalDuration = 240;
      } else {
        minGlobalDuration = 0;
        maxGlobalDuration = 240;
      }

      const minDurRange = document.getElementById("minDurationRange");
      const maxDurRange = document.getElementById("maxDurationRange");
      minDurRange.min = minGlobalDuration;
      minDurRange.max = maxGlobalDuration;
      minDurRange.value = minGlobalDuration;

      maxDurRange.min = minGlobalDuration;
      maxDurRange.max = maxGlobalDuration;
      maxDurRange.value = maxGlobalDuration;

      const countrySel = document.getElementById("countryFilter");
      Array.from(countries).sort().forEach(c => {
        if(c) countrySel.innerHTML += `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`;
      });

      updateYearSliderLabel();
      updateDurationSliderLabel();
      updateImdbSliderLabel();
      updateMyScoreSliderLabel();

      renderRecentDropdown();
      loadStateFromStorageDelayed();
    } catch (err) {
      console.error("initFilters error:", err);
    }
  }

  function updateYearSliderLabel() {
    const minRange = document.getElementById("minYearRange");
    const maxRange = document.getElementById("maxYearRange");
    const label = document.getElementById("yearRangeLabel");
    if (!minRange || !maxRange || !label) return;

    let minVal = parseInt(minRange.value, 10);
    let maxVal = parseInt(maxRange.value, 10);

    if (minVal > maxVal) {
      let temp = minVal;
      minVal = maxVal;
      maxVal = temp;
    }

    if (minVal === parseInt(minRange.min, 10) && maxVal === parseInt(maxRange.max, 10)) {
      label.innerText = "Tümü";
    } else {
      label.innerText = `${minVal} - ${maxVal}`;
    }
  }

  function updateDurationSliderLabel() {
    const minRange = document.getElementById("minDurationRange");
    const maxRange = document.getElementById("maxDurationRange");
    const label = document.getElementById("durationRangeLabel");
    if (!minRange || !maxRange || !label) return;

    let minVal = parseInt(minRange.value, 10);
    let maxVal = parseInt(maxRange.value, 10);

    if (minVal > maxVal) {
      let temp = minVal;
      minVal = maxVal;
      maxVal = temp;
    }

    if (minVal === parseInt(minRange.min, 10) && maxVal === parseInt(maxRange.max, 10)) {
      label.innerText = "Tümü";
    } else {
      label.innerText = `${minVal}dk - ${maxVal}dk`;
    }
  }

  function updateImdbSliderLabel() {
    const minRange = document.getElementById("minImdbRange");
    const maxRange = document.getElementById("maxImdbRange");
    const label = document.getElementById("imdbRangeLabel");
    if (!minRange || !maxRange || !label) return;

    let minVal = parseFloat(minRange.value);
    let maxVal = parseFloat(maxRange.value);

    if (minVal > maxVal) {
      let temp = minVal;
      minVal = maxVal;
      maxVal = temp;
    }

    if (minVal === parseFloat(minRange.min) && maxVal === parseFloat(maxRange.max)) {
      label.innerText = "Tümü";
    } else {
      label.innerText = `${minVal.toFixed(1)} - ${maxVal.toFixed(1)}`;
    }
  }

  function updateMyScoreSliderLabel() {
    const minRange = document.getElementById("minMyScoreRange");
    const maxRange = document.getElementById("maxMyScoreRange");
    const label = document.getElementById("myScoreRangeLabel");
    if (!minRange || !maxRange || !label) return;

    let minVal = parseFloat(minRange.value);
    let maxVal = parseFloat(maxRange.value);

    if (minVal > maxVal) {
      let temp = minVal;
      minVal = maxVal;
      maxVal = temp;
    }

    if (minVal === parseFloat(minRange.min) && maxVal === parseFloat(maxRange.max)) {
      label.innerText = "Tümü";
    } else {
      label.innerText = `${minVal.toFixed(1)} - ${maxVal.toFixed(1)}`;
    }
  }

  function getActorsString(m) {
    const actors = [m.actor1, m.actor2, m.actor3, m.actor4, m.actor5, m.actor6, m.actor7].filter(Boolean);
    return actors.join(", ");
  }

  function scrollToMovie(movieId, keepHighlight = true) {
    if (!movieId) return;
    const cleanId = String(movieId).trim();
    if (keepHighlight) {
      persistentHighlightedMovieId = cleanId;
    }
    applyPersistentHighlight();
    const targetElem = document.querySelector(`[data-movie-id-card="${cleanId}"]`) || document.getElementById("movie-card-" + cleanId);
    if (targetElem) {
      targetElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function goToPage(pageNum, scrollTop = true) {
    const totalPages = Math.max(1, Math.ceil(activeOrderedMovieIds.length / PAGE_SIZE));
    const targetPage = Math.min(Math.max(1, parseInt(pageNum, 10) || 1), totalPages);
    if (targetPage === currentPage && !scrollTop) return;
    currentPage = targetPage;
    renderMovies(false, true);
    if (scrollTop) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function renderPaginationBars(totalItems) {
    const topBar = document.getElementById("paginationTopBar");
    const botBar = document.getElementById("paginationBottomBar");
    if (!topBar || !botBar) return;

    const watchlistSelection = document.getElementById("watchlistDropdown").value;
    const isGroupedLinkedView = ((watchlistSelection === "linked_only" || watchlistSelection === "remake_only" || watchlistSelection === "genre_only") && !activeRelationFilterSet);

    if (isGroupedLinkedView || totalItems <= PAGE_SIZE) {
      topBar.classList.add("hidden-bar");
      botBar.classList.add("hidden-bar");
      topBar.innerHTML = "";
      botBar.innerHTML = "";
      return;
    }

    topBar.classList.remove("hidden-bar");
    botBar.classList.remove("hidden-bar");

    const totalPages = Math.ceil(totalItems / PAGE_SIZE);
    if (currentPage > totalPages) currentPage = totalPages;

    let html = `<button type="button" class="page-btn" onclick="goToPage(1)" ${currentPage === 1 ? "disabled" : ""}>« İlk</button>`;
    html += `<button type="button" class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? "disabled" : ""}>‹ Önceki</button>`;

    const windowSize = 3;
    const pagesToShow = new Set([1, totalPages]);
    for (let p = currentPage - windowSize; p <= currentPage + windowSize; p++) {
      if (p >= 1 && p <= totalPages) pagesToShow.add(p);
    }

    const sortedPages = Array.from(pagesToShow).sort((a, b) => a - b);
    let prev = 0;
    for (const p of sortedPages) {
      if (prev && p - prev > 1) {
        html += `<span style="color:#777; padding:0 4px;">...</span>`;
      }
      html += `<button type="button" class="page-btn ${p === currentPage ? "active-page" : ""}" onclick="goToPage(${p})">${p}</button>`;
      prev = p;
    }

    html += `<button type="button" class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? "disabled" : ""}>Sonraki ›</button>`;
    html += `<button type="button" class="page-btn" onclick="goToPage(${totalPages})" ${currentPage === totalPages ? "disabled" : ""}>Son »</button>`;
    html += `<span class="page-info-text">Sayfa ${currentPage} / ${totalPages} (${totalItems} film)</span>`;

    topBar.innerHTML = html;
    botBar.innerHTML = html;
  }

  function saveStateToStorage() {
    try {
      const state = {
        search: document.getElementById("searchInput").value,
        domain: document.getElementById("domainFilter").value,
        minYear: document.getElementById("minYearRange").value,
        maxYear: document.getElementById("maxYearRange").value,
        country: document.getElementById("countryFilter").value,
        minDuration: document.getElementById("minDurationRange").value,
        maxDuration: document.getElementById("maxDurationRange").value,
        minImdb: document.getElementById("minImdbRange").value,
        maxImdb: document.getElementById("maxImdbRange").value,
        minMyScore: document.getElementById("minMyScoreRange").value,
        maxMyScore: document.getElementById("maxMyScoreRange").value,
        sort1: document.getElementById("sortSelect1").value,
        sort2: document.getElementById("sortSelect2").value,
        watchlistSelection: document.getElementById("watchlistDropdown").value,
        linkedGroupsSort: document.getElementById("linkedGroupsSortSelect").value,
        showHidden: document.getElementById("showHiddenCheckbox").checked,
        lastId: document.getElementById("lastIdInput").value
      };
      localStorage.setItem("archive_ui_state", JSON.stringify(state));
    } catch (e) {
      localStorage.removeItem("archive_ui_state");
    }
  }

  function loadStateFromStorageDelayed() {
    setTimeout(() => {
      try {
        const saved = localStorage.getItem("archive_ui_state");
        if (saved) {
          const state = JSON.parse(saved);
          if (state.search !== undefined) document.getElementById("searchInput").value = state.search;
          if (state.domain !== undefined) document.getElementById("domainFilter").value = state.domain;
          if (state.minYear !== undefined) document.getElementById("minYearRange").value = state.minYear;
          if (state.maxYear !== undefined) document.getElementById("maxYearRange").value = state.maxYear;
          if (state.country !== undefined) document.getElementById("countryFilter").value = state.country;
          if (state.minDuration !== undefined) document.getElementById("minDurationRange").value = state.minDuration;
          if (state.maxDuration !== undefined) document.getElementById("maxDurationRange").value = state.maxDuration;
          if (state.minImdb !== undefined) document.getElementById("minImdbRange").value = state.minImdb;
          if (state.maxImdb !== undefined) document.getElementById("maxImdbRange").value = state.maxImdb;
          if (state.minMyScore !== undefined) document.getElementById("minMyScoreRange").value = state.minMyScore;
          if (state.maxMyScore !== undefined) document.getElementById("maxMyScoreRange").value = state.maxMyScore;
          if (state.sort1 !== undefined) document.getElementById("sortSelect1").value = state.sort1;
          if (state.sort2 !== undefined) document.getElementById("sortSelect2").value = state.sort2;
          if (state.watchlistSelection) {
            document.getElementById("watchlistDropdown").value = state.watchlistSelection;
          }
          if (state.linkedGroupsSort) {
            document.getElementById("linkedGroupsSortSelect").value = state.linkedGroupsSort;
          }
          if (state.showHidden) {
            document.getElementById("showHiddenCheckbox").checked = true;
          }
          if (state.lastId) {
            document.getElementById("lastIdInput").value = state.lastId;
          }
        } else {
          document.getElementById("domainFilter").value = "hdfilmcehennemi.nl";
          document.getElementById("sortSelect1").value = "imdb_desc";
          document.getElementById("sortSelect2").value = "year_desc";
        }

        updateYearSliderLabel();
        updateDurationSliderLabel();
        updateImdbSliderLabel();
        updateMyScoreSliderLabel();

        const generalLastId = localStorage.getItem("last_clicked_movie_id");
        if (generalLastId && !document.getElementById("lastIdInput").value) {
          if (!isNaN(generalLastId)) {
            document.getElementById("lastIdInput").value = generalLastId;
          } else {
            localStorage.removeItem("last_clicked_movie_id");
          }
        }

        renderMovies(false);
      } catch (e) {
        localStorage.removeItem("archive_ui_state");
        localStorage.removeItem("last_clicked_movie_id");
      }
    }, 150);
  }

  function renderRecentDropdown() {
    const sel = document.getElementById("recentMoviesDropdown");
    if (!sel) return;
    sel.innerHTML = `<option value="">🕒 Geçmiş (Son 30)</option>`;

    const showHidden = document.getElementById("showHiddenCheckbox").checked;

    recentMoviesState.forEach(item => {
      const fid = String(item.id);
      const isHidden = !!hiddenMoviesState[fid];
      if (isHidden && !showHidden) {
        return;
      }

      const opt = document.createElement("option");
      opt.value = fid;
      opt.textContent = `${fid} - ${item.title}`;
      sel.appendChild(opt);
    });
    sel.value = "";
  }

  function addRecentMovie(movieId) {
    const fid = String(movieId).trim();
    if (!fid) return;
    const movieObj = allMovies.find(m => String(m.film_ID) === fid);
    const title = movieObj && movieObj.film_name ? movieObj.film_name : `Film #${fid}`;
    recentMoviesState = recentMoviesState.filter(item => String(item.id) !== fid);
    recentMoviesState.unshift({ id: fid, title: title });
    if (recentMoviesState.length > 30) {
      recentMoviesState = recentMoviesState.slice(0, 30);
    }
    try {
      localStorage.setItem("recent_clicked_movies", JSON.stringify(recentMoviesState));
    } catch (e) {}
    renderRecentDropdown();
  }

  function handleCardClick(movieId) {
    try {
      if (movieId) {
        const fid = String(movieId).trim();
        localStorage.setItem("last_clicked_movie_id", fid);
        document.getElementById("lastIdInput").value = fid;
        syncCardRadioSelection(fid);
        persistentHighlightedMovieId = fid;
        applyPersistentHighlight();
        addRecentMovie(fid);
        saveStateToStorage();
        if (sidebarMode === "genre_add") {
          loadMovieGenresIntoSidebar();
        }
      }
    } catch (e) {}
  }

  function updateWatchlist(listNum, movieId, isChecked) {
    try {
      if (listNum === 1) {
        watchlist1State[movieId] = isChecked;
        localStorage.setItem("watchlist_ids", JSON.stringify(watchlist1State));
      } else if (listNum === 2) {
        watchlist2State[movieId] = isChecked;
        localStorage.setItem("watchlist_ids2", JSON.stringify(watchlist2State));
      } else if (listNum === 3) {
        watchlist3State[movieId] = isChecked;
        localStorage.setItem("watchlist_ids3", JSON.stringify(watchlist3State));
      }
      saveStateToStorage();

      const currentSelection = document.getElementById("watchlistDropdown").value;
      if (currentSelection !== "all") {
        renderMoviesPreservingScroll();
      }
    } catch (e) {}
  }

  function updateWatched(movieId, isChecked) {
    try {
      watchedState[movieId] = isChecked;
      localStorage.setItem("watched_ids", JSON.stringify(watchedState));
      saveStateToStorage();

      const currentSelection = document.getElementById("watchlistDropdown").value;
      if (currentSelection === "watched") {
        renderMoviesPreservingScroll();
      }
    } catch (e) {}
  }

  function updateGlorious(movieId, isChecked) {
    try {
      gloriousState[movieId] = isChecked;
      localStorage.setItem("glorious_movie_ids", JSON.stringify(gloriousState));
      saveStateToStorage();

      const currentSelection = document.getElementById("watchlistDropdown").value;
      if (currentSelection === "glorious") {
        renderMoviesPreservingScroll();
      }
    } catch (e) {}
  }

  function updateMyScore(movieId, scoreVal) {
    try {
      if (scoreVal === "" || isNaN(scoreVal)) {
        delete myScoreState[movieId];
      } else {
        myScoreState[movieId] = parseFloat(scoreVal);
      }
      localStorage.setItem("myscore_ids", JSON.stringify(myScoreState));
      saveStateToStorage();
    } catch (e) {}
  }

  function toggleHiddenMovie(movieId) {
    try {
      const fid = String(movieId);
      if (hiddenMoviesState[fid]) {
        delete hiddenMoviesState[fid];
      } else {
        hiddenMoviesState[fid] = true;
      }
      localStorage.setItem("hidden_movie_ids", JSON.stringify(hiddenMoviesState));
      updateRelationBanner();
      renderMoviesPreservingScroll();
      renderRecentDropdown();
    } catch (e) {}
  }

  function executeGoToId() {
    const manualId = document.getElementById("lastIdInput").value.trim();
    if (manualId && !isNaN(manualId)) {
      document.getElementById("searchInput").value = "";
      document.getElementById("domainFilter").value = "";
      document.getElementById("minYearRange").value = minGlobalYear;
      document.getElementById("maxYearRange").value = maxGlobalYear;
      updateYearSliderLabel();
      document.getElementById("countryFilter").value = "";
      document.getElementById("minDurationRange").value = minGlobalDuration;
      document.getElementById("maxDurationRange").value = maxGlobalDuration;
      updateDurationSliderLabel();
      document.getElementById("minImdbRange").value = 0;
      document.getElementById("maxImdbRange").value = 10;
      updateImdbSliderLabel();
      document.getElementById("minMyScoreRange").value = 0;
      document.getElementById("maxMyScoreRange").value = 10;
      updateMyScoreSliderLabel();

      sidebarSelectedGenreKeys.clear();
      document.getElementById("watchlistDropdown").value = "all";
      document.getElementById("showHiddenCheckbox").checked = false;

      activeRelationFilterSet = null;
      updateRelationBanner();

      try {
        localStorage.setItem("last_clicked_movie_id", manualId);
        saveStateToStorage();
      } catch (e) {}

      renderMovies(false, true);

      const idxInList = activeOrderedMovieIds.indexOf(String(manualId));
      if (idxInList !== -1) {
        const targetPage = Math.floor(idxInList / PAGE_SIZE) + 1;
        if (targetPage !== currentPage) {
          currentPage = targetPage;
          renderMovies(false, true);
        }
      }

      if (sidebarMode === "genre_add") {
        loadMovieGenresIntoSidebar();
      }

      requestAnimationFrame(() => {
        scrollToMovie(manualId, true);
      });
    }
  }

  function compareByCriteria(a, b, sortVal) {
    if (sortVal === "imdb_desc") return (b.imdb_score || 0) - (a.imdb_score || 0);
    if (sortVal === "imdb_asc") return (a.imdb_score || 0) - (b.imdb_score || 0);
    if (sortVal === "year_desc") return (b.year || 0) - (a.year || 0);
    if (sortVal === "year_asc") return (a.year || 0) - (b.year || 0);
    if (sortVal === "title_asc") return (a.film_name || "").localeCompare(b.film_name || "");
    if (sortVal === "title_desc") return (b.film_name || "").localeCompare(a.film_name || "");
    return 0;
  }

  function compareMoviesByCurrentSort(a, b, sort1, sort2) {
    if (sort1 !== "default") {
      const res1 = compareByCriteria(a, b, sort1);
      if (res1 !== 0) return res1;
    }
    if (sort2 !== "default") {
      const res2 = compareByCriteria(a, b, sort2);
      if (res2 !== 0) return res2;
    }
    return 0;
  }

  function arrangeMoviesWithRelationsSideBySide(movieList, showHidden, sort1, sort2) {
    if (!Array.isArray(movieList) || movieList.length <= 1) {
      return movieList;
    }

    const movieMap = new Map();
    movieList.forEach(m => movieMap.set(String(m.film_ID), m));

    const parent = new Map();
    movieList.forEach(m => {
      const fid = String(m.film_ID);
      parent.set(fid, fid);
    });

    function findRoot(x) {
      let r = parent.get(x);
      if (r !== x) {
        r = findRoot(r);
        parent.set(x, r);
      }
      return r;
    }

    function unionIds(a, b) {
      const ra = findRoot(a);
      const rb = findRoot(b);
      if (ra !== rb) {
        parent.set(rb, ra);
      }
    }

    const relGroups = [...seriesMoviesGroupsState, ...remakeMoviesGroupsState];
    relGroups.forEach(group => {
      if (!Array.isArray(group) || group.length < 2) return;
      const visibleMembers = group.slice(1)
        .map(String)
        .filter(id => movieMap.has(id) && (showHidden || !hiddenMoviesState[id]));
      for (let i = 1; i < visibleMembers.length; i++) {
        unionIds(visibleMembers[0], visibleMembers[i]);
      }
    });

    const clusterBuckets = new Map();
    movieList.forEach(m => {
      const fid = String(m.film_ID);
      const root = findRoot(fid);
      if (!clusterBuckets.has(root)) {
        clusterBuckets.set(root, []);
      }
      clusterBuckets.get(root).push(m);
    });

    const result = [];
    const emittedRoots = new Set();

    movieList.forEach(m => {
      const fid = String(m.film_ID);
      const root = findRoot(fid);
      if (emittedRoots.has(root)) return;
      emittedRoots.add(root);

      const clusterMovies = clusterBuckets.get(root) || [m];
      if (clusterMovies.length > 1) {
        clusterMovies.sort((x, y) => compareMoviesByCurrentSort(x, y, sort1, sort2));
      }
      clusterMovies.forEach(cm => result.push(cm));
    });

    return result;
  }

  function buildAddMovieToGenreCard(genreKey) {
    const card = document.createElement("div");
    card.className = "add-movie-to-genre-card";
    card.title = "Bu türe toplu olarak film ekle";
    card.innerHTML = `
      <div class="add-movie-plus-circle">+</div>
      <div class="add-movie-label">Film Ekle</div>
    `;
    card.addEventListener("click", (e) => {
      e.stopPropagation();
      openBulkAddMoviesToGenrePopup(genreKey);
    });
    return card;
  }

  function buildMovieCardElement(movie, showHidden, currentGeneralLastId, contextPrefix = "", positionIndex = null, totalCount = null) {
    const fid = String(movie.film_ID);
    const card = document.createElement("div");
    card.className = "movie-card";
    if (persistentHighlightedMovieId && String(persistentHighlightedMovieId) === fid) {
      card.classList.add("highlight");
    }
    card.id = contextPrefix ? `movie-card-${contextPrefix}-${fid}` : `movie-card-${fid}`;
    card.dataset.movieIdCard = fid;
    card.addEventListener("click", (e) => {
      if (e.target.closest("a, button, input, select, textarea, label")) return;
      handleCardClick(fid);
    });

    const posterUrl = movie.poster || "";
    const imdbText = movie.imdb_score ? "⭐ " + movie.imdb_score : "⭐ -";
    const yearText = movie.year ? String(movie.year) : "-";
    const durationText = movie.duration_mins ? `${Math.round(parseFloat(movie.duration_mins))}dk` : "";
    const actorsStr = getActorsString(movie);
    const domainText = getDomain(movie.web_scraper_start_url);
    const countryText = (movie.country || "").trim();
    const summaryRaw = (movie.movie_summary || "").trim();
    const summaryDisplay = summaryRaw || "Özet bulunamadı.";

    const altUrls = alternativeUrlsState[fid] || [];
    let altLinksHtml = "";
    altUrls.forEach((altUrl, idx) => {
      const label = `URL${idx + 2}`;
      altLinksHtml += ` | <a class="alt-url-link" href="${escapeHtml(altUrl)}" target="_blank" title="${escapeHtml(altUrl)}" onclick="handleCardClick('${fid}')">${label}</a>`;
    });

    const countryHtml = countryText
      ? `<span class="country-badge" title="${escapeHtml(countryText)}">${escapeHtml(countryText)}</span>`
      : `<span class="country-badge"></span>`;

    const domainContainerHtml = (domainText || countryText) ? `
      <div class="domain-container">
        <div class="domain-left" title="URL'leri yönetmek için domain adına tıklayın">
          ${domainText ? `<span class="domain-badge" onclick="openUrlPopup('${fid}')">${escapeHtml(domainText)}</span>` : ""}
          ${altLinksHtml}
        </div>
        ${countryHtml}
      </div>
    ` : "";

    const c1 = watchlist1State[fid] ? "checked" : "";
    const c2 = watchlist2State[fid] ? "checked" : "";
    const c3 = watchlist3State[fid] ? "checked" : "";
    const cWatched = watchedState[fid] ? "checked" : "";
    const cGlorious = gloriousState[fid] ? "checked" : "";
    const isRadioChecked = (currentGeneralLastId === fid) ? "checked" : "";
    const myScoreVal = myScoreState[fid] !== undefined ? myScoreState[fid] : "";
    const isHidden = !!hiddenMoviesState[fid];
    if (isHidden) {
      card.classList.add("hidden-card");
    }
    const eyeBtnTitle = isHidden ? "Gizli (Tekrar görünür yapmak için tıkla)" : "Bu filmi gizle";
    const eyeBtnIcon = isHidden ? "🙈" : "👁️";

    const positionBadgeHtml = (positionIndex !== null && totalCount !== null)
      ? `<div class="card-position-badge" title="Mevcut görünümdeki sırası: ${positionIndex} / ${totalCount}">${positionIndex} / ${totalCount}</div>`
      : "";

    const rawSeriesGroup = getSeriesGroupForMovie(fid);
    const seriesMembers = rawSeriesGroup ? (showHidden ? rawSeriesGroup.slice(1) : rawSeriesGroup.slice(1).filter(id => !hiddenMoviesState[id])) : null;
    const hasValidSeriesGroup = seriesMembers && seriesMembers.length >= 1;
    const isSeriesActiveGroup = activeRelationFilterSet && activeRelationFilterSet.type === 'series' && rawSeriesGroup && activeRelationFilterSet.groupKey === rawSeriesGroup[0];
    const seriesOtherIds = hasValidSeriesGroup ? (seriesMembers.filter(id => id !== fid).join(", ") || "Tek film") : "";
    const seriesInputVal = rawSeriesGroup ? rawSeriesGroup.slice(1).filter(id => id !== fid).join(",") : "";

    const rawRemakeGroup = getRemakeGroupForMovie(fid);
    const remakeMembers = rawRemakeGroup ? (showHidden ? rawRemakeGroup.slice(1) : rawRemakeGroup.slice(1).filter(id => !hiddenMoviesState[id])) : null;
    const hasValidRemakeGroup = remakeMembers && remakeMembers.length >= 1;
    const isRemakeActiveGroup = activeRelationFilterSet && activeRelationFilterSet.type === 'remake' && rawRemakeGroup && activeRelationFilterSet.groupKey === rawRemakeGroup[0];
    const remakeOtherIds = hasValidRemakeGroup ? (remakeMembers.filter(id => id !== fid).join(", ") || "Tek film") : "";
    const remakeInputVal = rawRemakeGroup ? rawRemakeGroup.slice(1).filter(id => id !== fid).join(",") : "";

    const rawGenreGroups = getGenreGroupsForMovie(fid);
    const validGenreGroups = rawGenreGroups.map(g => {
      const visibleM = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
      return {
        key: g[0],
        rawGroup: g,
        name: getGenreGroupName(g),
        visibleMembers: visibleM
      };
    }).filter(item => item.visibleMembers.length >= 1);

    let groupNameBadgesHtml = "";
    if (hasValidSeriesGroup) {
      const gNameStr = getSeriesGroupName(rawSeriesGroup);
      groupNameBadgesHtml += `<div class="poster-group-name-badge" title="${escapeHtml(gNameStr)}" style="background: rgba(29, 78, 216, 0.85);">🎬 ${escapeHtml(gNameStr)}</div>`;
    }
    if (hasValidRemakeGroup) {
      const rNameStr = getRemakeGroupName(rawRemakeGroup);
      groupNameBadgesHtml += `<div class="poster-group-name-badge" title="${escapeHtml(rNameStr)}" style="background: rgba(91, 33, 182, 0.85);">🎥 ${escapeHtml(rNameStr)}</div>`;
    }
    validGenreGroups.forEach(gItem => {
      groupNameBadgesHtml += `<div class="poster-group-name-badge" title="${escapeHtml(gItem.name)}" style="background: rgba(5, 150, 105, 0.85);">🏷️ ${escapeHtml(gItem.name)}</div>`;
    });

    let badgesRightHtml = "";
    if (hasValidSeriesGroup) {
      badgesRightHtml += `<button class="relation-badge-btn ${isSeriesActiveGroup ? 'active-group' : ''}" title="Seri Filmler: ${seriesOtherIds} (Filtrelemek için tıkla)" onclick="filterByRelationGroup('${fid}', 'series')">🎬 ${seriesMembers.length}</button>`;
    }
    if (hasValidRemakeGroup) {
      badgesRightHtml += `<button class="remake-badge-btn ${isRemakeActiveGroup ? 'active-group' : ''}" title="Remake Filmler: ${remakeOtherIds} (Filtrelemek için tıkla)" onclick="filterByRelationGroup('${fid}', 'remake')">🎥 ${remakeMembers.length}</button>`;
    }
    validGenreGroups.forEach(gItem => {
      const isThisGenreActive = activeRelationFilterSet && activeRelationFilterSet.type === 'genre' && activeRelationFilterSet.groupKey === gItem.key;
      badgesRightHtml += `<button class="genre-badge-btn ${isThisGenreActive ? 'active-group' : ''}" title="Tür: ${escapeHtml(gItem.name)} (${gItem.visibleMembers.length} film)" onclick="filterByRelationGroup('${fid}', 'genre', '${gItem.key}')">🏷️ ${gItem.visibleMembers.length}</button>`;
    });

    const unlinkSeriesHtml = rawSeriesGroup
      ? `<button class="btn-unlink" title="Seriden ayır" onclick="unlinkMovie('${fid}', 'series')" style="font-size:9px; background:#7f1d1d; color:#fff; border:none; padding:1px 3px; border-radius:2px; cursor:pointer;">Seri Ayır</button>`
      : "";

    const unlinkRemakeHtml = rawRemakeGroup
      ? `<button class="btn-unlink" title="Remake'den ayır" onclick="unlinkMovie('${fid}', 'remake')" style="font-size:9px; background:#5b21b6; color:#fff; border:none; padding:1px 3px; border-radius:2px; cursor:pointer;">Remake Ayır</button>`
      : "";

    let genrePillsHtml = "";
    if (rawGenreGroups.length > 0) {
      genrePillsHtml = `<div class="genre-tags-list">`;
      rawGenreGroups.forEach(g => {
        const gKey = g[0];
        const gName = getGenreGroupName(g);
        genrePillsHtml += `
          <span class="genre-tag-pill" title="${escapeHtml(gName)}">
            <span class="g-pill-text" onclick="filterByRelationGroup('${fid}', 'genre', '${gKey}')">${escapeHtml(gName)}</span>
            <button type="button" class="genre-tag-remove-btn" title="${escapeHtml(gName)} türünden ayır" onclick="unlinkMovie('${fid}', 'genre', '${gKey}')">×</button>
          </span>
        `;
      });
      genrePillsHtml += `</div>`;
    }

    const titleTooltip = isSimpleViewMode ? summaryDisplay : movie.film_name;

    card.innerHTML = `
      <div class="watchlist-group" title="İzleme Listeleri (1, 2, 3)">
        <input type="checkbox" class="watchlist-checkbox" ${c1} title="İzleme Listesi 1" onchange="updateWatchlist(1, '${fid}', this.checked)">
        <input type="checkbox" class="watchlist-checkbox" ${c2} title="İzleme Listesi 2" onchange="updateWatchlist(2, '${fid}', this.checked)">
        <input type="checkbox" class="watchlist-checkbox" ${c3} title="İzleme Listesi 3" onchange="updateWatchlist(3, '${fid}', this.checked)">
      </div>
      ${positionBadgeHtml}
      <div class="glorious-group" title="Muhteşem Filmler olarak işaretle">
        <input type="checkbox" class="glorious-checkbox" ${cGlorious} title="Muhteşem Filmler" onchange="updateGlorious('${fid}', this.checked)">
      </div>
      <div class="poster-badges-right">
        ${badgesRightHtml}
      </div>
      <div class="poster-wrapper">
        <img src="${escapeHtml(posterUrl)}" alt="${escapeHtml(movie.film_name)}" loading="lazy" onerror="this.onerror=null; this.src='https://via.placeholder.com/210x290?text=Afi%C5%9F+Yok';">
        <div class="select-id-radio-wrap" title="Bu filmin ID'sini Son ID kutucuğuna ata">
          <input type="radio" name="selectedMovieRadio" class="select-id-radio" ${isRadioChecked} onchange="selectMovieIdFromCardRadio('${fid}')">
        </div>
        <div class="poster-badges-bottom">
          ${groupNameBadgesHtml}
        </div>
        <button class="hide-movie-btn ${isHidden ? 'is-hidden' : ''}" title="${eyeBtnTitle}" onclick="toggleHiddenMovie('${fid}')">${eyeBtnIcon}</button>
      </div>
      <div class="card-user-actions">
        <label class="watched-label" title="İzlediklerim">
          <input type="checkbox" class="watched-checkbox" ${cWatched} onchange="updateWatched('${fid}', this.checked)"> İzledim
        </label>
        <span class="film-id-badge" title="Film ID">ID: ${fid}</span>
        <div class="score-container" title="Puanım (1-10)">
          <span>Puanım:</span>
          <input type="number" class="score-input" min="0" max="10" step="0.1" value="${myScoreVal}" onchange="updateMyScore('${fid}', this.value)">
        </div>
      </div>
      <div class="card-relation-bar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div class="relation-input-wrap" title="Seri ID'si yazıp Enter'a basın">
            <span class="relation-label">🎬 Seri:</span>
            <input type="text" inputmode="numeric" class="relation-input" value="${escapeHtml(seriesInputVal)}" placeholder="ID" onfocus="this.select()" onkeydown="if(event.key==='Enter'){ this.blur(); }" onblur="linkMovies('${fid}', this.value, 'series');">
            <button class="btn-add-group group-popup-trigger" type="button" data-type="series" data-movie-id="${fid}" title="Mevcut bir seri grubuna dahil et veya yeni oluştur (+)">+</button>
          </div>
          ${unlinkSeriesHtml}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div class="relation-input-wrap" title="Remake ID'si yazıp Enter'a basın">
            <span class="relation-label">🎥 Remake:</span>
            <input type="text" inputmode="numeric" class="relation-input" value="${escapeHtml(remakeInputVal)}" placeholder="ID" onfocus="this.select()" onkeydown="if(event.key==='Enter'){ this.blur(); }" onblur="linkMovies('${fid}', this.value, 'remake');" style="color:#d8b4fe; border-color:#7c3aed;">
            <button class="btn-add-remake group-popup-trigger" type="button" data-type="remake" data-movie-id="${fid}" title="Mevcut bir remake grubuna dahil et veya yeni oluştur (+)">+</button>
          </div>
          ${unlinkRemakeHtml}
        </div>
        <div style="display: flex; flex-direction: column; gap: 2px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="relation-input-wrap" title="Yeni tür grubu oluşturmak için başka bir film ID'si yazın veya + ile mevcut türlerden seçin">
              <span class="relation-label">🏷️ Tür:</span>
              <input type="text" inputmode="numeric" class="relation-input" value="" placeholder="ID" onfocus="this.select()" onkeydown="if(event.key==='Enter'){ this.blur(); }" onblur="linkMovies('${fid}', this.value, 'genre');" style="color:#a7f3d0; border-color:#10b981;">
              <button class="btn-add-genre group-popup-trigger" type="button" data-type="genre" data-movie-id="${fid}" title="Mevcut türlerden çoklu seç veya yeni oluştur (+)">+</button>
            </div>
          </div>
          ${genrePillsHtml}
        </div>
      </div>
      <div class="card-details">
        ${domainContainerHtml}
        <a class="movie-title" href="${escapeHtml(movie.web_scraper_start_url)}" target="_blank" title="${escapeHtml(titleTooltip)}" onclick="handleCardClick('${fid}')">${escapeHtml(movie.film_name)}</a>
        <div class="meta-info">
          <span>${imdbText}</span>
          <span>${durationText}</span>
          <span>${yearText}</span>
        </div>
        <div class="summary-text" title="${escapeHtml(summaryDisplay)}">${escapeHtml(summaryDisplay)}</div>
        <div class="actors-text" title="Oyuncular: ${escapeHtml(actorsStr || 'Bilgi yok')}">🎭 ${escapeHtml(actorsStr || 'Oyuncu bilgisi yok')}</div>
      </div>
    `;

    return card;
  }

  function populateGroupMoviesContainer(moviesContainer, groupKey, expand) {
    if (!moviesContainer) return;
    if (!expand) {
      moviesContainer.innerHTML = "";
      return;
    }
    if (moviesContainer.children.length > 0) return;

    const cached = activeGroupedDataCache.get(groupKey);
    if (!cached) return;

    const frag = document.createDocumentFragment();
    const totalInGroup = cached.grpInfo.movies.length;
    cached.grpInfo.movies.forEach((movie, idx) => {
      frag.appendChild(buildMovieCardElement(movie, cached.showHidden, cached.currentGeneralLastId, cached.grpInfo.key, idx + 1, totalInGroup));
    });
    if (cached.isGenreView) {
      frag.appendChild(buildAddMovieToGenreCard(cached.grpInfo.key));
    }
    moviesContainer.appendChild(frag);
  }

  function renderMovies(forceSearch = false, preservePage = false) {
    try {
      saveStateToStorage();

      if (!preservePage) {
        currentPage = 1;
      }

      const openGroupKeys = new Set();
      document.querySelectorAll(".group-section-wrapper").forEach(wrapper => {
        const moviesContainer = wrapper.querySelector(".group-movies-container");
        if (moviesContainer && !moviesContainer.classList.contains("collapsed")) {
          if (wrapper.dataset.groupKey) {
            openGroupKeys.add(wrapper.dataset.groupKey);
          }
        }
      });

      const container = document.getElementById("movieGridContainer");
      container.innerHTML = "";
      activeGroupedDataCache.clear();

      const searchVal = document.getElementById("searchInput").value.toLowerCase().trim();
      const selectedDomain = document.getElementById("domainFilter").value;
      const minYearVal = parseInt(document.getElementById("minYearRange").value, 10);
      const maxYearVal = parseInt(document.getElementById("maxYearRange").value, 10);
      const selectedCountry = document.getElementById("countryFilter").value;
      const minDurVal = parseInt(document.getElementById("minDurationRange").value, 10);
      const maxDurVal = parseInt(document.getElementById("maxDurationRange").value, 10);
      const minImdbVal = parseFloat(document.getElementById("minImdbRange").value);
      const maxImdbVal = parseFloat(document.getElementById("maxImdbRange").value);
      const minMyScoreVal = parseFloat(document.getElementById("minMyScoreRange").value);
      const maxMyScoreVal = parseFloat(document.getElementById("maxMyScoreRange").value);

      const sort1 = document.getElementById("sortSelect1").value;
      const sort2 = document.getElementById("sortSelect2").value;

      const watchlistSelection = document.getElementById("watchlistDropdown").value;
      const showHidden = document.getElementById("showHiddenCheckbox").checked;

      const linkedSortContainer = document.getElementById("linkedSortContainer");
      const toggleAllBtn = document.getElementById("toggleAllGroupsBtn");

      if ((watchlistSelection === "linked_only" || watchlistSelection === "remake_only" || watchlistSelection === "genre_only") && !activeRelationFilterSet) {
        linkedSortContainer.classList.add("visible");
        toggleAllBtn.classList.add("visible");
      } else {
        linkedSortContainer.classList.remove("visible");
        toggleAllBtn.classList.remove("visible");
      }

      const isSearchActive = Boolean(searchVal && searchVal.length > 0);
      const searchTerms = isSearchActive
        ? searchVal.split("||").map(t => t.trim()).filter(t => t.length > 0)
        : [];

      function matchesBaseFilters(movie) {
        const fid = String(movie.film_ID);

        if (watchlistSelection === "list1" && !watchlist1State[fid]) return false;
        if (watchlistSelection === "list2" && !watchlist2State[fid]) return false;
        if (watchlistSelection === "list3" && !watchlist3State[fid]) return false;
        if (watchlistSelection === "watched" && !watchedState[fid]) return false;
        if (watchlistSelection === "glorious" && !gloriousState[fid]) return false;

        if (watchlistSelection === "linked_only") {
          const g = getSeriesGroupForMovie(fid);
          if (!g) return false;
          const visibleG = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
          if (visibleG.length < 1) return false;
        }

        if (watchlistSelection === "remake_only") {
          const g = getRemakeGroupForMovie(fid);
          if (!g) return false;
          const visibleG = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
          if (visibleG.length < 1) return false;
        }

        if (watchlistSelection === "genre_only") {
          const gs = getGenreGroupsForMovie(fid);
          if (!gs || gs.length === 0) return false;
          const hasVisible = gs.some(g => {
            const visibleG = showHidden ? g.slice(1) : g.slice(1).filter(id => !hiddenMoviesState[id]);
            return visibleG.length >= 1;
          });
          if (!hasVisible) return false;
        }

        if (watchlistSelection === "no_genre") {
          const gs = getGenreGroupsForMovie(fid);
          if (gs && gs.length > 0) return false;
        }

        if (selectedDomain && getDomain(movie.web_scraper_start_url) !== selectedDomain) return false;

        if (movie.year) {
          const mYr = parseInt(movie.year, 10);
          if (!isNaN(mYr)) {
            let actualMin = Math.min(minYearVal, maxYearVal);
            let actualMax = Math.max(minYearVal, maxYearVal);
            if (mYr < actualMin || mYr > actualMax) return false;
          }
        }

        if (selectedCountry && !(movie.country || "").includes(selectedCountry)) return false;

        if (movie.duration_mins) {
          const mDur = parseFloat(movie.duration_mins);
          if (!isNaN(mDur)) {
            let actualMin = Math.min(minDurVal, maxDurVal);
            let actualMax = Math.max(minDurVal, maxDurVal);
            if (mDur < actualMin || mDur > actualMax) return false;
          }
        } else {
          let actualMin = Math.min(minDurVal, maxDurVal);
          if (actualMin > 0) return false;
        }

        if (movie.imdb_score !== undefined && movie.imdb_score !== null) {
          const mImdb = parseFloat(movie.imdb_score);
          if (!isNaN(mImdb)) {
            let actualMin = Math.min(minImdbVal, maxImdbVal);
            let actualMax = Math.max(minImdbVal, maxImdbVal);
            if (mImdb < actualMin || mImdb > actualMax) return false;
          }
        } else {
          let actualMin = Math.min(minImdbVal, maxImdbVal);
          if (actualMin > 0) return false;
        }

        const userScore = myScoreState[fid];
        let actualMyMin = Math.min(minMyScoreVal, maxMyScoreVal);
        let actualMyMax = Math.max(minMyScoreVal, maxMyScoreVal);

        if (actualMyMin > 0 || actualMyMax < 10) {
          if (userScore === undefined || userScore === null) return false;
          const uSc = parseFloat(userScore);
          if (isNaN(uSc) || uSc < actualMyMin || uSc > actualMyMax) return false;
        }

        return true;
      }

      function matchesSearchTerms(movie) {
        if (!isSearchActive || searchTerms.length === 0) return true;
        const name = (movie.film_name || "").toLowerCase();
        const summary = (movie.movie_summary || "").toLowerCase();
        const actors = getActorsString(movie).toLowerCase();

        let groupNameStr = "";
        const sg = getSeriesGroupForMovie(movie.film_ID);
        if (sg) groupNameStr += " " + getSeriesGroupName(sg).toLowerCase();
        const rg = getRemakeGroupForMovie(movie.film_ID);
        if (rg) groupNameStr += " " + getRemakeGroupName(rg).toLowerCase();
        const ggs = getGenreGroupsForMovie(movie.film_ID);
        ggs.forEach(gg => {
          groupNameStr += " " + getGenreGroupName(gg).toLowerCase();
        });

        return searchTerms.some(term =>
          name.includes(term) || summary.includes(term) || actors.includes(term) || groupNameStr.includes(term)
        );
      }

      function matchesSidebarGenres(movie) {
        if (!sidebarSelectedGenreKeys || sidebarSelectedGenreKeys.size === 0) return true;
        const movieGenreKeys = getMovieGenreKeySet(movie.film_ID);
        for (const reqKey of sidebarSelectedGenreKeys) {
          if (!movieGenreKeys.has(reqKey)) {
            return false;
          }
        }
        return true;
      }

      let expandedLinkedIds = null;
      if (!activeRelationFilterSet && isRelatedSideBySideMode) {
        const baseMatchedIds = new Set();
        allMovies.forEach(movie => {
          const fid = String(movie.film_ID);
          if (hiddenMoviesState[fid] && !showHidden) return;
          if (!matchesBaseFilters(movie)) return;
          if (!matchesSearchTerms(movie)) return;
          baseMatchedIds.add(fid);
        });

        expandedLinkedIds = new Set(baseMatchedIds);

        baseMatchedIds.forEach(fid => {
          const sgrp = getSeriesGroupForMovie(fid);
          if (sgrp) sgrp.slice(1).forEach(linkedId => {
            if (showHidden || !hiddenMoviesState[linkedId]) expandedLinkedIds.add(String(linkedId));
          });
          const rgrp = getRemakeGroupForMovie(fid);
          if (rgrp) rgrp.slice(1).forEach(linkedId => {
            if (showHidden || !hiddenMoviesState[linkedId]) expandedLinkedIds.add(String(linkedId));
          });
        });
      }

      const preSidebarMovies = allMovies.filter(movie => {
        const fid = String(movie.film_ID);
        if (hiddenMoviesState[fid] && !showHidden) return false;
        if (activeRelationFilterSet) return activeRelationFilterSet.set.has(fid);
        if (expandedLinkedIds !== null) return expandedLinkedIds.has(fid);
        if (!matchesBaseFilters(movie)) return false;
        if (!matchesSearchTerms(movie)) return false;
        return true;
      });

      let filtered = preSidebarMovies.filter(movie => matchesSidebarGenres(movie));

      renderSidebarGenreListbox(filtered, showHidden);

      const currentGeneralLastId = String(localStorage.getItem("last_clicked_movie_id") || "").trim();
      const isGroupedLinkedView = ((watchlistSelection === "linked_only" || watchlistSelection === "remake_only" || watchlistSelection === "genre_only") && !activeRelationFilterSet);

      if (isGroupedLinkedView) {
        const linkedSortVal = document.getElementById("linkedGroupsSortSelect").value;
        const isRemakeView = (watchlistSelection === "remake_only");
        const isGenreView = (watchlistSelection === "genre_only");

        let groupsList = seriesMoviesGroupsState;
        if (isRemakeView) groupsList = remakeMoviesGroupsState;
        else if (isGenreView) groupsList = genreMoviesGroupsState;

        const filteredMovieMap = new Map();
        filtered.forEach(m => filteredMovieMap.set(String(m.film_ID), m));

        const groupsArray = [];
        groupsList.forEach((g, originalIndex) => {
          if (!Array.isArray(g) || g.length < 2) return;
          const groupKey = g[0];
          const memberIds = g.slice(1);

          const matchedMembers = memberIds
            .map(id => filteredMovieMap.get(String(id)))
            .filter(Boolean);

          const visibleG = showHidden ? memberIds : memberIds.filter(id => !hiddenMoviesState[id]);
          const minLimit = 1;
          if (visibleG.length < minLimit || matchedMembers.length === 0) return;

          let gName = "";
          if (isRemakeView) gName = getRemakeGroupName(g);
          else if (isGenreView) gName = getGenreGroupName(g);
          else gName = getSeriesGroupName(g);

          let maxImdb = 0;
          let maxYear = 0;
          matchedMembers.forEach(m => {
            const sc = parseFloat(m.imdb_score || 0);
            if (sc > maxImdb) maxImdb = sc;
            const yr = parseInt(m.year || 0, 10);
            if (yr > maxYear) maxYear = yr;
          });

          groupsArray.push({
            key: groupKey,
            name: gName,
            count: visibleG.length,
            maxImdb: maxImdb,
            maxYear: maxYear,
            originalIndex: originalIndex,
            movies: matchedMembers
          });
        });

        groupsArray.sort((a, b) => {
          if (linkedSortVal === "default") {
            if (sort1 === "imdb_desc" || sort1 === "imdb_asc") {
              return b.maxImdb - a.maxImdb;
            } else if (sort1 === "year_desc" || sort1 === "year_asc") {
              return b.maxYear - a.maxYear;
            } else if (sort2 === "imdb_desc" || sort2 === "imdb_asc") {
              return b.maxImdb - a.maxImdb;
            } else if (sort2 === "year_desc" || sort2 === "year_asc") {
              return b.maxYear - a.maxYear;
            }
            return a.originalIndex - b.originalIndex;
          } else if (linkedSortVal === "alpha_asc") {
            return a.name.localeCompare(b.name);
          } else if (linkedSortVal === "alpha_desc") {
            return b.name.localeCompare(a.name);
          } else if (linkedSortVal === "count_asc") {
            if (a.count !== b.count) return a.count - b.count;
            return a.name.localeCompare(b.name);
          } else if (linkedSortVal === "count_desc") {
            if (a.count !== b.count) return b.count - a.count;
            return b.name.localeCompare(a.name);
          }
          return 0;
        });

        currentlyRenderedMovieIds = filtered.map(m => String(m.film_ID));
        activeOrderedMovieIds = [...currentlyRenderedMovieIds];
        document.getElementById("countDisplay").innerText = filtered.length;
        renderPaginationBars(filtered.length);

        const fragment = document.createDocumentFragment();
        let iconPrefix = "🎬";
        if (isRemakeView) iconPrefix = "🎥";
        else if (isGenreView) iconPrefix = "🏷️";

        groupsArray.forEach(grpInfo => {
          activeGroupedDataCache.set(grpInfo.key, {
            grpInfo,
            showHidden,
            currentGeneralLastId,
            isGenreView
          });

          const wrapper = document.createElement("div");
          wrapper.className = "group-section-wrapper";
          wrapper.dataset.groupKey = grpInfo.key;

          const secHeader = document.createElement("div");
          secHeader.className = "group-section-header";

          const isOpenPreviously = openGroupKeys.has(grpInfo.key);
          const collapseClass = isOpenPreviously ? "" : "collapsed";
          const collapseIconText = isOpenPreviously ? "▼" : "▶";

          secHeader.innerHTML = `<span>${iconPrefix} ${escapeHtml(grpInfo.name)} (${grpInfo.count} Film)</span><span class="group-collapse-icon">${collapseIconText}</span>`;

          const moviesContainer = document.createElement("div");
          moviesContainer.className = `group-movies-container ${collapseClass}`;

          if (isOpenPreviously) {
            populateGroupMoviesContainer(moviesContainer, grpInfo.key, true);
          }

          wrapper.appendChild(secHeader);
          wrapper.appendChild(moviesContainer);
          fragment.appendChild(wrapper);
        });

        container.appendChild(fragment);
        applyPersistentHighlight();
        updateToggleAllButtonState();
        return;
      }

      if (activeRelationFilterSet) {
        filtered.sort((a, b) => {
          const yearA = a.year ? parseInt(a.year, 10) : Infinity;
          const yearB = b.year ? parseInt(b.year, 10) : Infinity;
          if (yearA !== yearB) {
            return yearA - yearB;
          }
          return parseInt(String(a.film_ID), 10) - parseInt(String(b.film_ID), 10);
        });
      } else {
        filtered.sort((a, b) => compareMoviesByCurrentSort(a, b, sort1, sort2));
        if (isRelatedSideBySideMode) {
          filtered = arrangeMoviesWithRelationsSideBySide(filtered, showHidden, sort1, sort2);
        }
      }

      activeOrderedMovieIds = filtered.map(m => String(m.film_ID));
      const totalFilteredCount = filtered.length;
      document.getElementById("countDisplay").innerText = totalFilteredCount;
      renderPaginationBars(totalFilteredCount);

      const totalPages = Math.max(1, Math.ceil(totalFilteredCount / PAGE_SIZE));
      if (currentPage > totalPages) currentPage = totalPages;
      const startIdx = (currentPage - 1) * PAGE_SIZE;
      const pageMovies = filtered.slice(startIdx, startIdx + PAGE_SIZE);
      currentlyRenderedMovieIds = pageMovies.map(m => String(m.film_ID));

      const fragment = document.createDocumentFragment();
      pageMovies.forEach((movie, pageIdx) => {
        const globalPos = startIdx + pageIdx + 1;
        const card = buildMovieCardElement(movie, showHidden, currentGeneralLastId, "", globalPos, totalFilteredCount);
        fragment.appendChild(card);
      });

      if (activeRelationFilterSet && activeRelationFilterSet.type === 'genre' && activeRelationFilterSet.groupKey) {
        fragment.appendChild(buildAddMovieToGenreCard(activeRelationFilterSet.groupKey));
      }

      container.appendChild(fragment);
      applyPersistentHighlight();
      updateToggleAllButtonState();

    } catch (err) {
      console.error("renderMovies error:", err);
    }
  }

  document.getElementById("toggleFilmSearchSidebarBtn").addEventListener("click", () => {
    setSidebarMode(sidebarMode === "filter" ? null : "filter");
  });
  document.getElementById("toggleGenreAddSidebarBtn").addEventListener("click", () => {
    setSidebarMode(sidebarMode === "genre_add" ? null : "genre_add");
  });
  document.getElementById("toggleRelatedSideBySideBtn").addEventListener("click", toggleRelatedSideBySide);
  document.getElementById("closeFilmSearchSidebarBtn").addEventListener("click", () => {
    setSidebarMode(null);
  });
  document.getElementById("sidebarCancelGenreAddBtn").addEventListener("click", () => {
    setSidebarMode(null);
  });
  document.getElementById("sidebarConfirmGenreAddBtn").addEventListener("click", confirmSidebarGenreAdd);
  document.getElementById("sidebarCreateGenreBtn").addEventListener("click", createNewGenreInSidebar);
  document.getElementById("sidebarNewGenreInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      createNewGenreInSidebar();
    }
  });
  document.getElementById("sidebarRenameGenreBtn").addEventListener("click", renameFocusedGenreInSidebar);
  document.getElementById("sidebarRenameGenreInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      renameFocusedGenreInSidebar();
    }
  });
  document.getElementById("sidebarGenreSearchInput").addEventListener("input", () => renderSidebar4ColGenreList(null));
  document.getElementById("sidebarGenreSortSelect").addEventListener("change", () => renderSidebar4ColGenreList(null));

  document.getElementById("movieGridContainer").addEventListener("click", (e) => {
    const triggerBtn = e.target.closest(".group-popup-trigger");
    if (triggerBtn) {
      const movieId = triggerBtn.dataset.movieId;
      const type = triggerBtn.dataset.type;
      if (movieId && type) {
        openGroupSelectPopup(movieId, type);
      }
      return;
    }

    const header = e.target.closest(".group-section-header");
    if (header) {
      const wrapper = header.closest(".group-section-wrapper");
      if (!wrapper) return;
      const moviesContainer = wrapper.querySelector(".group-movies-container");
      if (!moviesContainer) return;

      const isCollapsed = moviesContainer.classList.toggle("collapsed");
      const iconSpan = header.querySelector(".group-collapse-icon");
      if (iconSpan) {
        iconSpan.innerText = isCollapsed ? "▶" : "▼";
      }

      populateGroupMoviesContainer(moviesContainer, wrapper.dataset.groupKey, !isCollapsed);
      applyPersistentHighlight();
      updateToggleAllButtonState();
    }
  });

  document.getElementById("multiSelectCheckbox").addEventListener("change", updateMultiSelectUI);
  document.getElementById("closeGroupSelectModalBtn").addEventListener("click", closeGroupSelectPopup);
  document.getElementById("confirmGroupSelectBtn").addEventListener("click", confirmGroupSelect);
  document.getElementById("createNewGroupInPopupBtn").addEventListener("click", createNewGroupFromPopup);
  document.getElementById("newGroupInPopupInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      createNewGroupFromPopup();
    }
  });
  document.getElementById("renameGroupInPopupBtn").addEventListener("click", renameSelectedGroupInPopup);
  document.getElementById("renameGroupInPopupInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      renameSelectedGroupInPopup();
    }
  });
  document.getElementById("groupSearchInput").addEventListener("input", () => filterAndSortGroupSelectDropdown(null));
  document.getElementById("groupPopupSortSelect").addEventListener("change", () => filterAndSortGroupSelectDropdown(null));

  document.getElementById("closeBulkAddModalBtn").addEventListener("click", closeBulkAddMoviesToGenrePopup);
  document.getElementById("confirmBulkAddBtn").addEventListener("click", confirmBulkAddMoviesToGenre);
  document.getElementById("bulkSearchInput").addEventListener("input", renderBulkAddMoviesGrid);
  document.getElementById("bulkDomainFilter").addEventListener("change", renderBulkAddMoviesGrid);
  document.getElementById("bulkMinYear").addEventListener("input", renderBulkAddMoviesGrid);
  document.getElementById("bulkMaxYear").addEventListener("input", renderBulkAddMoviesGrid);
  document.getElementById("bulkMinImdb").addEventListener("input", renderBulkAddMoviesGrid);
  document.getElementById("bulkMaxImdb").addEventListener("input", renderBulkAddMoviesGrid);
  document.getElementById("bulkSortSelect").addEventListener("change", renderBulkAddMoviesGrid);
  document.getElementById("bulkShowHiddenCheckbox").addEventListener("change", renderBulkAddMoviesGrid);
  document.getElementById("bulkResetFiltersBtn").addEventListener("click", () => {
    document.getElementById("bulkSearchInput").value = "";
    document.getElementById("bulkDomainFilter").value = "";
    document.getElementById("bulkMinYear").value = "";
    document.getElementById("bulkMaxYear").value = "";
    document.getElementById("bulkMinImdb").value = "";
    document.getElementById("bulkMaxImdb").value = "";
    document.getElementById("bulkSortSelect").value = "imdb_desc";
    document.getElementById("bulkShowHiddenCheckbox").checked = false;
    renderBulkAddMoviesGrid();
  });

  function updateToggleAllButtonState() {
    const containers = document.querySelectorAll(".group-movies-container");
    const toggleBtn = document.getElementById("toggleAllGroupsBtn");
    if (containers.length === 0 || !toggleBtn) return;

    const allCollapsed = Array.from(containers).every(el => el.classList.contains("collapsed"));
    if (allCollapsed) {
      toggleBtn.innerText = "📂 Tümünü Aç";
    } else {
      toggleBtn.innerText = "📁 Tümünü Kapat";
    }
  }

  function toggleAllGroups() {
    const wrappers = document.querySelectorAll(".group-section-wrapper");
    const toggleBtn = document.getElementById("toggleAllGroupsBtn");
    if (wrappers.length === 0 || !toggleBtn) return;

    const containers = Array.from(wrappers).map(w => w.querySelector(".group-movies-container")).filter(Boolean);
    const isCurrentlyAllCollapsed = containers.every(el => el.classList.contains("collapsed"));

    if (isCurrentlyAllCollapsed) {
      wrappers.forEach(w => {
        const mc = w.querySelector(".group-movies-container");
        const icon = w.querySelector(".group-collapse-icon");
        if (mc) {
          mc.classList.remove("collapsed");
          populateGroupMoviesContainer(mc, w.dataset.groupKey, true);
        }
        if (icon) icon.innerText = "▼";
      });
      toggleBtn.innerText = "📁 Tümünü Kapat";
    } else {
      wrappers.forEach(w => {
        const mc = w.querySelector(".group-movies-container");
        const icon = w.querySelector(".group-collapse-icon");
        if (mc) {
          mc.classList.add("collapsed");
          populateGroupMoviesContainer(mc, w.dataset.groupKey, false);
        }
        if (icon) icon.innerText = "▶";
      });
      toggleBtn.innerText = "📂 Tümünü Aç";
    }
    applyPersistentHighlight();
  }

  window.addEventListener("DOMContentLoaded", () => {
    const editorBtn = document.getElementById("editorLinkBtn");
    if (editorBtn) {
      const currentProtocol = window.location.protocol;
      if (currentProtocol === "file:") {
        editorBtn.href = "./film_editor.html";
      } else {
        editorBtn.href = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, "/") + "film_editor.html";
      }
    }
  });

  document.getElementById("toggleViewModeBtn").addEventListener("click", () => {
    toggleViewMode();
    renderMoviesPreservingScroll();
  });
  document.getElementById("goBtn").addEventListener("click", executeGoToId);
  document.getElementById("lastIdInput").addEventListener("keypress", (e) => {
    if (e.key === 'Enter') {
      executeGoToId();
    }
  });

  document.getElementById("toggleAllGroupsBtn").addEventListener("click", toggleAllGroups);

  document.getElementById("recentMoviesDropdown").addEventListener("change", (e) => {
    const selectedId = e.target.value;
    if (selectedId) {
      document.getElementById("searchInput").value = "";
      document.getElementById("domainFilter").value = "";
      document.getElementById("minYearRange").value = minGlobalYear;
      document.getElementById("maxYearRange").value = maxGlobalYear;
      updateYearSliderLabel();
      document.getElementById("countryFilter").value = "";
      document.getElementById("minDurationRange").value = minGlobalDuration;
      document.getElementById("maxDurationRange").value = maxGlobalDuration;
      updateDurationSliderLabel();
      document.getElementById("minImdbRange").value = 0;
      document.getElementById("maxImdbRange").value = 10;
      updateImdbSliderLabel();
      document.getElementById("minMyScoreRange").value = 0;
      document.getElementById("maxMyScoreRange").value = 10;
      updateMyScoreSliderLabel();

      sidebarSelectedGenreKeys.clear();
      document.getElementById("watchlistDropdown").value = "all";
      document.getElementById("showHiddenCheckbox").checked = false;

      activeRelationFilterSet = null;
      updateRelationBanner();

      document.getElementById("lastIdInput").value = selectedId;
      try {
        localStorage.setItem("last_clicked_movie_id", selectedId);
        saveStateToStorage();
      } catch (err) {}

      renderMovies(false, true);

      const idxInList = activeOrderedMovieIds.indexOf(String(selectedId));
      if (idxInList !== -1) {
        const targetPage = Math.floor(idxInList / PAGE_SIZE) + 1;
        if (targetPage !== currentPage) {
          currentPage = targetPage;
          renderMovies(false, true);
        }
      }

      if (sidebarMode === "genre_add") {
        loadMovieGenresIntoSidebar();
      }

      requestAnimationFrame(() => {
        scrollToMovie(selectedId, true);
      });
      e.target.value = "";
    }
  });

  function resetAllFilters() {
    document.getElementById("searchInput").value = "";
    document.getElementById("domainFilter").value = "";
    document.getElementById("minYearRange").value = minGlobalYear;
    document.getElementById("maxYearRange").value = maxGlobalYear;
    updateYearSliderLabel();
    document.getElementById("countryFilter").value = "";
    document.getElementById("minDurationRange").value = minGlobalDuration;
    document.getElementById("maxDurationRange").value = maxGlobalDuration;
    updateDurationSliderLabel();
    document.getElementById("minImdbRange").value = 0;
    document.getElementById("maxImdbRange").value = 10;
    updateImdbSliderLabel();
    document.getElementById("minMyScoreRange").value = 0;
    document.getElementById("maxMyScoreRange").value = 10;
    updateMyScoreSliderLabel();

    sidebarSelectedGenreKeys.clear();
    document.getElementById("watchlistDropdown").value = "all";
    document.getElementById("showHiddenCheckbox").checked = false;

    activeRelationFilterSet = null;
    updateRelationBanner();
    renderMovies(false);
    renderRecentDropdown();
  }

  document.getElementById("resetFiltersBtn").addEventListener("click", resetAllFilters);

  document.getElementById("exportDataBtn").addEventListener("click", exportUserData);
  document.getElementById("importDataBtn").addEventListener("click", () => {
    document.getElementById("importFileInput").click();
  });
  document.getElementById("importFileInput").addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      importUserData(e.target.files[0]);
      e.target.value = "";
    }
  });

  document.getElementById("searchInput").addEventListener("keypress", (e) => {
    if (e.key === 'Enter') {
      renderMovies(true);
    }
  });
  document.getElementById("searchBtn").addEventListener("click", () => {
    renderMovies(true);
  });

  document.getElementById("domainFilter").addEventListener("change", () => renderMovies(false));

  document.getElementById("minYearRange").addEventListener("input", () => {
    updateYearSliderLabel();
    renderMovies(false);
  });
  document.getElementById("maxYearRange").addEventListener("input", () => {
    updateYearSliderLabel();
    renderMovies(false);
  });

  document.getElementById("countryFilter").addEventListener("change", () => renderMovies(false));

  document.getElementById("minDurationRange").addEventListener("input", () => {
    updateDurationSliderLabel();
    renderMovies(false);
  });
  document.getElementById("maxDurationRange").addEventListener("input", () => {
    updateDurationSliderLabel();
    renderMovies(false);
  });

  document.getElementById("minImdbRange").addEventListener("input", () => {
    updateImdbSliderLabel();
    renderMovies(false);
  });
  document.getElementById("maxImdbRange").addEventListener("input", () => {
    updateImdbSliderLabel();
    renderMovies(false);
  });

  document.getElementById("minMyScoreRange").addEventListener("input", () => {
    updateMyScoreSliderLabel();
    renderMovies(false);
  });
  document.getElementById("maxMyScoreRange").addEventListener("input", () => {
    updateMyScoreSliderLabel();
    renderMovies(false);
  });

  document.getElementById("sortSelect1").addEventListener("change", () => renderMovies(false));
  document.getElementById("sortSelect2").addEventListener("change", () => renderMovies(false));
  document.getElementById("watchlistDropdown").addEventListener("change", () => {
    activeRelationFilterSet = null;
    updateRelationBanner();
    renderMovies(false);
  });
  document.getElementById("linkedGroupsSortSelect").addEventListener("change", () => renderMovies(false));
  document.getElementById("showHiddenCheckbox").addEventListener("change", () => {
    updateRelationBanner();
    renderMovies(false);
    renderRecentDropdown();
  });
  document.getElementById("clearRelationBtn").addEventListener("click", clearRelationFilter);

  initFilters();
  renderMovies(false);
</script>
</body>
</html>
"""

    import urllib.parse
    movies_json_str = json.dumps(details_js_list, ensure_ascii=False)
    encoded_movies_json = urllib.parse.quote(movies_json_str)

    final_html = html_template.replace("__MOVIES_JSON_PLACEHOLDER__", encoded_movies_json)
    final_html = final_html.replace("__COUNT_PLACEHOLDER__", str(len(details_js_list)))

    with open(input_prev_html, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f" -> '{input_prev_html}' başarıyla oluşturuldu.")
    print("=" * 65)

    try:
        import google.colab
        from google.colab import files
        files.download(input_prev_html)
        files.download(input_details)
    except ImportError:
        pass

if __name__ == "__main__":
    main()