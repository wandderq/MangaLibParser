import os
import re
import sys
import json
import cloudscraper
import validators
import logging as lg

from requests import RequestException
from argparse import ArgumentParser

from pdf_saver import save_chapter_as_pdf

MANGALIB_API_URL = 'https://api2.mangalib.me/api/manga'
IMGLIB_URL = 'https://img2.imglib.info/'
REQUEST_ATTEMPTS_LIMIT = 3

logger = lg.getLogger('mlibparser')

formatter = lg.Formatter('[%(asctime)s: %(levelname)s] [%(name)s] %(message)s')

stream_handler = lg.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(formatter)

class InvalidUrlError(Exception): ...
class InvalidChaptersError(Exception): ...
class MangaLibParserError(Exception): ...

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
            raise MangaLibParserError(f'Invalid MangaLib URL: {manga_url}')
        
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
    
    def __download_pages(self, pages: list, output_dir: str) -> None:
        downloaded = 0
        downloaded_pages = [os.path.splitext(filename)[0] for filename in os.listdir(output_dir) if os.path.splitext(filename)[1].lower() in ('.jpeg', '.jpg', '.png','.webp')]
        
        for id, url in enumerate(pages, 1):
            try:
                if str(id) in downloaded_pages:
                    continue
                
                resp = self.__scraper.get(url)
                if resp.status_code == 200:
                    ext = '.png' if '.png' in url else '.jpg' if '.jpg' in url else '.webp' if '.webp' in url else '.jpg'
                    image_path = os.path.join(output_dir, f"{id}{ext}")
                    with open(image_path, 'wb') as file:
                        file.write(resp.content)
                    downloaded += 1
            
            except Exception as e:
                print(e)
    
    def download(
            self,
            manga_url: str,
            chapters: list,
            output_dir: str = 'Manga',
            pdf: bool = False
        ) -> None:
        
        if not chapters:
            raise MangaLibParserError('Chapters list cannot be empty')
        if not output_dir:
            output_dir = 'Manga'
        
        url_slug = self.__parse_mangalib_url(manga_url)
        logger.info(f'Downloading manga: {url_slug}, chapters: {chapters}')
        
        manga_stats = self.get_manga_stats(manga_url)
        manga_name = str(manga_stats['data']['name']).lower().replace(' ', '_')
        manga_dir = os.path.join(output_dir, manga_name)
        
        chapters_info = self.__get_chapters_info(url_slug)
        if chapters_info is None:
            return
        chapters_info = {item['index']: item for item in chapters_info['data']}
        max_chapters = len(chapters_info)
        
        os.makedirs(manga_dir, exist_ok=True)
        for chapter in chapters:
            try:
                chapter_info = chapters_info[chapter]
                
                chapter_orig_name = chapter_info['name']
                chapter_orig_number = chapter_info['number']
                chapter_orig_volume = chapter_info['volume']
                
                chapter_dir_name = f'Chapter {chapter_orig_number}' +  (f' - {chapter_orig_name}' if str(chapter_orig_name).strip() else '')
                if os.path.exists(os.path.join(manga_dir, f'{chapter_dir_name}.pdf')) and pdf:
                    logger.debug(f'Chapter {chapter} alreday downloaded in pdf format')
                    
                chapter_dir = os.path.join(manga_dir, chapter_dir_name)
                os.makedirs(chapter_dir, exist_ok=True)
                
                pages = self.__get_chapter_pages(url_slug, chapter_orig_volume, chapter_orig_number)
                self.__download_pages(pages, chapter_dir)
                
                if pdf:
                    save_chapter_as_pdf(chapter_dir=chapter_dir, chapter_name=chapter_dir_name)
                
            except KeyError:
                logger.error(f'Chapter {chapter} not found')
        
def main() -> None:
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
            raise InvalidChaptersError(f'Invalid chapter(s) integer/range: {chapters}')
        
        os.makedirs(args.output_dir, exist_ok=True)
        
        if len(parts) == 1:
            mlp.download(
                manga_url=args.url,
                chapters=[int(parts[0])],
                output_dir=args.output_dir,
                pdf=args.pdf
            )
        
        elif len(parts) == 2:
            mlp.download(
                manga_url=args.url,
                chapters=[i for i in range(int(parts[0]), int(parts[1]) + 1)],
                output_dir=args.output_dir,
                pdf=args.pdf
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