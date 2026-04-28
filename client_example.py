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
    api = PrologService(str(Path("knowledge/context2.pl")))

    response = api.handle_request({
        "action": "raw_query",
        "params": {"query": "vehicle_type(ktw_c, Type)"}
    })
    print("vehicle_type(ktw_c, Type):", response)

    response = api.handle_request({
        "action": "raw_query",
        "params": {"query": "ktw_compliant(ktw_c, typ_c)"}
    })
    print("ktw_compliant(ktw_c, typ_c):", response)

    request_with_sld_visualization(api, "ktw_compliant(ktw_c, Type)", "sld_ktw_c.svg")


if __name__ == "__main__":
    main()
