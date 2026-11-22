#!/usr/bin/env python3
# Use URL provided as command-line argument
# RUN:
# python C:\Users\PC\Desktop\LeaStripper.py https://wol.jw.org/es/wol/d/r4/lp-s/2026401
# REQ:
# python -m pip install requests html2text beautifulsoup4 playwright

import argparse
import os
import re
import sys
import tempfile
import requests
import html2text
from bs4 import BeautifulSoup

# opening via sessions, trying to avoid Network error: ('Connection aborted.', RemoteDisconnected('Remote end closed
# connection without response') and 403 ERROR — The request could not be satisfied. Request blocked.)
from playwright.sync_api import sync_playwright

def download_text(url):
    # open headless Playwright chromium, to extract page.content() for processing
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome",headless=True,args=["--disable-blink-features=AutomationControlled","--no-sandbox","--disable-dev-shm-usage",])
        context = browser.new_context(viewport={"width": 1920, "height": 1080},locale="es-ES",user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/140.0.0.0 Safari/537.36")
        page = context.new_page()
        page.goto(url,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    return html

def strip_html_tags(dirtytext):
    # Remove anything between < and >, removes add the newline chars to keep each entry on one line
    cleantext = re.sub(r'<.*?>', '', dirtytext)
    cleantext = re.sub(r'&nbsp;', ' ', cleantext)
    # remove endline
    cleantext = cleantext.replace("\n", " ")
    # remove extra white spaces
    cleantext = (re.sub(' +', ' ', (cleantext.replace('\n', ' ')))).strip()

    return cleantext


def cleandownload(dirtytext):
    # Uses html2text to clean the freshly downloaded HTML into somewhat clean text, there are special chars that are left over and notations that jw.org using to long/display
    cleantext = html2text.html2text(dirtytext)
    # Removes *, [, and ] from the whole text
    cleantext = re.sub(r'\*', '', cleantext)
    cleantext = re.sub(r'[\[\]]', '', cleantext)
    # Finds and removes for the chars / or \ that are enclosed in ( ) and remove everything between ( ), including the ( )
    pattern = r'\([^()]*[\\/][^()]*\)'
    cleantext = re.sub(pattern, '', cleantext)
    return cleantext


def search_text(text:str, debug:bool=False):
    # Find occurrences of "(lea"
    # Match "(le[ae]" (case-insensitive) and continue until the next ')' or '.'

    #pattern = re.compile(r'\(l[eé][ae][^)]*\)', re.IGNORECASE)
    pattern = re.compile(r'\((?:l[eé][ae][^)]*|[^)]*\bl[eé][ae]\s+[^)]*\d+:\d+[^)]*)\)', re.IGNORECASE)
    #if debug: print(f"In search_text, text passed dump: {text} \n----END OF DUMP---")
    matches_found = False
    only_citations = []
    for i, match in enumerate(pattern.finditer(text), start=1):
        # if we got here that means that pattern.finditer(text) found at
        # least one iteration in the text of the pattern
        matches_found = True
        full_text = match.group()
        if debug: print(f"{i}: {full_text}")
        if debug: print(f"{i}: {match}")
        # if pattern contains a ';' to include the all the text between ( and ) in the output, a ';' would
        # indicate that there are multiple verses between ()
        if ";" in full_text:
            ingredient = re.sub(r'^\(le[ae]\s*','',full_text[:-1],flags=re.IGNORECASE)
        else:
            ingredient = re.sub(r'^\(le[ae]\s*','',full_text[:-1],flags=re.IGNORECASE)

        # once an instance of the pattern '(lea' is found search backwards for the first occurrence of a number
        # followed by ". ¿", keep track of that number, output the number at the end with 'Parr #' appended
        #todo
        # logic if match contains no numbers, the needed verse most be contained some where else, most
        # likely the needed verse would be the first one in ( ) right after the question to the paragraph. For
        # now just continue if there are no digits. Like in this example paragraph:
        # : 7 Los siervos de Jehová contamos con herramientas que nos permiten superar las barreras lingüísticas.
        # Predicamos unidos “buenas noticias eternas [...] a toda nación, tribu, lengua y pueblo” con la ayuda del
        # “ángel” mencionado en Apocalipsis 14:6 (léelo). Al ver cómo se cumplen en nuestros tiempos profecías tan
        # emocionantes como esta de Apocalipsis y la de Zacarías, nos convencemos de que las demás también se harán
        # realidad y estamos aún más decididos a ser leales a la organización que Jehová utiliza para proclamar las
        # buenas noticias.
        if not re.search(r'\d', full_text):
            continue
        # Everything before this match
        preceding_text = text[:match.start()]

        # Find the last <sup>123</sup> before this match
        parr_matches = list(re.finditer(r'\s*(\d+)\s*\.', preceding_text, re.IGNORECASE))
        parr_number = parr_matches[-1].group(1) if parr_matches else "Unknown"
        ingredient = strip_html_tags(ingredient)
        parr_number = strip_html_tags(parr_number)
        print(f"{i}: {ingredient} - Parr {parr_number}")
        only_citations.append(ingredient)
    print("\n")
    print("-" * 20)
    print(f"Found {len(only_citations)} citations, sanitized for easy copy/paste to verse2image:")
    for x in only_citations:
        result = re.sub(r',\s*', '-', x)
        print(result)
    if not matches_found:
        print("No matches found.")


def main():
    parser = argparse.ArgumentParser(description="Download webpage, save to temp file, and process matches.")
    parser.add_argument("url", help="URL to download")
    parser.add_argument("--tmpdir", help="Temporary directory to save downloaded pages, if not provided will write to system tmpdir, e.g. --tmpdir [/path/to/file/]")
    parser.add_argument("--keeptmp",default=False, help="False by default, if provided the raw tmp Download webpage will not be deleted at the end", action="store_true")

    args = parser.parse_args()
    keeptmp: bool = args.keeptmp
    tmpdir = args.tmpdir
    try:
        text = download_text(args.url)
        title = BeautifulSoup(text, 'html.parser').title.string
        if tmpdir is None:
            temp_path = os.path.join(tempfile.gettempdir(), "downloaded_page.txt")
        else:
            temp_path = os.path.join(tmpdir, "downloaded_page.txt")

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(text)

        print("\n")
        print("-------- " + title + " --------")
        print("\n")
        print(f"Downloaded page saved to:\n{temp_path}\n")
        print("Cleaning Download and writing out to temp file.")
        print("-" * 20)
        cleanedtext = cleandownload(text)
        if tmpdir is None:
            temp_path2 = os.path.join(tempfile.gettempdir(), "downloaded_page_clean.txt")
        else:
            temp_path2 = os.path.join(tmpdir, "downloaded_page_clean.txt")
        with open(temp_path2, "w", encoding="utf-8") as f:
            f.write(cleanedtext)
        print("Processed Matches")
        print("-" * 20)
        #todo
        # have search_text return a dic that can be iterated to be passed to verse2image, needed for
        # integration into UI, change the printing to terminal to outputing to the label that of the UI as
        # a progress indicator
        search_text(cleanedtext, False)
        if not keeptmp:
            os.remove(temp_path2)
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()