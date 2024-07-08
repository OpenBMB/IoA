# Based on https://github.com/microsoft/autogen/blob/19de99e3f6e46f6040d54c4a55785d02158dec28/autogen/browser_utils.py

import io
import re
import sys
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

# sys.path.append(".")
# sys.path.append("./im_client")
import threading

import requests
from llms import OpenAIChat
from llms.utils import count_string_tokens
from playwright.async_api import Error, async_playwright


# Event to signal the completion of PDF download
pdf_downloaded_event = threading.Event()


IS_PDF_CAPABLE = False
try:
    import pdfminer
    import pdfminer.high_level

    IS_PDF_CAPABLE = True
except ModuleNotFoundError:
    pass

try:
    import pathvalidate
except ModuleNotFoundError:
    pass


class SimpleTextBrowser:
    """An extremely simple text-based web browser based on Playwright."""

    def __init__(
        self,
        # start_page: Optional[str] = None,
        viewport_size: Optional[int] = 1024 * 5,
        downloads_folder: Optional[Union[str, None]] = None,
        bing_base_url: str = "https://api.bing.microsoft.com/v7.0/search",
        bing_api_key: Optional[Union[str, None]] = None,
    ):
        self.start_page: str = "about:blank"
        self.viewport_size = viewport_size
        self.downloads_folder = downloads_folder
        self.history: List[str] = list()
        self.page_title: Optional[str] = None
        self.viewport_current_page = 0
        self.viewport_pages: List[Tuple[int, int]] = list()
        # self.set_address(self.start_page)
        self.history.append("about:blank")
        self._set_page_content("")
        self.bing_base_url = bing_base_url
        self.bing_api_key = bing_api_key

        self._page_content = ""

    @property
    def address(self) -> str:
        """Return the address of the current page."""
        return self.history[-1]

    async def set_address(self, uri_or_path: str) -> None:
        self.history.append(uri_or_path)

        # Handle special URIs
        if uri_or_path == "about:blank":
            self._set_page_content("")
        elif uri_or_path.startswith("bing:"):
            self._bing_search(uri_or_path[len("bing:") :].strip())
        else:
            if not uri_or_path.startswith("http:") and not uri_or_path.startswith("https:"):
                uri_or_path = urljoin(self.address, uri_or_path)
                self.history[-1] = uri_or_path  # Update the address with the fully-qualified path
            await self._fetch_page(uri_or_path)

        self.viewport_current_page = 0

    async def _fetch_page(self, url: str) -> None:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                request = context.request

                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )

                try:
                    await page.goto(url, wait_until="networkidle")
                    self.page_title = await page.title()
                    html_content = await page.content()
                    self._process_html_content(html_content)
                except Error:
                    response = await request.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                        },
                    )
                    content_type = response.headers.get("content-type", "").lower()

                    if "application/pdf" in content_type and IS_PDF_CAPABLE:
                        pdf_content = await response.body()
                        pdf_data = io.BytesIO(pdf_content)
                        self.page_title = None
                        self._set_page_content(pdfminer.high_level.extract_text(pdf_data))
                    else:
                        html_content = await response.text()
                        self._process_html_content(html_content)

                await browser.close()
        except Exception as e:
            self.page_title = "Error"
            self._set_page_content(str(e))

    def _process_html_content(self, html_content: str) -> None:
        import markdownify
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove javascript and style blocks
        for script in soup(["script", "style"]):
            script.extract()

        for img in soup.find_all("img"):
            if "src" in img.attrs and img.attrs["src"].startswith("data:image"):
                img.extract()

        if self.history[-1].startswith("https://en.wikipedia.org/"):
            body_elm = soup.find("div", {"id": "mw-content-text"})
            title_elm = soup.find("span", {"class": "mw-page-title-main"})

            if body_elm:
                # What's the title
                main_title = soup.title.string
                if title_elm and len(title_elm) > 0:
                    main_title = title_elm.string
                webpage_text = "# " + main_title + "\n\n" + markdownify.MarkdownConverter().convert_soup(body_elm)
            else:
                webpage_text = markdownify.MarkdownConverter().convert_soup(soup)
        else:
            webpage_text = markdownify.MarkdownConverter().convert_soup(soup)

        webpage_text = markdownify.markdownify(str(soup), heading_style="ATX")
        webpage_text = re.sub(r"\r\n", "\n", webpage_text)
        webpage_text = re.sub(r"\n{2,}", "\n\n", webpage_text).strip()

        self.page_title = soup.title.string
        self._set_page_content(webpage_text)

    def _set_page_content(self, content: str) -> None:
        """Sets the text content of the current page."""
        self._page_content = content
        self._split_pages()
        if self.viewport_current_page >= len(self.viewport_pages):
            self.viewport_current_page = len(self.viewport_pages) - 1

    @property
    def page_content(self) -> str:
        """Return the full contents of the current page."""
        return self._page_content

    @property
    def viewport(self) -> str:
        """Return the content of the current viewport."""
        bounds = self.viewport_pages[self.viewport_current_page]
        return self.page_content[bounds[0] : bounds[1]]

    def _split_pages(self) -> None:
        # Split only regular pages
        if not self.address.startswith("http:") and not self.address.startswith("https:"):
            self.viewport_pages = [(0, len(self._page_content))]
            return

        # Handle empty pages
        if len(self._page_content) == 0:
            self.viewport_pages = [(0, 0)]
            return

        # Break the viewport into pages
        self.viewport_pages = []
        start_idx = 0
        while start_idx < len(self._page_content):
            end_idx = min(start_idx + self.viewport_size, len(self._page_content))  # type: ignore[operator]
            # Adjust to end on a space
            while end_idx < len(self._page_content) and self._page_content[end_idx - 1] not in [" ", "\t", "\r", "\n"]:
                end_idx += 1
            self.viewport_pages.append((start_idx, end_idx))
            start_idx = end_idx

    def page_down(self) -> None:
        self.viewport_current_page = min(self.viewport_current_page + 1, len(self.viewport_pages) - 1)

    def page_up(self) -> None:
        self.viewport_current_page = max(self.viewport_current_page - 1, 0)

    async def visit_page(self, path_or_uri: str) -> str:
        """Update the address, visit the page, and return the content of the viewport."""
        await self.set_address(path_or_uri)
        return self.viewport

    def _bing_api_call(self, query: str) -> Dict[str, Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]]:
        # Make sure the key was set
        if self.bing_api_key is None:
            raise ValueError("Missing Bing API key.")

        # Prepare the request parameters
        request_kwargs = {}
        request_kwargs["headers"] = {}
        request_kwargs["headers"]["Ocp-Apim-Subscription-Key"] = self.bing_api_key

        if "params" not in request_kwargs:
            request_kwargs["params"] = {}
        request_kwargs["params"]["q"] = query
        request_kwargs["params"]["textDecorations"] = False
        request_kwargs["params"]["textFormat"] = "raw"

        request_kwargs["stream"] = False

        # Make the request
        response = requests.get(self.bing_base_url, **request_kwargs)
        response.raise_for_status()
        results = response.json()

        return results  # type: ignore[no-any-return]

    def _bing_search(self, query: str) -> None:
        results = self._bing_api_call(query)

        web_snippets: List[str] = list()
        idx = 0
        for page in results["webPages"]["value"]:
            idx += 1
            web_snippets.append(f"{idx}. [{page['name']}]({page['url']})\n{page['snippet']}")
            if "deepLinks" in page:
                for dl in page["deepLinks"]:
                    idx += 1
                    web_snippets.append(
                        f"{idx}. [{dl['name']}]({dl['url']})\n{dl['snippet'] if 'snippet' in dl else ''}"  # type: ignore[index]
                    )

        news_snippets = list()
        if "news" in results:
            for page in results["news"]["value"]:
                idx += 1
                news_snippets.append(f"{idx}. [{page['name']}]({page['url']})\n{page['description']}")

        self.page_title = f"{query} - Search"

        content = (
            f"A Bing search for '{query}' found {len(web_snippets) + len(news_snippets)} results:\n\n## Web Results\n"
            + "\n\n".join(web_snippets)
        )
        if len(news_snippets) > 0:
            content += "\n\n## News Results:\n" + "\n\n".join(news_snippets)
        self._set_page_content(content)


def _browser_state(browser: SimpleTextBrowser) -> Tuple[str, str]:
    header = f"Address: {browser.address}\n"
    if browser.page_title is not None:
        header += f"Title: {browser.page_title}\n"

    current_page = browser.viewport_current_page
    total_pages = len(browser.viewport_pages)
    header += f"Viewport position: Showing page {current_page+1} of {total_pages}.\n"
    return (header, browser.viewport)


async def informational_web_search(browser: SimpleTextBrowser, query: str) -> str:
    await browser.visit_page(f"bing: {query}")
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def navigational_web_search(browser: SimpleTextBrowser, query: str):
    await browser.visit_page(f"bing: {query}")

    # Extract the first linl
    m = re.search(r"\[.*?\]\((http.*?)\)", browser.page_content)
    if m:
        await browser.visit_page(m.group(1))

    # Return where we ended up
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def visit_page(browser: SimpleTextBrowser, url: str):
    await browser.visit_page(url)
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def download_file(browser: SimpleTextBrowser, url: str):
    await browser.visit_page(url)
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def page_up(browser: SimpleTextBrowser):
    browser.page_up()
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def page_down(browser: SimpleTextBrowser):
    browser.page_down()
    header, content = _browser_state(browser)
    return header.strip() + "\n=======================\n" + content


async def find_on_page_ctrl_f(browser: SimpleTextBrowser, search_string: str):
    find_result = browser.find_on_page(search_string)
    header, content = _browser_state(browser)

    if find_result is None:
        return (
            header.strip()
            + "\n=======================\nThe search string '"
            + search_string
            + "' was not found on this page."
        )
    else:
        return header.strip() + "\n=======================\n" + content


async def find_next(browser: SimpleTextBrowser):
    find_result = browser.find_next()
    header, content = _browser_state(browser)

    if find_result is None:
        return header.strip() + "\n=======================\nThe search string was not found on this page."
    else:
        return header.strip() + "\n=======================\n" + content


async def read_page_and_answer(
    browser: SimpleTextBrowser,
    summarization_client: OpenAIChat,
    question: str,
    url: str | None = None,
):
    if url is not None and url != browser.address:
        await browser.visit_page(url)

    limit = 32000

    buffer = ""
    for line in re.split(r"([\r\n]+)", browser.page_content):
        tokens = count_string_tokens(buffer + line, summarization_client.args.model)
        if tokens + 1024 > limit:  # Leave room for our summary
            break
        buffer += line

    buffer = buffer.strip()
    if len(buffer) == 0:
        return "Nothing to summarize."

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can summarize long documents to answer question.",
        }
    ]

    prompt = f"Please summarize the following into one or two paragraph:\n\n{buffer}"
    if question is not None:
        prompt = f"Please summarize the following into one or two paragraphs with respect to '{question}':\n\n{buffer}"

    messages.append(
        {"role": "user", "content": prompt},
    )

    try:
        response = await summarization_client.agenerate_response(history=messages)  # type: ignore[union-attr]
    except Exception as e:
        return str(e)
    return response.content


async def summarize_page(
    browser: SimpleTextBrowser,
    summarization_client: OpenAIChat,
    url: str | None = None,
):
    return await read_page_and_answer(browser, summarization_client, url=url, question=None)
