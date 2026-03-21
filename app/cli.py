from app.graph.graph import build_graph


def main():
    app = build_graph()
    result = app.invoke({"question": "What is agent memory?"})
    print(result["generation"])


if __name__ == "__main__":
    main()
