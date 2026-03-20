from dotenv import load_dotenv

load_dotenv()

from graph.graph import app

if __name__ == "__main__":
    result = app.invoke({"question": "What is agent memory?"})
    print(result["generation"])
