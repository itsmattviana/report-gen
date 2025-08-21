from pathlib import Path
from collections import Counter, defaultdict
import re
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from load_data import load_feedbacks

MODEL_NAME = "gpt-4o-mini"  # troque se desejar

# --- 1) Regras determinísticas de classificação ---
POS_WORDS = [
    r"\bexcelente\b", r"\bótim[oa]\b", r"\bbom\b", r"\bboa\b",
    r"\brápid[ao]\b", r"\bimpecável\b", r"\bmoderno\b", r"\brecomendei\b",
    r"\bcusto[- ]?benefício\b", r"\bvoltarei a comprar\b", r"\bcurti\b"
]
NEG_WORDS = [
    r"\blento\b", r"\bdemorou?\b", r"\bcar[oa]\b", r"\bcaro\b", r"\bcar[a|o]\b",
    r"\bmenor que o esperado\b", r"\bdecepcionad[oa]\b", r"\bproblema\b",
    r"\bruim\b", r"\bpéssim[oa]\b", r"\bn[ãa]o resolutiv[oa]\b", r"\batendimento.*lento\b"
]

ISSUE_KEYS = {
    "Frete/Entrega": [r"\bfrete\b", r"\bentrega\b", r"\bdemorou?\b", r"\brápid[ao]\b"],
    "Tamanho/Ajuste": [r"\btamanho\b", r"\bmenor que o esperado\b"],
    "Suporte/Atendimento": [r"\batendimento\b", r"\bchat\b", r"\bsuporte\b", r"\blento\b", r"\bn[ãa]o resolutiv[oa]\b"],
    "Preço/Custo": [r"\bcar[oa]\b", r"\bcaro\b", r"\bcust[o|0]\b", r"\bcusto[- ]?benefício\b"],
    "Qualidade/Design": [r"\bqualidade\b", r"\bdesign\b", r"\bcomo nas fotos\b", r"\bimpecável\b"]
}

def classify_sentiment(text: str) -> str:
    t = text.lower()
    pos = any(re.search(p, t) for p in POS_WORDS)
    neg = any(re.search(p, t) for p in NEG_WORDS)
    if pos and not neg:
        return "Positive"
    if neg and not pos:
        return "Negative"
    # se houver sinais mistos ou nenhum, marque como Neutral
    return "Neutral"

def extract_issues(text: str) -> list[str]:
    t = text.lower()
    hits = []
    for issue, patterns in ISSUE_KEYS.items():
        if any(re.search(p, t) for p in patterns):
            hits.append(issue)
    return hits

def build_markdown_table(counts: dict[str, int], total: int) -> str:
    rows = []
    for cat in ["Positive", "Negative", "Neutral"]:
        c = counts.get(cat, 0)
        pct = (c / total * 100) if total else 0
        rows.append(f"| {cat} | {c} | {pct:.1f}% |")
    table = (
        "| Category | Count | % |\n"
        "|---|---:|---:|\n" +
        "\n".join(rows)
    )
    return table

def main():
    load_dotenv()
    client = OpenAI()

    # --- 2) Carregar dados ---
    df = load_feedbacks("data/feedbacks.csv")

    # --- 3) Classificar sentimentos e issues ---
    sentiments = []
    all_issues = []
    for row in df.itertuples():
        s = classify_sentiment(row.feedback)
        sentiments.append(s)
        all_issues.extend(extract_issues(row.feedback))

    df["sentiment"] = sentiments

    # --- 4) Contagens e % ---
    counts = Counter(df["sentiment"])
    total = len(df)
    table_md = build_markdown_table(counts, total)

    # --- 5) Top 3 issues ---
    issue_counts = Counter(all_issues)
    top3 = issue_counts.most_common(3)
    top3_list = [f"**{k}** — {v} ocorrência(s)" for k, v in top3] if top3 else ["(Sem issues recorrentes detectados)"]

    # --- 6) Montar insumos 100% determinísticos ---
    # Incluímos também alguns exemplos curtos por categoria para o LLM ilustrar (opcional).
    examples = defaultdict(list)
    for row in df.itertuples():
        if len(examples[row.sentiment]) < 2:  # até 2 exemplos por categoria
            examples[row.sentiment].append(f"{row.id}: {row.feedback}")

    insights_block = (
        f"Total feedbacks: {total}\n\n"
        f"Table (Markdown):\n{table_md}\n\n"
        f"Top 3 recurring issues:\n- " + "\n- ".join(top3_list) + "\n\n"
        f"Examples by category (up to 2 each):\n"
        f"- Positive: " + (" | ".join(examples.get("Positive", []) or ["—"])) + "\n"
        f"- Negative: " + (" | ".join(examples.get("Negative", []) or ["—"])) + "\n"
        f"- Neutral: "  + (" | ".join(examples.get("Neutral", [])  or ["—"])) + "\n"
    )

    # --- 7) Prompt: LLM só redige (não inventar números) ---
    prompt = f"""
You are a business analyst. Write a monthly report based ONLY on the metrics and items below.
Do not invent numbers or categories; use them as-is. Keep it concise and executive-ready.

Required sections:
- ## Positive (bulleted, 3–5 bullets)
- ## Negative (bulleted, 3–5 bullets)
- ## Neutral (bulleted, 1–3 bullets)
- ## Metrics (include the Markdown table exactly as provided, without altering values)
- ## Top 3 Issues (one-liners; bold the issue keyword already provided)
- ## Recommendations (2 bullets, each starting with a verb)
- **TL;DR** (one line)

Metrics and items (DO NOT CHANGE THE NUMBERS OR TABLE):
{insights_block}
"""

        # --- 8) Chamada ao modelo com fallback ---
    def generate_text_with_fallback():
        try:
            resp = client.responses.create(
                model=MODEL_NAME,
                input=prompt
            )
            return resp.output_text
        except Exception as e:
            print(f"[AVISO] Falha ao chamar OpenAI: {e}")
            # Fallback: relatório mínimo com as métricas já calculadas em Python
            fallback = [
                "# Customer Feedback Report (fallback)",
                "Relatório gerado sem LLM devido a erro na API. Números e issues vêm do Python.",
                "## Metrics",
                table_md,
                "## Top 3 Issues",
            ]
            if top3_list:
                fallback.extend([f"- {item}" for item in top3_list])
            else:
                fallback.append("- (Sem issues recorrentes)")
            fallback.extend([
                "## Recommendations",
                "- Revisar políticas de frete e SLA de entrega.",
                "- Treinar equipe de atendimento para reduzir tempo de resposta.",
                "## TL;DR",
                "Relatório gerado em modo de contingência; números conferidos no Python."
            ])
            return "\n".join(fallback)

    report_md = generate_text_with_fallback()

    # --- 9) Salvar saída ---
    out = Path("outputs/hybrid.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_md, encoding="utf-8")
    print(f"[OK] Relatório híbrido salvo em {out.resolve()}")

