from PIL import Image
import os
import logging as lg

logger = lg.getLogger('mlibparser.pdfsaver')

def save_chapter_as_pdf(chapter_dir, chapter_name) -> None:
    pages = [os.path.abspath(os.path.join(chapter_dir, page)) for page in os.listdir(chapter_dir) if os.path.isfile(os.path.join(chapter_dir, page))]
    images = [Image.open(image) for image in pages]
    
    manga_dir = os.path.dirname(os.path.abspath(chapter_dir))
    
    images[0].save(
        os.path.join(manga_dir, f'{chapter_name}.pdf'),
        "PDF", 
        resolution=100.0,
        save_all=True,
        append_images=images[1:]
    )
    
    for page in pages:
        os.remove(page)
    