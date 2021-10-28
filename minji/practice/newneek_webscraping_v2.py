'''뉴닉에서 '원문-쉬운글' pair 데이터 크롤링'''
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import time
import csv
import requests
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import original_text  # newneek 패키지의 모듈 임포트

def make_csv_file(filename):   # 1. 웹데이터를 수집할 csv 파일을 만듭니다.
    f = open(filename, "w", encoding='utf-8-sig', newline="")
    writer = csv.writer(f)
    col_name = "id category title date summary original_text url".split()  # column 에 대한 설명 첫행에 추가
    writer.writerow(col_name)
    return writer


def more_loading(browser):
    while True:     # 더보기 버튼 계속 누르기
        try:
            element = browser.find_element_by_xpath('//button[text()="더보기"]')
            browser.execute_script("arguments[0].click();", element)
            time.sleep(3)      #페이지 로딩 대기
        except:
            break


def main():
    writer = make_csv_file('newneek.csv')   # 1. 웹데이터를 수집할 csv 파일을 만듭니다.

    # 2. selenium 과 BeautifulSoup을 활용해 크롤링을 진행합니다.
    options = webdriver.ChromeOptions()
    # options.headless=True
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars --disable-extensions")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36")
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"
    browser = webdriver.Chrome(desired_capabilities=caps, options=options)   # selenium driver 크롬
    url = "https://www.newneek.co"  # 뉴닉 페이지 이동
    browser.get(url)
    time.sleep(5)
 
    more_loading(browser)   # 더보기 버튼 계속 누르기

    # 로딩이 완료된 후 card element 찾기
    cards = browser.find_elements_by_class_name("card  ")   # 기사 card element 찾기

    # https://www.newneek.co 의 기사들(card)을 하나씩 열며 진행합니다.
    for idx, card in enumerate(cards):
        card.send_keys(Keys.COMMAND+"\n")   # card를 다른 탭으로 열기
        browser.switch_to_window(browser.window_handles[1])       # 새로 연 탭으로 이동
        
        time.sleep(2)   # 로딩 대기
        soup = BeautifulSoup(browser.page_source, 'lxml')    # soup 객체로 웹페이지 스크래핑
        # 각 기사의 카테고리, 제목, 날짜 데이터를 웹페이지로부터 수집합니다.
        try: category = soup.find("a", attrs={"class":"post-head-runninghead"}).get_text() # 카테고리
        except: category = 'NULL'  # 카테고리가 없는 기사의 경우는 'NULL'로 지정
        try: title = soup.find("h2", attrs={"class":"post-head-headline"}).get_text() # 제목
        except: title = 'NULL'
        try: date = soup.find("time", attrs={"class":"post-head-date"}).get_text()  # 날짜
        except: date = 'NULL'
        
        # 기사내용을 담은 paragraph 에서 요약문, 원문을 추출
        paragraphs = soup.find_all("p")
        for paragraph in paragraphs:
            try: 
                url = paragraph.find("a", {"target":"_blank"})['href']  # 원문 링크가 있는 paragraph만 추출
            except: continue
            
            sum = paragraph.get_text()   # 요약문 추출
            sum = re.sub(r'[\n\r\t]','', sum)  # 전처리
            
            # 원문 기사를 selenium 으로 다른 탭에 열기
            browser.find_element_by_xpath('//a[@href="'+url+'"]').send_keys(Keys.COMMAND+"\n")
            time.sleep(4)
            browser.switch_to_window(browser.window_handles[2])       # 새로 연 탭으로 이동
            url = browser.current_url   # 현재 url 주소 가져오기
            
            original = original_text.main(url, browser)   # original_text 모듈에서 main함수로 원문기사 크롤링
            original = re.sub(r'[\n\r\t]','', original)
            
            # csv의 row에 들어갈 data를 list변수로 생성
            data=[idx, category, title, date, sum, original, url]
            print(data)
            writer.writerow(data)  # csv 파일에 행으로 쓰기
            browser.close()
            browser.switch_to_window(browser.window_handles[1])
        
        browser.close() # 현재 탭 닫기
        browser.switch_to_window(browser.window_handles[0]) # 첫번 째 탭(뉴닉 메인 페이지)으로 이동해서 다시 반복


if __name__ == "__main__":
    main()