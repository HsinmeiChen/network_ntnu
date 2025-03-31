import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def get_chinese_font_file() -> str:
    fonts_path = r"C:\\Windows\\Fonts"
    candidates = ["kaiu.ttf", "msjh.ttc", "mingliu.ttc"]
    for font in candidates:
        font_path = os.path.join(fonts_path, font)
        if os.path.exists(font_path):
            print("找到系統中文字型：", font_path)
            return os.path.abspath(font_path)
    print("未在系統中找到候選中文字型檔案。")
    return None

def generate_report(output_filename):
    # 讀取資料檔案
    df = pd.read_csv("sample3-2.csv")

    # 計算每位使用者正確率
    user_summary = df.groupby("USER_ID").agg(
        總答題數=("GPT_ANSWER_VALIDATOR_REPLY", "count"),
        正確數=("GPT_ANSWER_VALIDATOR_REPLY", lambda x: (x == True).sum())
    )
    user_summary["正確率 (%)"] = (user_summary["正確數"] / user_summary["總答題數"] * 100).round(2)
    user_summary.reset_index(inplace=True)

    # 每一題正確率與錯誤題號
    step_summary = df.groupby("CURRENT_STEP").agg(
        總答題數=("GPT_ANSWER_VALIDATOR_REPLY", "count"),
        正確數=("GPT_ANSWER_VALIDATOR_REPLY", lambda x: (x == True).sum())
    )
    step_summary["錯誤數"] = step_summary["總答題數"] - step_summary["正確數"]
    step_summary["正確率 (%)"] = (step_summary["正確數"] / step_summary["總答題數"] * 100).round(2)
    step_summary.reset_index(inplace=True)

    most_wrong_step = step_summary.sort_values("正確率 (%)").iloc[0]["CURRENT_STEP"]

    chinese_font_path = get_chinese_font_file()
    if chinese_font_path:
        pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
        print("已註冊中文字型：", chinese_font_path)
    else:
        print("無中文字型，將使用預設字型。")

    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ChineseTitle', fontName='ChineseFont' if chinese_font_path else styles['Title'].fontName, fontSize=24, leading=28, alignment=1))
    styles.add(ParagraphStyle(name='ChineseNormal', fontName='ChineseFont' if chinese_font_path else styles['Normal'].fontName, fontSize=12, leading=14))

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
        ("FONTNAME", (0,0), (-1,-1), "ChineseFont" if chinese_font_path else styles['Normal'].fontName),
        ("FONTSIZE", (0,0), (-1,-1), 10)
    ]))
    elements.append(user_table)

    elements += [
        Spacer(1, 20),
        Paragraph("以下為各題目正確率統計（含錯誤數）：", styles["ChineseNormal"]),
        Spacer(1, 6)
    ]

    step_table_data = [list(step_summary.columns)] + step_summary.values.tolist()
    step_table = Table(step_table_data)
    step_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,-1), "ChineseFont" if chinese_font_path else styles['Normal'].fontName),
        ("FONTSIZE", (0,0), (-1,-1), 10)
    ]))
    elements.append(step_table)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"📌 正確率最低的題號是：{most_wrong_step}", styles["ChineseNormal"]))

    doc.build(elements)
    print("PDF 檔案已儲存至:", output_filename)

if __name__ == "__main__":
    generate_report("exam_report_chinese.pdf")