#!/usr/bin/env python3

import os
import re
import sys
import cloudscraper
import validators
import logging as lg
import unicodedata

from PIL import Image
from io import BytesIO
from requests import RequestException
from argparse import ArgumentParser

MANGALIB_API_URL = 'https://api2.mangalib.me/api/manga'
IMGLIB_URL = 'https://img2.imglib.info/'
REQUEST_ATTEMPTS_LIMIT = 3

logger = lg.getLogger('mlibparser')

class InvalidUrlError(Exception): ...

class MangaLibParser:
    def __init__(self) -> None:
        self.__scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False,
            },
            delay=3
        )
    
    def __sanitize_chapter_name(self, filename, replace_with=" "):
        filename = unicodedata.normalize("NFKD", filename)
        
        filename = "".join(c for c in filename if not unicodedata.category(c).startswith("C"))
        
        forbidden_chars = r'<>:"/\|?*\0'
        for char in forbidden_chars:
            filename = filename.replace(char, replace_with)
        
        filename = filename.strip(". ")
        
        filename = re.sub(r"_+", "_", filename)
        
        if not filename:
            filename = "unnamed"
        
        max_length = 255
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip(". ")
        
        return filename
    
    def __make_request(self, url: str, params = None) -> dict:
        for attempt in range(1, REQUEST_ATTEMPTS_LIMIT + 1):
            try:
                logger.debug(f'Trying to do request to \'{url}\', attempt {attempt}')
                
                responce = self.__scraper.get(url, params=params)
                logger.debug(f'GET \'{url}\' STATUS {responce.status_code}')
                
                if responce.status_code == 200:
                    return responce.json()
            
            except Exception as e:
                logger.warning(f'GET request to \'{url}\' failed due to error: {str(e)}. Attempt {attempt}')
        raise RequestException(f'GET request to \'{url}\' failed after {REQUEST_ATTEMPTS_LIMIT} attempts')
                
    
    def __parse_mangalib_url(self, manga_url: str) -> str:
        manga_url = str(manga_url).strip()
        if not validators.url(manga_url):
            raise InvalidUrlError(f'String \'{manga_url}\' is not an url')
        
        match = re.search(r'/manga/(\d+--[^/?]+)', manga_url)
        if not match:
            raise InvalidUrlError(f'Invalid MangaLib URL: {manga_url}')
        
        return match.group(1)
    
    def get_manga_stats(self, manga_url: str) -> dict:
        url_slug = self.__parse_mangalib_url(manga_url)
        logger.info(f'Getting manga stats: {url_slug}')
        
        stats_url = f'{MANGALIB_API_URL}/{url_slug}'
        data = self.__make_request(stats_url)
        
        return data
    
    def __get_chapters_info(self, url_slug: str) -> dict | None:
        info_url = f'{MANGALIB_API_URL}/{url_slug}/chapters'
        data = self.__make_request(info_url)
        
        if not data or 'data' not in data:
            logger.warning(f'No chapters found in {url_slug}')
            return None
        
        return data
    
    def __get_chapter_pages(self, url_slug: str, volume: int, chapter: int) -> list:
        pages_url = f'{MANGALIB_API_URL}/{url_slug}/chapter'
        params = {'number': chapter, 'volume': volume}
        
        data = self.__make_request(pages_url, params)
        return [f"{IMGLIB_URL}{page['url']}" for page in data['data']['pages']]
    
    def __download_pages(self, url_slug: str, volume: int, chapter: int, chapter_dir: str, manga_dir: str, save_as_pdf: bool, pdf_name: str | None = None) -> None:
        pages_url = f'{MANGALIB_API_URL}/{url_slug}/chapter'
        params = {'number': chapter, 'volume': volume}
        data = self.__make_request(pages_url, params)
        pages = [f"{IMGLIB_URL}{page['url']}" for page in data['data']['pages']]
        
        # downloaded_pages = [os.path.splitext(filename)[0] for filename in os.listdir(output_dir) if os.path.splitext(filename)[1].lower() in ('.jpeg', '.jpg', '.png','.webp')]
        
        downloaded_pages = None
        downloaded_chapters = None
        
        if not save_as_pdf:
            downloaded_pages = [
                os.path.splitext(filename)[0]
                for filename in os.listdir(chapter_dir)
                if os.path.splitext(filename)[1].lower() in ('.jpg', '.png', '.webp')
            ]
        else:
            downloaded_chapters = [
                os.path.splitext(filename)[0]
                for filename in os.listdir(manga_dir)
                if os.path.splitext(filename)[1].lower() == '.pdf'
            ]
        
        pdf_images = []
        for id, url in enumerate(pages, 1):
            try:
                if not save_as_pdf:
                    if str(id) in downloaded_pages: # type: ignore
                        logger.debug(f'Page {id} from chapter {chapter} alreday downloaded')
                        continue
                else:
                    if pdf_name in downloaded_chapters: # type: ignore
                        logger.debug(f'Chapter {chapter} alreday downloaded')
                        break
                
                responce = self.__scraper.get(url)
                if responce.status_code == 200:
                    if save_as_pdf:
                        img = Image.open(BytesIO(responce.content))
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        pdf_images.append(img)
                    
                    else:
                        ext = '.png' if '.png' in url else '.jpg' if '.jpg' in url else '.webp' if '.webp' in url else '.jpg'
                        image_path = os.path.join(chapter_dir, f"{id}{ext}")
                        with open(image_path, 'wb') as page:
                            page.write(responce.content)
                            logger.debug(f'Page {id} downloaded')
                
                else:
                    logger.error(f'Unable to download page {id} from chapter{chapter} due to bad status code: {responce.status_code}')
                    continue
                
                
                # if str(id) in downloaded_pages:
                #     continue
                
                # resp = self.__scraper.get(url)
                # if resp.status_code == 200:
                #     ext = '.png' if '.png' in url else '.jpg' if '.jpg' in url else '.webp' if '.webp' in url else '.jpg'
                #     image_path = os.path.join(output_dir, f"{id}{ext}")
                #     with open(image_path, 'wb') as file:
                #         file.write(resp.content)
                #     downloaded += 1
            
            except Exception as e:
                logger.error(f'Error when downloading pages: {e}')
        
        if pdf_images:
            pdf_images[0].save(
                os.path.join(manga_dir, f'{pdf_name}.pdf'),
                "PDF",
                resolution=100.0,
                save_all=True,
                append_images=pdf_images[1:]
            )
    def parse_chapters(
            self,
            manga_url: str,
            chapters: list,
            output_dir: str = 'Manga',
            save_as_pdf: bool = False,
            simple_chapter_name: bool = False
        ) -> None:
        
        if not chapters:
            raise ValueError('Chapters list cannot be empty')
        
        url_slug = self.__parse_mangalib_url(manga_url)
        logger.info(f'Downloading manga: {url_slug}, chapters: {chapters}')
        
        manga_stats = self.get_manga_stats(manga_url)
        manga_name = str(manga_stats['data']['name']).lower().replace(' ', '_')
        
        chapters_info = self.__get_chapters_info(url_slug)
        if chapters_info is None:
            return
        
        chapters_info = {item['index']: item for item in chapters_info['data']}
        # max_chapters = len(chapters_info)
        
        manga_dir = os.path.join(output_dir, manga_name)
        os.makedirs(manga_dir, exist_ok=True)
        
        for chapter in chapters:
            try:
                chapter_info = chapters_info[chapter]
                chapter_original_name = chapter_info['name']
                chapter_original_number = chapter_info['number']
                chapter_original_volume = chapter_info['volume']
                
                if not simple_chapter_name:
                    chapter_name = f'Chapter {chapter_original_number}'
                    if str(chapter_original_name).strip():
                        sanitized_name = self.__sanitize_chapter_name(str(chapter_original_name).strip())
                        chapter_name += f' - {sanitized_name}'
                else:
                    chapter_name = f'chapter-{chapter_original_number}'
                
                chapter_dirname = os.path.join(manga_dir, chapter_name)
                
                if not save_as_pdf:
                    os.makedirs(chapter_dirname, exist_ok=True)
                
                self.__download_pages(
                    url_slug=url_slug,
                    volume=chapter_original_volume,
                    chapter=chapter_original_number,
                    chapter_dir=chapter_dirname,
                    manga_dir=manga_dir,
                    save_as_pdf=save_as_pdf,
                    pdf_name=chapter_name
                )
                
                # chapter_orig_name = chapter_info['name']
                # chapter_orig_number = chapter_info['number']
                # chapter_orig_volume = chapter_info['volume']
                
                # chapter_dir_name = f'Chapter {chapter_orig_number}' +  (f' - {chapter_orig_name}' if str(chapter_orig_name).strip() else '')
                    
                # chapter_dir = os.path.join(manga_dir, chapter_dir_name)
                # os.makedirs(chapter_dir, exist_ok=True)
                
                # pages = self.__get_chapter_pages(url_slug, chapter_orig_volume, chapter_orig_number)
                # self.__download_pages(pages, chapter_dir)
                
            except KeyError:
                logger.error(f'Chapter {chapter} not found')


def main() -> None:
    global logger
    
    formatter = lg.Formatter('[%(asctime)s: %(levelname)s] [%(name)s] %(message)s')
    stream_handler = lg.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    argparser = ArgumentParser(
        description='Simple mangalib.me manga parser',
        epilog=f"""For example:
        \'python {sys.argv[0]} https://mangalib.me/ru/manga/3595--kimetsu-no-yaiba -c 2-13 -iv\'
        downloads \'Kimetsu no Yaiba\' chapters from 2 to 13, shows manga info and debug logs"""
    )
    
    argparser.add_argument('url', type=str, help='Url to mnga page. Ex: https://mangalib.me/ru/manga/7965--chainsaw-man')
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode. Shows debug logs')
    argparser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode. Shows only warn/err/crit logs')
    
    argparser.add_argument('-c', '--chapters', default=[], help='Chapters to download (number or from-to range). Ex: 1-100')
    argparser.add_argument('-i', '--info', action='store_true', help='Shows manga info')
    argparser.add_argument('-o', '--output-dir', default='Manga', type=str, help='Output directory, defaults setted to \'Manga\'. Downloading like this: /output/path/manga-name/chapters... ')
    argparser.add_argument('--pdf', action='store_true', help='Save manga chapters in .pdf format')
    argparser.add_argument('-s', '--simple-names', action='store_true', help='Use simple names for chapters')
    
    args = argparser.parse_args()
    mlp = MangaLibParser()
    
    logger.setLevel(lg.WARNING if args.quiet else lg.DEBUG if args.verbose else lg.INFO)
    logger.debug('Startting args parsing')
    
    if not args.chapters and not args.info:
        logger.warning('Nothing to do!')
                
    if args.chapters:
        chapters = str(args.chapters).strip()
        logger.info(f'Setted chapter(s): {chapters}')
        
        parts = chapters.split('-')
        
        if (len(parts) not in (1,2) or not all([i.isdigit() for i in parts]) or int(parts[0]) < 1):
            raise ValueError(f'Invalid chapter(s) integer/range: {chapters}')
        
        os.makedirs(args.output_dir, exist_ok=True)
        
        if len(parts) == 1:
            mlp.parse_chapters(
                manga_url=args.url,
                chapters=[int(parts[0])],
                output_dir=args.output_dir,
                save_as_pdf=args.pdf,
                simple_chapter_name=args.simple_names
            )
        
        elif len(parts) == 2:
            mlp.parse_chapters(
                manga_url=args.url,
                chapters=[i for i in range(int(parts[0]), int(parts[1]) + 1)],
                output_dir=args.output_dir,
                save_as_pdf=args.pdf,
                simple_chapter_name=args.simple_names
            )
            
    if args.info:
        logger.info('Getting manga info...')
        stats = mlp.get_manga_stats(
            manga_url=args.url,
        )
        data = stats['data']
        
        manga_id = data['id']
        manga_name = data['name']
        manga_rus_name = data['rus_name']
        manga_eng_name = data['eng_name']
        manga_age_restriction = data['ageRestriction']['label']
        manga_is_licensed = data['is_licensed']
        manga_status = data['status']['label']
        manga_release = data['releaseDateString']
        
        print(f"""
== \'{manga_eng_name}\' stats ==

ID              : {manga_id}
Name            : {manga_name}
Russian name    : {manga_rus_name}
English name    : {manga_eng_name}
Age restriction : {manga_age_restriction}
Is licensed     : {manga_is_licensed}
Status          : {manga_status}
Release date    : {manga_release}
             """)
    
if __name__ == '__main__':
    main()
    
sys.exit(0)