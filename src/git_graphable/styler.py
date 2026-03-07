"""
Main entry point for graph styling and export.
"""

from graphable import Graph
from graphable.views import (
    D2StylingConfig,
    GraphvizStylingConfig,
    MermaidStylingConfig,
    export_topology_d2,
    export_topology_d2_image,
    export_topology_graphviz_dot,
    export_topology_graphviz_image,
    export_topology_mermaid_image,
    export_topology_mermaid_mmd,
)

from .core import Engine, GitCommit, GitLogConfig
from .styling.base import get_contrast_color, get_node_text
from .styling.generic import get_generic_link_style, get_generic_style
from .styling.html import export_html
from .styling.mermaid import mermaid_link_style, mermaid_style

# Re-export core utilities for external usage
__all__ = ["export_graph", "get_node_text", "get_contrast_color"]


def export_graph(
    graph: Graph[GitCommit],
    output_path: str,
    config: GitLogConfig,
    engine: Engine = Engine.MERMAID,
    as_image: bool = False,
) -> None:
    """Export the graph to a file using the specified engine."""

    def label_fnc(n):
        return get_node_text(n, config.date_format, engine)

    def node_ref_fnc(n):
        return n.reference.hash

    if engine == Engine.MERMAID:
        styling_config = MermaidStylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_text_fnc=label_fnc,
            node_style_fnc=lambda n: mermaid_style(n, config),
            link_style_fnc=lambda n, sn: mermaid_link_style(n, sn, config),
        )
        fnc = export_topology_mermaid_image if as_image else export_topology_mermaid_mmd
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.GRAPHVIZ:
        styling_config = GraphvizStylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_attr_fnc=lambda n: get_generic_style(n, Engine.GRAPHVIZ, config),
            edge_attr_fnc=lambda n, sn: get_generic_link_style(
                n, sn, Engine.GRAPHVIZ, config
            ),
        )
        fnc = (
            export_topology_graphviz_image if as_image else export_topology_graphviz_dot
        )
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.D2:
        styling_config = D2StylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_style_fnc=lambda n: get_generic_style(n, Engine.D2, config),
            edge_style_fnc=lambda n, sn: get_generic_link_style(
                n, sn, Engine.D2, config
            ),
        )
        fnc = export_topology_d2_image if as_image else export_topology_d2
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.HTML:
        export_html(graph, output_path, config, node_ref_fnc)
    else:
        graph.write(output_path)
