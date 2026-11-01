from common import ROOT,AUDIT,save,digest
from pypdf import PdfReader
import fitz
def main():
    out=AUDIT/'papers';out.mkdir(exist_ok=True);records=[]
    for project,name,pages in [('01_PhysGaussian','PhysGaussian_2024.pdf',[4,5,8]),('02_PAT','PAT_2006.pdf',[6,7]),('03_NeuralSound','NeuralSound_2022.pdf',[7,8])]:
        path=ROOT/project/'paper'/name;reader=PdfReader(path)
        text='\n\n'.join(f'=== PDF PAGE {i+1} ===\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages))
        (out/(project+'.txt')).write_text(text,encoding='utf-8')
        doc=fitz.open(path)
        for page in pages:
            doc[page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(out/f'{project}_page{page:02d}.png'))
        records.append(dict(path=str(path),sha256=digest(path),pages=len(reader.pages),rendered_pages=pages))
    save('papers/sources.json',records)
if __name__=='__main__':main()
