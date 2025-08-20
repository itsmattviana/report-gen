from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def main():
    input_file = Path("outputs/hybrid.md")
    if not input_file.exists():
        print("[ERRO] Nenhum relatório encontrado em outputs/hybrid.md")
        print("Dica: rode antes `python src/report_hybrid.py`")
        return

    report = input_file.read_text(encoding="utf-8")

    output_file = Path("outputs/report.pdf")
    c = canvas.Canvas(str(output_file), pagesize=A4)
    width, height = A4

    # quebra simples por linha
    y = height - 50
    for line in report.splitlines():
        c.drawString(40, y, line[:110])  # corta linhas muito grandes
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    print(f"[OK] Relatório PDF salvo em {output_file.resolve()}")

if __name__ == "__main__":
    main()

