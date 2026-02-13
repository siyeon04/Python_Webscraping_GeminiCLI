import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from wordcloud import WordCloud
from loguru import logger
import os
import re

# 로깅 설정
logger.add("yes24/log/eda_{time}.log", rotation="500 MB")

def preprocess_date(date_str):
    try:
        # '2025년 11월' 형식을 '2025-11'로 변환
        match = re.search(r'(\d{4})년\s*(\d{1,2})월', str(date_str))
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}"
        return None
    except Exception:
        return None

def run_analysis():
    # 경로 설정
    csv_path = 'yes24/data/yes24_ai.csv'
    plot_dir = 'yes24/plots'
    
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
        logger.info(f"디렉토리 생성: {plot_dir}")

    # 1. 데이터 불러오기
    logger.info("데이터 로드 중...")
    df = pd.read_csv(csv_path)

    # 2. 데이터 전처리
    logger.info("데이터 전처리 시작...")
    
    # 수치 데이터 변환
    numeric_cols = ['정가', '판매가', '리뷰 수', '판매지수']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 발행일 처리
    df['발행연월'] = df['발행일'].apply(preprocess_date)
    df['발행일_dt'] = pd.to_datetime(df['발행연월'], format='%Y-%m', errors='coerce')
    df['발행연도'] = df['발행일_dt'].dt.year
    df['발행월'] = df['발행일_dt'].dt.month

    # 할인율 계산
    df['할인율'] = ((df['정가'] - df['판매가']) / df['정가'] * 100).fillna(0)

    # 3. EDA - 통계 요약
    logger.info("통계 분석 수행 중...")
    summary = df[['판매지수', '리뷰 수', '판매가', '할인율']].describe()
    logger.info("통계 요약:\n{}", summary)

    # 4. 시각화
    logger.info("시각화 생성 중...")

    # (1) 판매지수 상위 10권
    plt.figure(figsize=(12, 10))
    top_10 = df.nlargest(10, '판매지수')
    plt.barh(top_10['제목'], top_10['판매지수'], color='skyblue')
    plt.xlabel('판매지수')
    plt.title('YES24 AI 도서 판매지수 TOP 10')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(f'{plot_dir}/top_10_sales.png')
    plt.close()

    # (2) 리뷰 수 vs 판매지수 상관관계
    plt.figure(figsize=(10, 6))
    plt.scatter(df['리뷰 수'], df['판매지수'], alpha=0.5, color='orange')
    plt.xlabel('리뷰 수')
    plt.ylabel('판매지수')
    plt.title('리뷰 수와 판매지수의 상관관계')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f'{plot_dir}/review_vs_sales.png')
    plt.close()

    # (3) 연도별 도서 발행 권수 추이
    plt.figure(figsize=(10, 6))
    # 0인 연도 제외 (전처리 실패 대비)
    yearly_counts = df[df['발행연도'] > 0].groupby('발행연도').size()
    if not yearly_counts.empty:
        yearly_counts.plot(kind='line', marker='o', color='green')
        plt.xlabel('발행연도')
        plt.ylabel('발행 권수')
        plt.title('연도별 AI 도서 발행 추이')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f'{plot_dir}/yearly_trend.png')
    plt.close()

    # (4) 워드클라우드 (제목 기반)
    logger.info("워드클라우드 생성 중...")
    text = " ".join(df['제목'].values)
    # 한글 폰트 경로 (Windows 기준 'Malgun Gothic')
    font_path = 'C:/Windows/Fonts/malgun.ttf' if os.name == 'nt' else '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    try:
        wc = WordCloud(
            font_path=font_path,
            width=800, height=400,
            background_color='white'
        ).generate(text)
        
        plt.figure(figsize=(15, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title('AI 도서 제목 주요 키워드')
        plt.savefig(f'{plot_dir}/wordcloud.png')
        plt.close()
    except Exception as e:
        logger.error("워드클라우드 생성 실패: {}", e)

    logger.info("모든 분석 및 시각화 완료. 결과는 yes24/plots 디렉토리에 저장되었습니다.")

if __name__ == "__main__":
    run_analysis()
