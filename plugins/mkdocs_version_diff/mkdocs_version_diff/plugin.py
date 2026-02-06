from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Set


def _version_key(version: str):
    """Split version into ints and strings for natural-ish sorting."""
    return [int(x) if x.isdigit() else x for x in re.split(r"[\\.-]", version)]


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        if value in seen:
            continue
        out.append(value)
        seen.add(value)
    return out


class VersionDiffPlugin(BasePlugin):
    """
    - Generates compare pages under <site_dir>/compare/<rel_path>. When published via mike,
      these are served under /<version>/compare/<page>.
    - Injects a floating 'Compare Versions' button that, on click, computes the correct
      prefix at runtime, resolving aliases like 'latest' using versions.json when needed.
    """

    config_scheme = (
        ("enabled", config_options.Type(bool, default=True)),
        ("button_text", config_options.Type(str, default="📊 Compare Versions")),
        ("default_compare_versions", config_options.Type(int, default=2)),
        ("versions", config_options.Type(list, default=None)),
        ("versions_json_path", config_options.Type(str, default=None)),
        ("fetch_gh_pages", config_options.Type(bool, default=False)),
        ("current_version", config_options.Type(str, default=None)),
        ("fallback_to_git_tags", config_options.Type(bool, default=False)),
        ("git_tag_pattern", config_options.Type(str, default=r"^v?\\d+\\.\\d+\\.\\d+.*$")),
    )

    def __init__(self):
        self.versions = []
        self.versions_data = []
        self.alias_map = {}  # alias -> version
        self.site_dir = None
        self.current_version = None

    def on_config(self, config):
        if not self.config["enabled"]:
            return config

        self.site_dir = config["site_dir"]

        self.current_version = (
            self.config.get("current_version")
            or os.environ.get("MIKE_VERSION")
            or os.environ.get("MKDOCS_VERSION")
            or self._infer_current_version_from_pyproject()
        )

        # If user configured versions explicitly, use them
        if self.config.get("versions"):
            self.versions = list(self.config["versions"])
            if self.current_version and self.current_version not in self.versions:
                self.versions.append(self.current_version)
            self.versions = sorted(_dedupe_keep_order(self.versions), key=_version_key)
            print(f"✓ Using manually configured versions: {', '.join(self.versions)}")
            return config

        versions_data = self._load_versions_data(config)
        if versions_data:
            self._apply_versions_data(versions_data)

        if self.current_version and self.current_version not in self.versions:
            self.versions.append(self.current_version)

        self.versions = sorted(_dedupe_keep_order([v for v in self.versions if v]), key=_version_key)

        if self.versions:
            detected = ", ".join(self.versions)
            if self.current_version:
                print(f"✓ Detected versions (current={self.current_version}): {detected}")
            else:
                print(f"✓ Detected versions: {detected}")
            return config

        print(
            "⚠ Warning: Could not auto-detect versions. "
            "Set `plugins.version-diff.versions` or `plugins.version-diff.versions_json_path`."
        )
        self.versions = []
        self.alias_map = {}
        return config

    def on_files(self, files, config):
        return files

    def on_post_page(self, output, page, config):
        """
        Inject the floating compare button. The click handler computes the correct
        base prefix at runtime, including resolving 'latest' to its backing version.
        """
        if not self.config["enabled"] or not self.versions:
            return output

        # Defensive checks
        page_url = (getattr(page, "url", "") or "").lstrip("/")
        if page_url.startswith("compare/") or "/compare/" in page_url:
            return output
        if 'id="version-compare-link"' in output:
            return output

        dest_url = getattr(page, "url", "") or ""              # directory form "flavors_intro/" or "" for home
        dest_file = getattr(page.file, "dest_path", "") or ""  # "flavors_intro/index.html" or "index.html"
        button_html = self._generate_button_html(dest_url, dest_file)

        if "</body>" in output:
            output = output.replace("</body>", button_html + "</body>", 1)
        return output

    def on_post_build(self, config):
        """
        Generate compare pages under site_dir/compare/<rel_path>.
        On mike builds, this becomes /<version>/compare/<page>.
        """
        if not self.config["enabled"] or not self.versions:
            print("⚠ No versions found, skipping comparison page generation")
            return

        default_versions = self._get_default_compare_versions()
        if len(default_versions) < 2:
            print("⚠ Need at least 2 versions for comparison")
            return

        site_dir = config["site_dir"]
        print(f"✓ Generating comparison pages in: {site_dir}")
        print(f"✓ Default comparison versions: {', '.join(default_versions)}")

        page_count = 0
        for root, dirs, files in os.walk(site_dir):
            # Skip anything already under compare/
            if os.path.relpath(root, site_dir).split(os.sep)[0] == "compare":
                continue

            for file in files:
                if not file.endswith(".html"):
                    continue

                rel_path = os.path.relpath(os.path.join(root, file), site_dir)
                if rel_path.startswith("compare/") or rel_path == "versions.json":
                    continue

                self._generate_compare_page(site_dir, rel_path, default_versions)
                page_count += 1

        print(f"✓ Generated {page_count} comparison pages")

    # --------------------------
    # Helpers
    # --------------------------

    def _get_default_compare_versions(self):
        n = int(self.config.get("default_compare_versions", 2))
        if len(self.versions) < 2:
            return []

        sorted_versions = sorted(_dedupe_keep_order(self.versions), key=_version_key)
        if self.current_version and self.current_version in sorted_versions:
            idx = sorted_versions.index(self.current_version)
            end = idx + 1
            start = max(0, end - n)
            subset = sorted_versions[start:end]
            if len(subset) >= 2:
                return subset

        return sorted_versions[-n:] if len(sorted_versions) >= n else sorted_versions

    def _generate_button_html(self, dest_url: str, dest_file: str) -> str:
        """
        Render a root-fixed button. The click handler determines the correct
        version prefix at runtime, resolves 'latest' via versions.json if needed,
        and navigates to <prefix>/compare/<dest_url>. The compare page itself uses
        dest_file to fetch HTML from each version.
        """
        button_text = self.config["button_text"]
        versions_sorted = sorted(self.versions, key=_version_key)
        alias_map_json = json.dumps(self.alias_map or {})
        versions_json = json.dumps(versions_sorted)

        return f'''
<style>
#version-compare-link {{
    position: fixed;
    top: 88px;
    right: 24px;
    z-index: 1000;
    background: var(--md-primary-fg-color, #2196F3);
    color: var(--md-primary-bg-color, #fff) !important;
    border-radius: var(--md-button-border-radius, 4px);
    font-size: 14px;
    font-weight: 500;
    box-shadow: var(--md-shadow-z2, 0 2px 8px rgba(0,0,0,0.2));
    transition: var(--md-button-transition, all 0.2s);
    padding: 0;
    border: none;
    text-decoration: none;
    display: inline-block;
}}
#version-compare-link .md-button-content {{
    padding: 10px 20px;
    display: block;
}}
#version-compare-link:hover {{
    background: var(--md-primary-fg-color--light, #42a5f5);
    box-shadow: var(--md-shadow-z3, 0 4px 12px rgba(0,0,0,0.3));
    transform: translateY(-2px);
}}
</style>
<a href="#" id="version-compare-link"
   class="md-button"
   data-dest="{dest_url}"
   data-dest-file="{dest_file}"
   data-versions='{versions_json}'
   data-alias-map='{alias_map_json}'>
  <span class="md-button-content">{button_text}</span>
</a>
<script>
(function() {{
  const link = document.getElementById('version-compare-link');
  if (!link) return;

  function pathParts() {{
    return window.location.pathname.split('/').filter(Boolean);
  }}

  function ensureTrailingSlash(path) {{
    return path.endsWith('/') ? path : (path + '/');
  }}

  // Derive the "root" directory for the current page from MkDocs' known outputs:
  // - destUrl is directory form like "flavors_intro/" (use_directory_urls=True)
  // - destFile is file form like "flavors_intro/index.html"
  //
  // This avoids hard-coding "/" and keeps deployments working under arbitrary bases
  // like /weave/dev/.../StudyWeaver/.
  function deriveRootFromCurrentPage(destUrl, destFile) {{
    const path = window.location.pathname;
    if (destUrl && path.endsWith(destUrl)) {{
      return ensureTrailingSlash(path.slice(0, path.length - destUrl.length));
    }}
    if (destFile && path.endsWith(destFile)) {{
      return ensureTrailingSlash(path.slice(0, path.length - destFile.length));
    }}
    // Best-effort directory fallback.
    if (path.endsWith('/')) return path;
    return ensureTrailingSlash(path.replace(/[^/]*$/, ''));
  }}

  function baseAndPrefixFromRoot(root, versions, aliasMap) {{
    const parts = root.split('/').filter(Boolean);
    const last = parts.length ? parts[parts.length - 1] : '';

    // If the last segment looks like a version/alias, treat it as the "prefix".
    if (versions.includes(last) || aliasMap[last] || last === 'latest') {{
      const baseParts = parts.slice(0, -1);
      const base = '/' + (baseParts.length ? (baseParts.join('/') + '/') : '');
      return {{ base, prefix: last }};
    }}

    // Otherwise we're at the docs base (no explicit version in URL).
    return {{ base: ensureTrailingSlash(root), prefix: '' }};
  }}

  link.addEventListener('click', async function(ev) {{
    ev.preventDefault();
    const destUrl = link.dataset.dest || '';        // e.g. "flavors_intro/" or ""
    const destFile = link.dataset.destFile || '';   // e.g. "flavors_intro/index.html"

    let versions = [];
    let aliasMap = {{}};
    try {{ versions = JSON.parse(link.dataset.versions || '[]'); }} catch {{ versions = []; }}
    try {{ aliasMap = JSON.parse(link.dataset.aliasMap || '{{}}'); }} catch {{ aliasMap = {{}}; }}

    const root = deriveRootFromCurrentPage(destUrl, destFile);
    const {{ base, prefix }} = baseAndPrefixFromRoot(root, versions, aliasMap);

    // Prefer the concrete version directory when possible (more robust than relying on alias dirs
    // like "latest/" being present in every static export).
    const newest = versions.length ? versions[versions.length - 1] : '';
    const defaultVersion = aliasMap['latest'] || newest || '';
    const targetVersion = (versions.includes(prefix) ? prefix : (aliasMap[prefix] || defaultVersion));
    if (!targetVersion) return;

    // Navigate to the directory URL for compare, not the file path.
    const target = base + targetVersion + '/compare/' + destUrl;
    window.location.assign(target);
  }});
}})();
</script>
'''

    def _generate_compare_page(self, site_dir: str, rel_path: str, default_versions):
        if len(default_versions) < 2:
            return

        compare_dir = os.path.join(site_dir, "compare", os.path.dirname(rel_path))
        os.makedirs(compare_dir, exist_ok=True)

        compare_html = self._generate_compare_html(rel_path, default_versions)
        compare_file = os.path.join(site_dir, "compare", rel_path)

        with open(compare_file, "w", encoding="utf-8") as f:
            f.write(compare_html)

    def _generate_compare_html(self, page_path: str, versions) -> str:
        """
        page_path is the HTML path relative to the site's root,
        for example 'flavors_intro/index.html' or 'index.html'.
        """
        old_version = versions[-2]
        new_version = versions[-1]
        version_options = "".join(
            [f'<option value="{v}">{v}</option>' for v in sorted(self.versions, key=_version_key)]
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Compare Versions</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}

    .header {{
      position: sticky;
      top: 0;
      background: white;
      border-bottom: 2px solid #ddd;
      padding: 15px 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      z-index: 1000;
      display: flex;
      align-items: center;
      gap: 15px;
      flex-wrap: wrap;
    }}

    .title {{ font-size: 18px; font-weight: 600; flex: 1; }}

    .view-toggle {{
      display: flex;
      gap: 5px;
      background: #f0f0f0;
      padding: 4px;
      border-radius: 4px;
    }}

    .view-toggle button {{
      padding: 8px 16px;
      background: transparent;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      color: #555;
    }}

    .view-toggle button.active {{
      background: white;
      color: #333;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}

    select {{
      padding: 8px 12px;
      border: 2px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      background: white;
      cursor: pointer;
    }}

    .back-link {{
      padding: 8px 16px;
      background: #2196F3;
      color: white;
      text-decoration: none;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
    }}

    .container {{
      display: flex;
      height: calc(100vh - 70px);
    }}

    .pane {{
      flex: 1;
      display: flex;
      flex-direction: column;
      border-right: 2px solid #ddd;
    }}

    .pane:last-child {{ border-right: none; }}

    .pane-header {{
      background: #f8f9fa;
      padding: 12px 20px;
      border-bottom: 2px solid #ddd;
      font-weight: 600;
    }}

    .pane-content {{ flex: 1; position: relative; }}
    iframe {{ width: 100%; height: 100%; border: none; }}

    .loading {{
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(255,255,255,0.9);
      display: flex; align-items: center; justify-content: center;
    }}

    .inline-view {{ display: block; height: calc(100vh - 70px); overflow: auto; }}
    .side-view {{ display: none; }}

    .diff-summary {{
      background: #f0f8ff;
      border-bottom: 2px solid #b3d9ff;
      padding: 15px 20px;
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
      font-size: 14px;
      position: sticky;
      top: 0;
      z-index: 100;
    }}

    .inline-versions {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      padding: 20px;
      max-width: 1400px;
      margin: 0 auto;
    }}

    .inline-block {{
      border: 2px solid #ddd;
      border-radius: 8px;
      overflow: hidden;
    }}

    .inline-block-header {{
      background: #f8f9fa;
      padding: 12px 20px;
      font-weight: 600;
      border-bottom: 2px solid #ddd;
    }}

    .inline-block-content {{ height: 600px; position: relative; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">📊 Compare: {page_path}</div>
    <div class="view-toggle">
      <button id="btn-inline" class="active" type="button">Inline Diff</button>
      <button id="btn-side" type="button">Side-by-Side</button>
    </div>
    <label>Old: <select id="old">{version_options}</select></label>
    <label>New: <select id="new">{version_options}</select></label>
    <a href="#" class="back-link" onclick="history.back(); return false;">← Back</a>
  </div>

  <div class="container side-view" id="side-view">
    <div class="pane">
      <div class="pane-header" id="h1">Old</div>
      <div class="pane-content">
        <div class="loading" id="l1">Loading...</div>
        <iframe id="f1"></iframe>
      </div>
    </div>
    <div class="pane">
      <div class="pane-header" id="h2">New</div>
      <div class="pane-content">
        <div class="loading" id="l2">Loading...</div>
        <iframe id="f2"></iframe>
      </div>
    </div>
  </div>

  <div class="inline-view" id="inline-view">
    <div class="diff-summary">
      <span><strong id="inline-old">Old</strong> → <strong id="inline-new">New</strong></span>
      <span id="stats">Calculating...</span>
    </div>
    <div class="inline-versions">
      <div class="inline-block">
        <div class="inline-block-header">
          <span id="inline-h2">New</span> (Current with inline diff)
        </div>
        <div class="inline-block-content">
          <iframe id="inline-f2"></iframe>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/diff_match_patch/20121119/diff_match_patch.js"></script>
  <script>
    // Derive site base and current prefix from the URL, preserving subpaths like /repo/.
    function pathParts() {{ return window.location.pathname.split('/').filter(Boolean); }}

    function locatePrefix(versions) {{
      const parts = pathParts();
      for (let i = 0; i < parts.length; i++) {{
        if (versions.includes(parts[i]) || parts[i] === 'latest') return {{ idx: i, value: parts[i] }};
      }}
      return {{ idx: -1, value: '' }};
    }}

    function siteBase(versions) {{
      const parts = pathParts();

      // If we are on .../<prefix>/compare/..., base should be everything before <prefix>.
      const compareIdx = parts.indexOf('compare');
      if (compareIdx > 0) {{
        const prefix = parts[compareIdx - 1];
        if (versions.includes(prefix) || prefix === 'latest') {{
          const baseParts = parts.slice(0, compareIdx - 1);
          return '/' + (baseParts.length ? (baseParts.join('/') + '/') : '');
        }}
      }}

      const {{ idx }} = locatePrefix(versions);
      if (idx <= 0) return '/';
      return '/' + parts.slice(0, idx).join('/') + '/';
    }}

    const PATH = "{page_path}"; // e.g. flavors_intro/index.html
    const versions = {json.dumps(sorted(self.versions, key=_version_key))};
    const BASE = siteBase(versions); // includes trailing slash if non-root

    let currentView = "inline";

    const old = document.getElementById("old");
    const newv = document.getElementById("new");
    const f1 = document.getElementById("f1");
    const f2 = document.getElementById("f2");
    const h1 = document.getElementById("h1");
    const h2 = document.getElementById("h2");
    const l1 = document.getElementById("l1");
    const l2 = document.getElementById("l2");
    const btnSide = document.getElementById("btn-side");
    const btnInline = document.getElementById("btn-inline");
    const sideView = document.getElementById("side-view");
    const inlineView = document.getElementById("inline-view");

    old.value = "{old_version}";
    newv.value = "{new_version}";

    function switchView(view) {{
      currentView = view;
      if (view === "side") {{
        sideView.style.display = "flex";
        inlineView.style.display = "none";
        btnSide.classList.add("active");
        btnInline.classList.remove("active");
        loadSideBySide();
      }} else {{
        sideView.style.display = "none";
        inlineView.style.display = "block";
        btnSide.classList.remove("active");
        btnInline.classList.add("active");
        loadInline();
      }}
    }}

    btnSide.onclick = function() {{ switchView("side"); }};
    btnInline.onclick = function() {{ switchView("inline"); }};

    function loadSideBySide() {{
      const oldVer = old.value;
      const newVer = newv.value;

      h1.textContent = "Old: " + oldVer;
      h2.textContent = "New: " + newVer;

      l1.style.display = "flex";
      l2.style.display = "flex";

      f1.src = BASE + oldVer + "/" + PATH;
      f2.src = BASE + newVer + "/" + PATH;

      f1.onload = function() {{ l1.style.display = "none"; }};
      f2.onload = function() {{ l2.style.display = "none"; }};
    }}

    function loadInline() {{
      const oldVer = old.value;
      const newVer = newv.value;

      document.getElementById("inline-old").textContent = oldVer;
      document.getElementById("inline-new").textContent = newVer;
      document.getElementById("inline-h2").textContent = newVer;

      const inlineIframe = document.getElementById("inline-f2");
      inlineIframe.src = BASE + newVer + "/" + PATH;

      inlineIframe.onload = () => {{
        calculateDiffBlockwise(oldVer, newVer);
      }};
    }}

    function diffTextNodes(oldNodes, newNodes) {{
      const dmp = new diff_match_patch();
      let adds = 0, dels = 0;

      for (let i = 0; i < newNodes.length; i++) {{
        const newNode = newNodes[i];
        const oldNode = oldNodes[i];
        if (!newNode || !oldNode) continue;

        let newChildren = Array.from(newNode.childNodes);
        let oldChildren = Array.from(oldNode.childNodes);

        for (let j = 0; j < newChildren.length; j++) {{
          const newChild = newChildren[j];
          const oldChild = oldChildren[j];
          if (!newChild || !oldChild) continue;

          if (newChild.nodeType === Node.TEXT_NODE && oldChild.nodeType === Node.TEXT_NODE) {{
            const text1 = oldChild.textContent;
            const text2 = newChild.textContent;
            const blockDiffs = dmp.diff_main(text1, text2);
            dmp.diff_cleanupSemantic(blockDiffs);

            let html = "";
            blockDiffs.forEach(([op, txt]) => {{
              const words = txt.trim().split(/\\s+/).filter(w => w.length > 0);
              if (op === 1) adds += words.length;
              if (op === -1) dels += words.length;
              if (!txt) return;
              if (op === 1) {{
                html += '<span class="diff-added">' + escapeHtml(txt) + '</span>';
              }} else if (op === -1) {{
                html += '<span class="diff-deleted">' + escapeHtml(txt) + '</span>';
              }} else {{
                html += escapeHtml(txt);
              }}
            }});
            const span = document.createElement("span");
            span.innerHTML = html;
            newNode.replaceChild(span, newChild);
          }}
        }}
      }}
      return {{adds, dels}};
    }}

    async function calculateDiffBlockwise(oldVer, newVer) {{
      const stats = document.getElementById("stats");
      stats.textContent = "Calculating...";

      try {{
        const [html1, html2] = await Promise.all([
          fetchHtml(oldVer),
          fetchHtml(newVer)
        ]);

        const doc1 = new DOMParser().parseFromString(html1, "text/html");
        const doc2 = document.getElementById("inline-f2").contentDocument || document.getElementById("inline-f2").contentWindow.document;

        const root1 = doc1.querySelector(".md-content__inner") || doc1.querySelector("article") || doc1.querySelector("main") || doc1.body;
        const root2 = doc2.querySelector(".md-content__inner") || doc2.querySelector("article") || doc2.querySelector("main") || doc2.body;

        const blocks1 = Array.from(root1.querySelectorAll("p, li, h1, h2, h3, h4, h5, h6"));
        const blocks2 = Array.from(root2.querySelectorAll("p, li, h1, h2, h3, h4, h5, h6"));

        const {{adds, dels}} = diffTextNodes(blocks1, blocks2);

        stats.innerHTML =
          '<span style="background:#d4edda;padding:4px 8px;border-radius:3px;">+' + adds + ' words</span> ' +
          '<span style="background:#f8d7da;padding:4px 8px;border-radius:3px;">-' + dels + ' words</span>';

        if (!doc2.getElementById("diff-inline-style")) {{
          const style = doc2.createElement("style");
          style.id = "diff-inline-style";
          style.textContent = `
            .diff-added {{
              font-weight: bold;
              background: #d4edda;
              color: #155724;
              padding: 1px 2px;
              border-radius: 2px;
            }}
            .diff-deleted {{
              text-decoration: line-through;
              background: #f8d7da;
              color: #721c24;
              padding: 1px 2px;
              border-radius: 2px;
            }}
          `;
          doc2.head.appendChild(style);
        }}
      }} catch (e) {{
        console.error(e);
        stats.textContent = "Error calculating diff";
      }}
    }}

    async function fetchHtml(ver) {{
      const url = BASE + ver + "/" + PATH;
      const res = await fetch(url, {{ cache: 'no-cache' }});
      return await res.text();
    }}

    function escapeHtml(text) {{
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }}

    old.onchange = function() {{ currentView === "inline" ? loadInline() : loadSideBySide(); }};
    newv.onchange = function() {{ currentView === "inline" ? loadInline() : loadSideBySide(); }};

    switchView("inline");
  </script>
</body>
</html>"""
        return html

    def _apply_versions_data(self, versions_data: List[Dict[str, Any]]) -> None:
        self.versions_data = versions_data
        versions: List[str] = []
        alias_map: Dict[str, str] = {}

        for entry in versions_data:
            ver = entry.get("version")
            if ver:
                versions.append(ver)
                for alias in entry.get("aliases", []) or []:
                    alias_map[str(alias)] = ver

        self.versions = versions
        self.alias_map = alias_map

    def _load_versions_data(self, config) -> Optional[List[Dict[str, Any]]]:
        versions_json_path = self.config.get("versions_json_path") or os.environ.get(
            "MKDOCS_VERSION_DIFF_VERSIONS_JSON_PATH"
        )

        if versions_json_path:
            data = self._try_read_versions_json_file(versions_json_path)
            if data:
                print(f"✓ Loaded versions.json from file: {versions_json_path}")
                return data
            print(f"⚠ Failed to load versions.json from file: {versions_json_path}")

        # Try to read versions.json from gh-pages via git (local ref, then remote ref).
        for ref in ("gh-pages", "origin/gh-pages"):
            data = self._try_read_versions_json_git_ref(ref)
            if data:
                print(f"✓ Loaded versions.json from git ref: {ref}")
                return data

        # Optional convenience: attempt to fetch gh-pages if requested, then retry.
        if self.config.get("fetch_gh_pages"):
            fetched = self._try_fetch_gh_pages()
            if fetched:
                data = self._try_read_versions_json_git_ref("gh-pages")
                if data:
                    print("✓ Loaded versions.json after fetching gh-pages")
                    return data

        if self.config.get("fallback_to_git_tags"):
            tag_versions = self._try_versions_from_git_tags()
            if tag_versions:
                print("✓ Derived versions from git tags")
                return [{"version": v, "aliases": []} for v in tag_versions]

        return None

    def _try_read_versions_json_file(self, path: str) -> Optional[List[Dict[str, Any]]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
            return data if isinstance(data, list) else None
        except Exception:
            return None

    def _try_read_versions_json_git_ref(self, ref: str) -> Optional[List[Dict[str, Any]]]:
        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:versions.json"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            return None

        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else None
        except Exception:
            return None

    def _try_fetch_gh_pages(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "fetch", "--depth=1", "origin", "gh-pages:gh-pages"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            return False
        return result.returncode == 0

    def _try_versions_from_git_tags(self) -> List[str]:
        pattern = re.compile(str(self.config.get("git_tag_pattern") or ""))
        try:
            result = subprocess.run(
                ["git", "tag", "--list"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            return []

        if result.returncode != 0:
            return []

        versions: List[str] = []
        for tag in (result.stdout or "").splitlines():
            tag = tag.strip()
            if not tag or not pattern.match(tag):
                continue
            versions.append(tag[1:] if tag.startswith("v") else tag)

        return sorted(_dedupe_keep_order(versions), key=_version_key)

    def _infer_current_version_from_pyproject(self) -> Optional[str]:
        pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
        if not os.path.exists(pyproject_path):
            return None

        try:
            import tomllib  # py311+

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            project = data.get("project") or {}
            if isinstance(project, dict) and project.get("version"):
                return str(project["version"])

            tool = data.get("tool") or {}
            poetry = tool.get("poetry") if isinstance(tool, dict) else None
            if isinstance(poetry, dict) and poetry.get("version"):
                return str(poetry["version"])
        except Exception:
            pass

        # Fallback: simple section-aware regex extraction without adding dependencies.
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            return None

        def find_version_in_section(section_name: str) -> Optional[str]:
            match = re.search(rf"^\\[{re.escape(section_name)}\\]\\s*$", text, re.MULTILINE)
            if not match:
                return None
            start = match.end()
            next_section = re.search(r"^\\[.*\\]\\s*$", text[start:], re.MULTILINE)
            end = start + next_section.start() if next_section else len(text)
            body = text[start:end]
            m = re.search(r'^version\\s*=\\s*["\\\']([^"\\\']+)["\\\']\\s*$', body, re.MULTILINE)
            return m.group(1) if m else None

        return find_version_in_section("project") or find_version_in_section("tool.poetry")
