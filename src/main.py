import os
import time
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ==========================================
# 1. 설정: 요일별 QA 기술 테마 (월~토)
# ==========================================
CATEGORY_MAP = {
    0: { "name": "🌐 웹 프론트엔드 (UI Test & Framework)", "queries": ["topic:react", "topic:typescript", "topic:nextjs"] },
    1: { "name": "📱 모바일 앱 (Mobile Testing)", "queries": ["topic:android", "topic:ios", "topic:flutter"] },
    2: { "name": "🧪 테스트 자동화 & API 도구", "queries": ["topic:playwright", "topic:cypress", "topic:postman", "topic:selenium"] },
    3: { "name": "🏗️ CI/CD & 인프라 (DevOps)", "queries": ["topic:jenkins", "topic:docker", "topic:github-actions", "topic:kubernetes"] },
    4: { "name": "⚙️ 백엔드 & 자프링 (Enterprise)", "queries": ["topic:spring-boot", "topic:spring-framework", "language:java"] },
    5: { "name": "🤖 AI 에이전트 & 데이터 분석", "queries": ["topic:ai-agent", "topic:langchain", "topic:pandas", "topic:grafana"] }
}

# ==========================================
# 2. 데이터 수집: GitHub Search API 호출
# ==========================================
def get_github_search_trends(query):
    """특정 키워드의 최근 7일간 인기 프로젝트 상위 5개를 가져옵니다."""
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = "https://api.github.com/search/repositories"
    
    params = {
        "q": f"{query} pushed:>{seven_days_ago}",
        "sort": "stars",
        "order": "desc",
        "per_page": 5 
    }
    
    headers = {}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200: 
            print(f"⚠️ [{query}] 데이터 수집 실패: {response.status_code}")
            return []
        
        items = response.json().get('items', [])
        repos = []
        
        for item in items:
            desc_en = item['description'] if item['description'] else "설명이 없습니다."
            try:
                desc_ko = GoogleTranslator(source='auto', target='ko').translate(desc_en)
                if len(desc_ko) > 150: 
                    desc_ko = desc_ko[:147] + "..."
            except:
                desc_ko = desc_en

            repos.append({
                'name': item['full_name'],
                'link': item['html_url'],
                'stars': item['stargazers_count'],
                'desc': desc_ko
            })
        return repos
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return []

# ==========================================
# 3. 메시지 생성: 트렌드 한 줄 요약
# ==========================================
def generate_trend_summary(category_name, all_results):
    keywords = [q.replace("topic:", "").replace("language:", "").upper() for q in all_results.keys()]
    total_count = sum(len(repos) for repos in all_results.values())
    
    if total_count == 0:
        return "오늘은 새로운 주요 업데이트 소식이 없습니다."
    
    return f"오늘의 {category_name} 트렌드는 **{', '.join(keywords)}** 중심으로 총 {total_count}개의 핫한 프로젝트가 선정되었습니다."

# ==========================================
# 4. 메시지 전송: Discord Webhook 연동
# ==========================================
def send_discord_message(category_name, all_results):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url: 
        print("⚠️ DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        return

    # 한국 시간 기준 날짜 출력
    today = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
    summary = generate_trend_summary(category_name, all_results)

    content = f"## 📢 오늘의 QA 기술 리포트\n"
    content += f"📅 **날짜**: {today}\n"
    content += f"💡 **한 줄 요약**: {summary}\n"
    content += "---"

    for query, repos in all_results.items():
        display_name = query.replace("topic:", "").replace("language:", "").upper()
        content += f"\n### 🔍 {display_name} 테마 TOP 5\n"
        
        if not repos:
            content += "> 검색 결과가 없습니다.\n"
            continue
            
        for idx, repo in enumerate(repos, 1):
            content += f"**{idx}. {repo['name']}** (⭐ `{repo['stars']}`)\n"
            content += f"> {repo['desc']}\n"
            content += f"- [코드 보기]({repo['link']})\n"
            
    # 디스코드는 한 번에 2000자까지만 전송 가능하므로 안전하게 길이 조절
    if len(content) > 2000:
        content = content[:1900] + "...\n\n(🚨 메시지가 길어 일부가 생략되었습니다. 더 많은 정보는 GitHub에서 확인하세요!)"
        
    res = requests.post(webhook_url, json={"content": content})
    if res.status_code == 204:
        print(f"✅ [{category_name}] 디스코드 전송 완료!")
    else:
        print(f"❌ 전송 실패: {res.status_code}")

# ==========================================
# 5. 메인 실행 로직
# ==========================================
if __name__ == "__main__":
    # GitHub Actions 서버는 UTC 기준이므로 한국 시간(KST, UTC+9)으로 보정
    current_day = (datetime.utcnow() + timedelta(hours=9)).weekday()
    
    if current_day in CATEGORY_MAP:
        category = CATEGORY_MAP[current_day]
        print(f"=== {category['name']} 분석 시작 ===")
        
        final_results = {}
        for q in category['queries']:
            trends = get_github_search_trends(q)
            if trends:
                final_results[q] = trends
            time.sleep(1)
            
        send_discord_message(category['name'], final_results)
    else:
        print("오늘은 일요일입니다. 봇도 휴식을 취합니다! 💤")
