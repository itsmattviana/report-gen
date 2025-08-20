from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
from load_data import load_feedbacks

# Ajuste aqui o modelo que você prefere usar.
# Ex.: "gpt-5" (ou "gpt-5-mini"), e se necessário troque de volta para "gpt-4o-mini".
MODEL_NAME = "gpt-5"

ADVANCED_PROMPT_TMPL = """You are a data analyst. Generate a monthly business report from the customer feedback dataset below.

Rules:
1) Summarize key insights in sections: Positive, Negative, Neutral (bulleted lists).
2) Provide a Markdown table with counts per category (columns: Category, Count, %).
3) Highlight the top 3 recurring issues (one line each, bold the keyword).
4) Suggest 2 actionable recommendations for management (each starting with a verb).
5) Keep the tone concise and executive-ready.
6) Output strictly in Markdown with headers (##) and a final **TL;DR** line.

Dataset (one per line as 'id: text'):
{{DATASET}}
"""

def serialize_dataset(df: pd.DataFrame) -> str:
    return "\n".join(f"{row.id}: {row.feedback}" for row in df.itertuples())

def main():
    load_dotenv()
    client = OpenAI()

    # 1) Carregar dados
    df = load_feedbacks("data/feedbacks.csv")

    # 2) Serializar dataset em linhas compactas
    dataset_str = serialize_dataset(df)

    # 3) Montar prompt avançado
    prompt = ADVANCED_PROMPT_TMPL.replace("{{DATASET}}", dataset_str)

    # 4) Chamar o modelo (temperatura baixa para mais consistência)
    resp = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
    )

    # 5) Extrair e salvar a resposta em Markdown
    report_md = resp.output_text
    out = Path("outputs/advanced.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_md, encoding="utf-8")
    print(f"[OK] Relatório avançado salvo em {out.resolve()}")

if __name__ == "__main__":
    main()


