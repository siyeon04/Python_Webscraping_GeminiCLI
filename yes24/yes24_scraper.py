import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from loguru import logger
import os

# 1. 로깅 설정
logger.add("yes24/yes24_scraping.log", rotation="500 MB")

def scrape_yes24():
    # 실제 데이터를 가져오는 URL
    base_url = "https://www.yes24.com/product/category/CategoryProductContents"
    
    # 해당 Request에 대한 Header 정보
    headers = {
        "host": "www.yes24.com",
        "referer": "https://www.yes24.com/product/category/display/001001003032",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    all_books = []
    
    # 4. 데이터 수집 프로세스: 1페이지부터 10페이지까지
    for page in range(1, 11):
        logger.info(f"페이지 {page} 수집 시작...")
        
        # Payload (Parameters)
        params = {
            "dispNo": "001001003032",
            "order": "SINDEX_ONLY",
            "addOptionTp": "0",
            "page": page,
            "size": "120", # 페이지당 120개 수집
            "statGbYn": "N",
            "viewMode": "",
            "_options": "",
            "directDelvYn": "",
            "usedTp": "0",
            "elemNo": "0",
            "elemSeq": "0",
            "seriesNumber": "0"
        }
        
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('div.itemUnit')
            
            if not items:
                logger.warning(f"{page}페이지에 수집할 데이터가 없습니다.")
                break
                
            for item in items:
                try:
                    # 제목
                    title_tag = item.select_one('a.gd_name')
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    
                    # 상세 페이지 URL
                    link = "https://www.yes24.com" + title_tag['href'] if title_tag and 'href' in title_tag.attrs else "N/A"
                    
                    # 저자
                    author_tag = item.select_one('span.info_auth a')
                    author = author_tag.get_text(strip=True) if author_tag else "N/A"
                    
                    # 출판사
                    pub_tag = item.select_one('span.info_pub a')
                    pub = pub_tag.get_text(strip=True) if pub_tag else "N/A"
                    
                    # 발행일
                    date_tag = item.select_one('span.info_date')
                    date = date_tag.get_text(strip=True) if date_tag else "N/A"
                    
                    # 가격 (판매가, 정가)
                    price_sale_tag = item.select_one('strong.txt_num em.yes_b')
                    price_sale = price_sale_tag.get_text(strip=True).replace(',', '') if price_sale_tag else "0"
                    
                    price_origin_tag = item.select_one('span.txt_num.dash em.yes_m')
                    price_origin = price_origin_tag.get_text(strip=True).replace(',', '') if price_origin_tag else price_sale
                    
                    # 리뷰 수
                    review_tag = item.select_one('span.rating_rvCount em.txC_blue')
                    review_count = review_tag.get_text(strip=True) if review_tag else "0"
                    
                    # 판매지수
                    sale_num_tag = item.select_one('span.saleNum')
                    sale_index = sale_num_tag.get_text(strip=True).replace('판매지수 ', '').replace(',', '') if sale_num_tag else "0"
                    
                    # 설명
                    desc_tag = item.select_one('div.info_read')
                    description = desc_tag.get_text(strip=True) if desc_tag else ""
                    
                    # 데이터 합치기
                    book_data = {
                        "제목": title,
                        "저자": author,
                        "출판사": pub,
                        "발행일": date,
                        "정가": price_origin,
                        "판매가": price_sale,
                        "리뷰 수": review_count,
                        "판매지수": sale_index,
                        "설명": description,
                        "상세 페이지 URL": link
                    }
                    all_books.append(book_data)
                    
                except Exception as e:
                    logger.error(f"아이템 파싱 중 오류 발생: {e}")
                    continue
            
            logger.info(f"{page}페이지 수집 완료: {len(items)}개 도서 추출")
            
            # 요청 간 적절한 시간 간격 (1-2초)
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            logger.error(f"{page}페이지 요청 실패: {e}")
            break

    # 5. 데이터 저장 형식 (CSV)
    if all_books:
        df = pd.DataFrame(all_books)
        
        # 저장 경로 설정
        data_dir = os.path.join('yes24', 'data')
        os.makedirs(data_dir, exist_ok=True)
        output_file = os.path.join(data_dir, 'yes24_ai.csv')
        
        # CSV 저장 (utf-8-sig로 한글 깨짐 방지)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"수집 성공! 총 {len(df)}개의 데이터를 '{output_file}'에 저장했습니다.")
        
        # 데이터프레임 일부 출력
        print("\n[수집 데이터 요약]")
        print(df.head())
    else:
        logger.warning("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    scrape_yes24()
