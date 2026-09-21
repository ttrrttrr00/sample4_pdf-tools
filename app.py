import streamlit as st
import io, zipfile, re, pymupdf
from PIL import Image

st.set_page_config(page_title="문서 통합 도구", layout="wide")
st.title("📄 PDF 및 문서 통합 유틸리티")

t1, t2, t3, t4 = st.tabs(["1. 단어/특수문자", "2. 이미지 추출", "3. 텍스트 추출", "4. HWPX 통합 생성"])

with t1:
    f1 = st.file_uploader("문서 업로드 (PDF, TXT)", type=["pdf", "txt"], key="u1")
    if f1:
        text = "\n".join([p.get_text() for p in pymupdf.open(stream=f1.read(), filetype="pdf")]) if f1.name.endswith(".pdf") else f1.read().decode("utf-8", errors="ignore")
        c1, c2, c3 = st.columns(3)
        c1.metric("총 단어 수", f"{len(text.split()):,} 개")
        c2.metric("특수문자 수", f"{len(re.findall(r'[\w\s]', text)):,} 개")
        c3.metric("글자 수(공백제외)", f"{len(re.sub(r'\s+', '', text)):,} 자")
        st.text_area("텍스트 미리보기", text, height=200)

with t2:
    f2 = st.file_uploader("PDF 업로드 (이미지 추출)", type=["pdf"], key="u2")
    if f2:
        doc = pymupdf.open(stream=f2.read(), filetype="pdf")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            cnt = 0
            for p_i, p in enumerate(doc):
                for i_i, img in enumerate(p.get_images(full=True)):
                    im = Image.open(io.BytesIO(doc.extract_image(img[0])["image"])).convert("RGB")
                    o = io.BytesIO(); im.save(o, format="JPEG")
                    z.writestr(f"p{p_i+1}_img{i_i+1}.jpg", o.getvalue())
                    cnt += 1
        if cnt > 0:
            st.success(f"총 {cnt}개 이미지 추출 완료")
            st.download_button("이미지 전체 다운로드 (.zip)", buf.getvalue(), "images.zip")
        else:
            st.warning("추출할 이미지가 없습니다.")

with t3:
    f3 = st.file_uploader("PDF 업로드 (텍스트 추출)", type=["pdf"], key="u3")
    if f3:
        doc = pymupdf.open(stream=f3.read(), filetype="pdf")
        res = "\n\n".join([f"=== [페이지 {i+1}] ===\n" + p.get_text() for i, p in enumerate(doc)])
        st.download_button("텍스트 다운로드 (.txt)", res.encode("utf-8"), "extracted.txt")
        st.text_area("내용", res, height=250)

with t4:
    st.info("PDF의 본문 텍스트와 추출 이미지를 결합하여 .hwpx 문서 파일로 패키징합니다.")
    f4 = st.file_uploader("PDF 업로드 (HWPX 변환)", type=["pdf"], key="u4")
    if f4:
        doc = pymupdf.open(stream=f4.read(), filetype="pdf")
        hwpx_buf = io.BytesIO()
        with zipfile.ZipFile(hwpx_buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("mimetype", "application/hwp+zip")
            body_lines = []
            img_idx = 0
            for p_i, page in enumerate(doc):
                t = page.get_text().strip()
                if t:
                    body_lines.append(f"=== [페이지 {p_i+1}] ===\n" + t)
                for img in page.get_images(full=True):
                    img_idx += 1
                    raw_img = doc.extract_image(img[0])["image"]
                    z.writestr(f"BinData/image{img_idx}.jpg", raw_img)
                    body_lines.append(f"[그림 {img_idx} 삽입: BinData/image{img_idx}.jpg]")
            full_txt = "\n\n".join(body_lines)
            sec_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">\n'
            for line in full_txt.splitlines():
                safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                sec_xml += f'  <hp:p><hp:run><hp:t>{safe}</hp:t></hp:run></hp:p>\n'
            sec_xml += '</hs:sec>'
            z.writestr("Contents/section0.xml", sec_xml.encode("utf-8"))
        st.success(f"총 {len(doc)}페이지 텍스트와 {img_idx}개 이미지가 결합되었습니다.")
        st.download_button("생성된 .hwpx 다운로드", hwpx_buf.getvalue(), "converted.hwpx", mime="application/octet-stream")
