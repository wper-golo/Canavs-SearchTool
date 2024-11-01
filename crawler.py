import json
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 设置浏览器选项
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # 不显示浏览器窗口
options.add_argument('--disable-gpu')
# no download no pictures and videos
prefs = {
    "download.default_directory": "/dev/null",
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.videos": 2
}
options.add_experimental_option("prefs", prefs)
# options.add_argument('--no-sandbox')



# Install ChromeDriver using ChromeDriverManager and wrap the path with Service
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


class Crawler:
    def __init__(self, start_url, course_url, group_url, depth_limit):
        self.course_url = course_url
        self.group_url = group_url
        self.start_url = start_url
        self.depth_limit = depth_limit
        self.visited = set()

    def find_links(self):
        # Get the page source
        page_source = driver.page_source
        with open("test.html", "w") as f:
            f.write(page_source)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all <a> elements that are not descendants of a <header> with id 'header'
        links = [a for a in soup.find_all('a', href=True) if not a.find_parent('header', id='header')]

        filtered_links = []
        for link in links:
            href = link.get('href')
            if href and (href.startswith(self.course_url) or href.startswith(self.group_url)) and "#" not in href and href not in self.visited:
                filtered_links.append(link)
                # print(link.get('href'))

        return filtered_links

    def deep_crawl(self, url, depth):
        if depth == 0 or url in self.visited:
            return

        # try:
        driver.get(url)
        # wait for the page to load
        time.sleep(1)
        # save page source into web-cache dir, named by the title of the page
        filename = driver.title.replace('/', '_')
        # if filename start with BUS or HUM skip
        if filename.startswith("BUS") or filename.startswith("HUM"):
            return
        with open(f"web-cache/{filename}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)


        print(f"Depth {depth}: {driver.title} - {url}")

        self.visited.add(url)

        links = self.find_links()

        for link in links:
            href = link.get('href')
            self.deep_crawl(href, depth - 1)


        # except Exception as e:
        #     print(f"Error occurred at Link: {url} , Error: {e}", file=sys.stderr)
        #     return

    def login(self):
        try:
            driver.get("https://canvas.sydney.edu.au/")
            # 读取 cookies
            if os.path.exists("cookies.json"):
                with open("cookies.json", "r") as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        cookie['domain'] = '.sydney.edu.au'
                        driver.add_cookie(cookie)
            # 等待页面加载完成
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("Page is fully loaded!")
        except Exception as e:
            print(f"Error occurred: {e}")

        # 检测是否有可以登陆 如果访问start_url没有跳转就是已经登录 跳转了就是未登录
        driver.get(self.start_url)
        driver.get(self.start_url)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        if driver.current_url == self.start_url:
            print("Already logged in!")
            return

        # 否则登录
        driver.get("https://canvas.sydney.edu.au/")
        input("Login First, Press Enter to continue...")
        # 保存登录后的 cookies
        with open("cookies.json", "w") as f:
            cookies = driver.get_cookies()
            json.dump(cookies, f)

    def start(self):
        # 登录
        self.login()
        self.deep_crawl(self.start_url, self.depth_limit)


def main():
    course_url = "https://canvas.sydney.edu.au/courses/61585"
    group_url = "https://canvas.sydney.edu.au/groups/624156/pages"
    start_url = "https://canvas.sydney.edu.au/groups/624156/pages"
    depth_limit = 99 # 设置最大深度
    crawler = Crawler(start_url, course_url, group_url, depth_limit)
    crawler.start()
    input("Press Enter to close the browser...")
    # close the browser
    driver.quit()

if __name__ == '__main__':
    main()