from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
from load_data import load_feedbacks

# Prompt básico sem estrutura
BASIC_PROMPT = "Write a report summarizing customer feedback."

def build_context_table(df: pd.DataFrame) -> str:
    """
    Transforma o DataFrame em linhas simples no formato 'id: feedback'.
    """
    return "\n".join(f"{row.id}: {row.feedback}" for row in df.itertuples())

def main():
    load_dotenv()
    client = OpenAI()

    # Carregar dataset
    df = load_feedbacks("data/feedbacks.csv")
    context = build_context_table(df)

    # Montar prompt final
    user_input = (
        f"{BASIC_PROMPT}\n\n"
        f"Data (one per line as 'id: text'):\n{context}\n"
    )

    # Chamada ao modelo
    resp = client.responses.create(
        model="gpt-4o-mini",   # pode trocar por gpt-5 se quiser
        input=user_input
    )

    # Extrair resposta
    report_md = resp.output_text

    # Salvar resultado em arquivo
    out = Path("outputs/basic.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_md, encoding="utf-8")
    print(f"[OK] Relatório básico salvo em {out.resolve()}")

if __name__ == "__main__":
    main()

