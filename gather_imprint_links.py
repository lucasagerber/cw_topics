"""
gather_imprint_links
Lucas A. Gerber
"""


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup as soup
import urllib.request
from time import sleep
from random import randint
import os
import pandas as pd


# Function to extract article information from link
def exract_article_from_link(url, headers, save_html=True):
     """
    Extracts article text and information from url.
    Returns article information as list.
    """
    request = urllib.request.Request(url, headers=headers)

    # Open link, read, and convert to beautiful soup 
    with urllib.request.urlopen(request) as url:
        url_html = url.read()

    url_soup = soup(url_html, 'html.parser')
    
    if save_html:
        out_file_name = "/articles/" + url + ".txt"
        with open(out_file_name, "w") as file:
            file.write(url_html)
    
    try:
        article_title = url_soup.find('h1').get_text()
        article_date = url_soup.find(class_='pf-date').get_text()
        article_author = url_soup.find('author').get_text().strip('By ')
        article_tags = ", ".join([a.get_text() for a in url_soup.find(class_='article-tags').find_all('a')])
        article_type = url.split('/')[3]
        article_text = '\n'.join([p.get_text() for p in url_soup.find(class_='article-content').find_all('p')])
        
        article_list = [url, article_title, article_date, article_author, article_tags, article_type, article_text]
    except Exception as e:
        print("Error:", e, url)
        article_list =  [url, '','','','','','']
        
    return article_list


# Function to extract article links from web page
def extract_article_links(html):
    """
    Extracts article links from html.
    Returns number of articles and list of links.
    """
    page_soup = soup(html, "html.parser")
    article_as = page_soup.findAll("a", {"class": "article-preview-link"})
    article_links = [article.get('href') for article in article_as]
    
    return len(article_links), article_links


# Function to open web browser & extract articles
def load_all_articles(browser, url, load_more=True):
    """
    Takes a topic url from ImprintNews and extracts all article preview links.
    Returns number of articles and list of links.
    """

    browser.get(url)

    page_html = browser.page_source
    n_article_links_old, article_links = extract_article_links(page_html)
    print("Articles:",  n_article_links_old)
    
    while load_more:
        sleep(randint(3, 12))
        try:
            print("Loading more articles...")
            
            # Move to footer
            print("Moving to footer...")
            footer = browser.find_element(By.CLASS_NAME, 'body--footer')
            hover_footer = ActionChains(browser).move_to_element(footer)
            hover_footer.perform()
            sleep(randint(1,3))

            # Move to load more button on bottom
            print("Moving to load more button...")
            load_more_button = browser.find_element(By.CLASS_NAME, 'alm-load-more-btn')
            click_load_more = ActionChains(browser).move_to_element(load_more_button).click()
            click_load_more.perform()
            print("Performed button hover/click.")
            sleep(randint(3, 12))
            
        except Exception as e:
            print("Error:", e)
            break

        page_html = browser.page_source
        n_article_links_new, article_links = extract_article_links(page_html)
        print("Articles:", n_article_links_old, "to", n_article_links_new)

        if n_article_links_old >= n_article_links_new:
            print("Done loading...", n_article_links_old, "to", n_article_links_new)
            break
        else:
            n_article_links_old = n_article_links_new

    page_soup = soup(browser.page_source, "html.parser")
    browser.quit()
    
    return len(article_links), article_links, page_soup
    

def main():
    """
    Run load_all_articles on the ImprintNews child welfare topic.
    Write out each article link.
    """
    # If hasn't been run already, then load all article links from child welfare archives
    if not os.path.exists("imprint_child-welfare_article_links.txt"):
        browser = webdriver.Chrome()
        imprint_url = 'https://imprintnews.org/topic/child-welfare-2'

        n_articles, articles, soup = load_all_articles(browser, imprint_url, load_more=True)
        
        with open("imprint_child-welfare_article_links.txt", "w") as file:
            for article in articles:
                file.write(article + '\n')
            
        print("Completed. Articles:", n_articles)
    
    # Load text file where article links are and download each article into dataframe
    print("Loading article links...")
    with open("imprint_child-welfare_article_links.txt", "r") as file:
        article_links = file.readlines()
        
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'}

    article_list_of_lists = [extract_article_from_link(link, headers) for link in article_links]
    article_columns = ["url","title","date","author","tags","type","text"]
    
    print("Creating dataframe...")
    article_df = pd.DataFrame.from_dict(data, columns=article_columns, orient='index')
    article_df.to_csv('imprint_articles_df.csv')
    print("Saved dataframe. Done.")


if __name__ == '__main__':
    main()
