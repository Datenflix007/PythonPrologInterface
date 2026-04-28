from pathlib import Path
from prolog_api import PrologService
from prolog_api.sld_rendering import save_sld_tree_svg, open_svg_in_browser


def request_with_sld_visualization(api: PrologService, query: str, output_path: str = "sld_tree.svg") -> None:
    response = api.handle_request({
        "action": "explain_query",
        "params": {"query": query}
    })

    print("=== SLD-Resolutionserklärung ===")
    if response.get("ok"):
        tree = response["data"]["tree"]
        svg_path = save_sld_tree_svg(tree, output_path, title=f"SLD Tree: {query}")
        print("SVG gespeichert unter:", svg_path)
        open_svg_in_browser(svg_path)
    else:
        print("Fehler beim Erstellen der Erklärung:", response.get("error"))


def main():
    knowledge_file = Path("knowledge/context2.pl")
    api = PrologService(knowledge_file)

    #response = api.handle_request({
    #    "action": "raw_query",
    #    "params": {"query": "classify_vehicle(ktw_c, Type)"}
    #})
    #print("classify_vehicle(ktw_c, Type):", response)

    #response = api.handle_request({
    #    "action": "raw_query",
    #    "params": {"query": "equipped_for(ktw_c, emergency_service)"}
    #})
    #print("equipped_for(ktw_c, emergency_service):", response)

    query = "ktw_norm([ktw_a, ktw_b, ktw_c], Norm)"
    response = api.handle_request({
        "action": "raw_query",
        "params": {"query": query}
    })
    print("ktw_norm(Type, Norm) - long:", response)

    response = api.handle_request({
        "action": "raw_query",
        "params": {"query": query, "mode": "short"}
    })
    print("ktw_norm(Type, Norm) - short:", response)

    request_with_sld_visualization(api, query, "sld_tree.svg")


if __name__ == "__main__":
    main()
