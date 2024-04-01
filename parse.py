import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors


search_text = "간호"
current_directory = os.path.dirname(os.path.abspath(__file__))
output_directory = os.path.join(current_directory, "output")
output_file_path = os.path.join(output_directory, "combined_output.json")
pdf_file_path = os.path.join(current_directory, "result.pdf")


def merge_file():
    json_files = [
        f
        for f in os.listdir(output_directory)
        if f.startswith("output_") and f.endswith(".json")
    ]

    all_data = []
    for file in json_files:
        with open(os.path.join(output_directory, file), "rt", encoding="utf8") as f:
            file_data = json.load(f)
            all_data.append(file_data)

    with open(output_file_path, "w", encoding="utf8") as f:
        json.dump(all_data, f, ensure_ascii=False)


def parse_data():
    res = []
    with open(output_file_path, "rt", encoding="utf8") as f:
        res = json.load(f)
    return res


def export_excel(data_li):
    table_data = [("날짜", "수급자명", "본문")]
    cnt = 0
    for data in data_li:
        for key in data:
            if key == "date":
                continue
            msg_li = data[key]
            cnt += len(msg_li)
            for i, msg in enumerate(msg_li):
                if search_text in msg:
                    table_data.append((data['date'][i], key, msg.replace(search_text, f"『{search_text}』")))
    print(cnt)

    # PDF 생성
    pdfmetrics.registerFont(TTFont("NanumMyeongjo", "NanumMyeongjo-Regular.ttf"))
    doc = SimpleDocTemplate(pdf_file_path, pagesize=A4)
    elements = []
    
    # 테이블 생성
    table_style = TableStyle(
        [
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "NanumMyeongjo"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )
    
    max_rows_per_page = 25
    for i in range(0, len(table_data), max_rows_per_page):
        page_data = table_data[i:i+max_rows_per_page]

        # 테이블 생성
        table = Table(page_data, colWidths=[80, 60, 420])
        table.setStyle(table_style)
        elements.append(table)

        # 페이지 브레이크 추가
        if i + max_rows_per_page < len(data):
            elements.append(PageBreak())
    doc.build(elements)



if __name__ == "__main__":
    # merge_file()
    dat = parse_data()
    export_excel(dat)
    ...
