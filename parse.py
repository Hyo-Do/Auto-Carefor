import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageTemplate, Frame
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
    json_files.sort(reverse=True)

    all_data = []
    for file in json_files:
        with open(os.path.join(output_directory, file), "rt", encoding="utf8") as f:
            file_data = json.load(f)
            all_data.append(file_data)

    with open(output_file_path, "w", encoding="utf8") as f:
        json.dump(all_data, f, ensure_ascii=False)


def load_file():
    res = []
    with open(output_file_path, "rt", encoding="utf8") as f:
        res = json.load(f)
    return res


def processing_data(data_li):
    _max_width = 60
    res = [("날짜", "성함", "본문")]
    cnt = 0
    for data in data_li:
        for key in data:
            if key == "date":
                continue
            msg_li = data[key]
            cnt += len(msg_li)
            for i, msg in enumerate(msg_li):
                if search_text in msg:
                    _msg = (
                        msg.replace(search_text, f"『{search_text}』")
                        .replace("\n", " ")
                        .replace("  ", " ")
                        .replace("  ", " ")
                    )
                    if len(_msg) > _max_width:
                        _msg = "\n".join(
                            _msg[_max_width * i : _max_width * (i + 1)]
                            for i in range(len(_msg) // _max_width + 1)
                        )
                    res.append((data["date"][i], key, _msg))
    print(cnt)
    return res


def _add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont("NanumMyeongjo", 8.5)
    canvas.drawString(10, 9, text)


def _init_table_style():
    return TableStyle(
        [
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "NanumMyeongjo"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def export_pdf(data):
    pdfmetrics.registerFont(TTFont("NanumMyeongjo", "NanumMyeongjo-Regular.ttf"))
    doc = SimpleDocTemplate(pdf_file_path, pagesize=A4, topMargin=40, bottomMargin=25)
    table = Table(data, colWidths=[65, 50, 445])
    table.setStyle(_init_table_style())
    doc.build([table], onFirstPage=_add_page_number, onLaterPages=_add_page_number)


if __name__ == "__main__":
    # merge_file()
    export_pdf(processing_data(load_file()))
    ...
