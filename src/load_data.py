from pathlib import Path
import pandas as pd

def load_feedbacks(csv_path: str) -> pd.DataFrame:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_file}")
    df = pd.read_csv(csv_file)
    cols = ["id", "date", "customer", "feedback"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas faltando no CSV: {missing}")
    df = df.dropna(subset=["feedback"]).reset_index(drop=True)
    return df
