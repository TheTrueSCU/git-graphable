"""
HTML and JS templates for interactive graphs.
"""

LEGEND_CSS = """
        .legend {
            position: absolute;
            bottom: 20px;
            left: 10px;
            z-index: 999;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-size: 0.85em;
            max-height: 50vh;
            overflow-y: auto;
            min-width: 180px;
        }
        .legend h4 { margin: 0 0 8px 0; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
        .legend-section { margin-bottom: 12px; }
        .legend-section-title { font-weight: bold; margin-bottom: 6px; display: block; color: #555; font-size: 0.9em; }
        .legend-item { display: flex; align-items: center; margin-bottom: 4px; cursor: pointer; padding: 2px 4px; border-radius: 3px; }
        .legend-item:hover { background: #f0f0f0; }
        .legend-color { width: 12px; height: 12px; border-radius: 2px; margin-right: 8px; border: 1px solid #999; flex-shrink: 0; }
        .legend-label { flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .legend-input { margin-left: 10px; flex-shrink: 0; }
    </style>"""

DAGRE_SCRIPTS = """
    <script src="https://unpkg.com/dagre@0.7.4/dist/dagre.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
</head>"""

LEGEND_HTML = """
    <div class="legend" id="legend">
        <h4>Git Graph</h4>
        <div class="legend-section">
            <span class="legend-section-title">Color Mode</span>
            {fill_modes}
        </div>
        <div class="legend-section">
            <span class="legend-section-title">Overlays</span>
            {overlays}
        </div>
    </div>
    <div id="cy"></div>"""


def get_toggle_logic(tag_to_style_json, tags):
    """Return the JS logic for toggling highlights."""
    return f"""
        var tagStyles = {tag_to_style_json};
        var activeMode = 'none';
        var disabledOverlays = new Set();
        var fillTags = [
            "{tags.PR_OPEN.value}", 
            "{tags.PR_MERGED.value}", 
            "{tags.PR_CLOSED.value}", 
            "{tags.PR_DRAFT.value}"
        ];

        function syncOverlayState() {{
            disabledOverlays.clear();
            document.querySelectorAll('.legend-input[type="checkbox"]').forEach(function(cb) {{
                var tag = cb.id.replace('overlay-', '');
                if (!cb.checked) {{ disabledOverlays.add(tag); }}
            }});
        }}

        function setMode(mode, event) {{
            activeMode = mode;
            var radio = document.getElementById('mode-' + mode);
            if (radio) radio.checked = true;
            applyStyles();
        }}

        function toggleOverlay(tag, event) {{
            var checkbox = document.getElementById('overlay-' + tag);
            if (event && event.target !== checkbox) {{ checkbox.checked = !checkbox.checked; }}
            if (checkbox.checked) {{ disabledOverlays.delete(tag); }} 
            else {{ disabledOverlays.add(tag); }}
            applyStyles();
        }}

        function applyStyles() {{
            if (typeof cyGraph === 'undefined') return;
            
            // 1. Reset base styles
            cyGraph.nodes().style({{
                'background-color': '#007bff', 'color': '#333', 'border-width': 0,
                'border-color': 'transparent', 'shape': 'ellipse', 'opacity': 1
            }});
            cyGraph.edges().style({{ 'line-color': '#ccc', 'width': 2, 'line-style': 'solid', 'opacity': 1 }});

            // 2. Apply Fill Mode
            if (activeMode === 'authors') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{tags.AUTHOR_HIGHLIGHT.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{tags.AUTHOR_HIGHLIGHT.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'distance') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{tags.DISTANCE_COLOR.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{tags.DISTANCE_COLOR.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'stale') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{tags.STALE_COLOR.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{tags.STALE_COLOR.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'pr_status') {{
                fillTags.forEach(function(tag) {{
                    if (tagStyles[tag]) {{ cyGraph.nodes().filter(n => (n.data('tags') || []).includes(tag)).style(tagStyles[tag]); }}
                }});
            }}

            // 3. Apply Overlays (Skipping Fill Tags to prevent conflicts)
            Object.keys(tagStyles).forEach(function(tag) {{
                if (fillTags.includes(tag) || tag === '{tags.PR_STATUS.value}') return;
                if (tag.startsWith('{tags.AUTHOR_HIGHLIGHT.value}') || tag.startsWith('{tags.DISTANCE_COLOR.value}') || tag.startsWith('{tags.STALE_COLOR.value}')) return;
                if (disabledOverlays.has(tag)) return;
                
                var selector = (tag.includes('edge') || tag.includes('highlight') || tag.includes('logical_merge') || tag.includes('long_running_edge')) ? 'edge' : 'node';
                cyGraph.elements(selector).filter(el => (el.data('tags') || []).includes(tag)).style(tagStyles[tag]);
            }});
            
            // 4. Re-apply selection style
            cyGraph.elements(':selected').style({{ 'border-width': '4px', 'border-color': '#ff0', 'background-color': '#0056b3' }});
        }}

        function initStyles() {{
            if (typeof cyGraph !== 'undefined') {{ syncOverlayState(); applyStyles(); }} 
            else {{ setTimeout(initStyles, 50); }}
        }}
        initStyles();
        """
