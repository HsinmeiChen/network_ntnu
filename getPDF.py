import os
import pandas as pd
import gradio as gr
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

def get_chinese_font_file():
    fonts_path = r"C:\\Windows\\Fonts"
    candidates = ["kaiu.ttf", "msjh.ttc", "mingliu.ttc"]
    for font in candidates:
        font_path = os.path.join(fonts_path, font)
        if os.path.exists(font_path):
            return os.path.abspath(font_path)
    return None

//資料分析邏輯
def generate_analysis_report_from_csv(file_path, output_pdf_path):
    df = pd.read_csv(file_path)

    user_summary = df.groupby("USER_ID").agg(
        總答題數=("GPT_ANSWER_VALIDATOR_REPLY", "count"),
        正確數=("GPT_ANSWER_VALIDATOR_REPLY", lambda x: (x == True).sum())
    )
    user_summary["正確率 (%)"] = (user_summary["正確數"] / user_summary["總答題數"] * 100).round(2)
    user_summary.reset_index(inplace=True)

    guide_summary = df.groupby("CURRENT_GUIDE").agg(
        總答題數=("GPT_ANSWER_VALIDATOR_REPLY", "count"),
        正確數=("GPT_ANSWER_VALIDATOR_REPLY", lambda x: (x == True).sum())
    )
    guide_summary["錯誤數"] = guide_summary["總答題數"] - guide_summary["正確數"]
    guide_summary["正確率 (%)"] = (guide_summary["正確數"] / guide_summary["總答題數"] * 100).round(2)
    guide_summary.reset_index(inplace=True)

    most_wrong_guide = guide_summary.sort_values("正確率 (%)").iloc[0]["CURRENT_GUIDE"]
    top_3_wrong_guides = guide_summary.sort_values("錯誤數", ascending=False).head(3)["CURRENT_GUIDE"].tolist()

    chinese_font_path = get_chinese_font_file()
    if chinese_font_path:
        pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
        font_name = "ChineseFont"
    else:
        font_name = "Helvetica"

    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ChineseTitle', fontName=font_name, fontSize=20, leading=24, alignment=1))
    styles.add(ParagraphStyle(name='ChineseNormal', fontName=font_name, fontSize=12, leading=16))

    elements = [
        Paragraph("答題成效分析報告", styles["ChineseTitle"]),
        Spacer(1, 12),
        Paragraph("以下為每位使用者的答題正確率統計：", styles["ChineseNormal"]),
        Spacer(1, 6)
    ]

    user_table_data = [list(user_summary.columns)] + user_summary.values.tolist()
    user_table = Table(user_table_data)
    user_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 10)
    ]))
    elements.append(user_table)

    elements += [
        Spacer(1, 20),
        Paragraph("以下為各題目（CURRENT_GUIDE）正確率統計（含錯誤數）：", styles["ChineseNormal"]),
        Spacer(1, 6)
    ]

    guide_table_data = [list(guide_summary.columns)] + guide_summary.values.tolist()
    guide_table = Table(guide_table_data)
    guide_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 10)
    ]))
    elements.append(guide_table)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"📌 正確率最低的題目（CURRENT_GUIDE）是：{most_wrong_guide}", styles["ChineseNormal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"📌 錯誤次數最多的前三題目為：{', '.join(top_3_wrong_guides)}", styles["ChineseNormal"]))

    doc.build(elements)
    return output_pdf_path

def gradio_handler(file):
    if file is None:
        return "請上傳檔案", None

    file_path = file.name
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"答題成效分析報告_{now}.pdf"

    try:
        generate_analysis_report_from_csv(file_path, pdf_path)
        return "分析成功，請下載報表。", pdf_path
    except Exception as e:
        return f"產生報表失敗：{str(e)}", None

with gr.Interface(
    fn=gradio_handler,
    inputs=[gr.File(label="請上傳答題 CSV 檔案", file_types=[".csv"])],
    outputs=[gr.Textbox(label="分析狀態"), gr.File(label="下載報表 PDF")],
    title="答題成效分析報表產生器",
    description="上傳答題記錄 CSV 檔案，自動計算每位使用者與各題目（CURRENT_GUIDE）的答題正確率，並產出整齊的分析報告 PDF。"
) as demo:
    demo.launch()
