"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""
import re
import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
from argparse import Namespace
import bs4
import requests
from scraper import author
import pandas as pd


def get_genres(soup):
    genres = soup.find('div', {'data-testid': 'genresList'})
    try:
        genres = [genre.text.strip() for genre in genres.find_all('a')]
        return genres
    except:
        return ''

def get_isbn(soup):
    try:
        isbn = re.findall(r'nisbn: [0-9]{10}' , str(soup))[0].split()[1]
        return isbn
    except:
        return "isbn not found"

def get_num_pages(soup):
    if soup.find("span", {"itemprop": "numberOfPages"}):
        num_pages = soup.find("span", {"itemprop": "numberOfPages"}).text.strip()
        return int(num_pages.split()[0])
    return ""


def get_year_first_published(soup):
    year_first_published = soup.find("nobr", attrs={"class": "greyText"})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search("([0-9]{3,4})", year_first_published).group(1)
    else:
        return None


def get_author_id(soup):
    try:
        author_url = soup.find("a", {"class": "authorName"}).attrs.get("href")
        return author_url.split("/")[-1]
    except:
        print("cant get author")
        return "na/"


def get_description(soup):
    # genres = soup.find('div', {'data-testid': 'genresList'})
    desc = soup.find("div", {'data-testid': 'description'})
    desc = desc.text.strip()
    return desc
#.findAll("span")[-1].text

def get_title(soup):
    # genres = soup.find('div', {'data-testid': 'genresList'})
    title = soup.find("h1", {'data-testid': 'bookTitle'})
    title = title.text.strip()
    return title

def get_id(book_id):
    pattern = re.compile("([^.-]+)")
    return pattern.search(book_id).group()


def get_reviews(soup, book_id, username):
 
    reviews = []
    #<section class="ReviewText__content" dir="auto"><div class="TruncatedContent" tabindex="-1"><div class="TruncatedContent__text TruncatedContent__text--large TruncatedContent__text--expanded" tabindex="-1" data-testid="contentContainer"><span class="Formatted">I was offered a free advanced copy from Net Galley in exchange for an honest review. 4.5 stars<br><br>The story revolves around Brynn, who finds herself at the center of a school scandal. She becomes an outcast during her senior year for something she didn't even do. Also, the male at the center of the controversy won't come clean and the reactions to the incident make it apparent that there are different outcomes and expectations depending mostly on your gender.<br><br>I enjoyed this book which takes a deep dive into looking at inequalities in our culture. At first I was worried that despite having a good mix of representation it would vilify Christians but then as the book progresses this group is examined in a more nuanced light and I realized it was mainly one character who doesn't represent the group. I am always for books that make people question norms and whether they are fair. It also tackles the dynamics on families when there are addiction issues and how it can focus the attentions on that person and away from their other family members. It also shows the pressure for the non addicted family members to be perfect so as not to rock the boat any further. It delves into how to fight back against inequality and how to do it fairly.<br><br>All in all, the characters were well done and the pacing was good. Note- If you are a parent who monitors what their kids read this book does dive into issues around sex, teenage pregnancy, underage drinking, addiction, sexting and the like. Therefore if you have one of those advanced readers who isn't ready for conversations around mature content then maybe read it with them or have them wait a couple of years.</span></div><div class=""></div></div></section>
    reviews_list = soup.find_all('section', {'class': 'ReviewText__content'})
    reviewers_list = soup.find_all('div', {'class': 'ReviewerProfile__name'})
    #book_title = soup.find(id='bookTitle').text.strip()
    i = 0
    user_review = []
    for r in reviews_list:
        m = []
        r = r.text.strip()
        u = reviewers_list[i].text.strip()
        if u == username:
            user_review.append(u)
            user_review.append(r)
        else:
            m.append(u)
            m.append(r)
        i+=1
        reviews.append(m)

    return reviews, user_review

def get_rating_stats(soup):
    #<div class="RatingStatistics__meta" aria-label="9,603,683 ratings and 154,810 reviews" role="figure"><span data-testid="ratingsCount" aria-hidden="true">9,603,683<!-- -->&nbsp;<!-- -->ratings</span><span data-testid="reviewsCount" class="u-dot-before" aria-hidden="true">154,810<!-- -->&nbsp;<!-- -->reviews</span></div>
    ratings = soup.find('div', {'class': 'RatingStatistics__rating'})
    ratings = ratings.text.strip()

    return ratings

def get_author(soup):
    contributors = []
    #<section class="ReviewText__content" dir="auto"><div class="TruncatedContent" tabindex="-1"><div class="TruncatedContent__text TruncatedContent__text--large TruncatedContent__text--expanded" tabindex="-1" data-testid="contentContainer"><span class="Formatted">I was offered a free advanced copy from Net Galley in exchange for an honest review. 4.5 stars<br><br>The story revolves around Brynn, who finds herself at the center of a school scandal. She becomes an outcast during her senior year for something she didn't even do. Also, the male at the center of the controversy won't come clean and the reactions to the incident make it apparent that there are different outcomes and expectations depending mostly on your gender.<br><br>I enjoyed this book which takes a deep dive into looking at inequalities in our culture. At first I was worried that despite having a good mix of representation it would vilify Christians but then as the book progresses this group is examined in a more nuanced light and I realized it was mainly one character who doesn't represent the group. I am always for books that make people question norms and whether they are fair. It also tackles the dynamics on families when there are addiction issues and how it can focus the attentions on that person and away from their other family members. It also shows the pressure for the non addicted family members to be perfect so as not to rock the boat any further. It delves into how to fight back against inequality and how to do it fairly.<br><br>All in all, the characters were well done and the pacing was good. Note- If you are a parent who monitors what their kids read this book does dive into issues around sex, teenage pregnancy, underage drinking, addiction, sexting and the like. Therefore if you have one of those advanced readers who isn't ready for conversations around mature content then maybe read it with them or have them wait a couple of years.</span></div><div class=""></div></div></section>
    c_list = soup.find_all('span', {'class': 'ContributorLink__name'})
    #book_title = soup.find(id='bookTitle').text.strip()
    for r in c_list:
        r = r.text.strip()
        contributors.append(r)

    return contributors

def scrape_book(book_id: str, args: Namespace, username):
    url = "https://www.goodreads.com/book/show/" + book_id
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    pubDate = soup.find('p', {'data-testid': 'publicationInfo'})
    pubDate = pubDate.text.strip()
#<p data-testid="publicationInfo">First published October 3, 2023</p>
    pages = soup.find('p', {'data-testid': 'pagesFormat'})
    pages = pages.text.strip()
   # <p data-testid="pagesFormat">384 pages, Hardcover</p>
    reviews, userReview = get_reviews(soup, book_id, username)
    book = {
        "book_id_title": book_id,
        "book_id": get_id(book_id),
        "book_title": get_title(soup),
        "author": get_author(soup),
        "book_description": get_description(soup),
        "book_url": url,
        'isbn':                 get_isbn(soup),
        'publish date': pubDate,
        "genres": get_genres(soup),
        'page format': pages,
        "ratings": get_rating_stats(soup),
        "reviews": reviews,
        "user_review": userReview
    }
   
    
    return book
