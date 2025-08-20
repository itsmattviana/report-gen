from pathlib import Path

def main():
    report_path = Path("outputs/hybrid.md")
    if not report_path.exists():
        print("[ERRO] Nenhum relatório encontrado em outputs/hybrid.md")
        print("Dica: rode antes `python src/report_hybrid.py`")
        return

    report = report_path.read_text(encoding="utf-8")

    readme_path = Path("README.md")
    header = "# 📊 Customer Feedback Reports\n\nÚltima versão gerada automaticamente:\n\n"
    readme_path.write_text(header + report, encoding="utf-8")

    print(f"[OK] README.md atualizado com o relatório mais recente -> {readme_path.resolve()}")

if __name__ == "__main__":
    main()

