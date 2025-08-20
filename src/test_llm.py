from dotenv import load_dotenv
from openai import OpenAI

def main():
    load_dotenv()                 # lê OPENAI_API_KEY do .env
    client = OpenAI()
    resp = client.responses.create(
        model="gpt-4o-mini",
        input="Responda apenas com a palavra: OK"
    )
    print(resp.output_text)

if __name__ == "__main__":
    main()
