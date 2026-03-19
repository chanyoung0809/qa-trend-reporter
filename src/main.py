import os
import time
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ==========================================
# 1. 설정: 요일별 QA 기술 테마 (월~토)
# ==========================================
# 🔥 개선: 공식 레포지토리(-repo)를 제외하여 생태계 주변의 핫한 프로젝트를 발굴합니다.
CATEGORY_MAP = {
    0: { 
        "name": "🌐 웹 프론트엔드", 
        "queries": ["topic:react -repo:facebook/react", "topic:typescript", "topic:nextjs -repo:vercel/next.js"] 
    },
    1: { 
        "name": "📱 모바일 앱", 
        "queries": ["topic:flutter -repo:flutter/flutter", "topic:react-native -repo:facebook/react-native", "language:kotlin topic:android", "language:swift topic:ios"] 
    },
    2: { 
        "name": "🧪 테스트 자동화 & API 도구", 
        "queries": ["topic:playwright -repo:microsoft/playwright", "topic:cypress -repo:cypress-io/cypress", "topic:postman", "topic:selenium -repo:SeleniumHQ/selenium"] 
    },
    3: { 
        "name": "🏗️ CI/CD & 인프라 (DevOps)", 
        "queries": ["topic:jenkins -repo:jenkinsci/jenkins", "topic:kubernetes -repo:kubernetes/kubernetes", "topic:docker -repo:docker/cli", "topic:github-actions"] 
    },
    4: { 
        "name": "⚙️ 백엔드", 
        # 🔥 개선: Spring으로 통합하고 Go, Rust, Node.js 추가
        "queries": ["topic:spring -repo:spring-projects/spring-boot", "language:go", "language:rust", "topic:nodejs -repo:nodejs/node"] 
    },
    5: { 
        "name": "🤖 AI 에이전트 & 데이터 분석", 
        "queries": ["topic:ai-agent", "topic:langchain -repo:langchain-ai/langchain", "topic:pandas -repo:pandas-dev/pandas", "topic:grafana -repo:grafana/grafana"] 
    }
}

EMOJI_MAP = {
    "REACT": "⚛️", "REACT-NATIVE": "📱", "TYPESCRIPT": "📘", "NEXTJS": "▲",
    "ANDROID": "🤖", "IOS": "🍏", "FLUTTER": "🦋",
    "PLAYWRIGHT": "🎭", "CYPRESS": "🌲", "POSTMAN": "📮", "SELENIUM": "✅",
    "JENKINS": "🤵‍♂️", "KUBERNETES": "☸️", "DOCKER": "🐳", "GITHUB-ACTIONS": "🐙", 
    "SPRING": "🌿", "GO": "🐹", "RUST": "🦀", "NODEJS": "🟢", 
    "AI-AGENT": "🤖", "LANGCHAIN": "🦜", "PANDAS": "🐼", "GRAFANA": "📊"
}

# ==========================================
# 2. 데이터 수집: GitHub Search API 호출
# ==========================================
def get_github_search_trends(query, fetch_limit):
    """최근 7일간 업데이트된 핫한 프로젝트를 가져옵니다."""
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = "https://api.github.com/search/repositories"
    
    params = {
        "q": f"{query} pushed:>{seven_days_ago}",
        "sort": "stars",
        "order": "desc",
        "per_page": fetch_limit 
    }
    
    headers = {}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200: return []
        
        items = response.json().get('items', [])
        repos = []
        
        for item in items:
            desc_en = item['description'] if item['description'] else "설명이 없습니다."
            try:
                desc_ko = GoogleTranslator(source='auto', target='ko').translate(desc_en)
                if len(desc_ko) > 130: desc_ko = desc_ko[:127] + "..."
            except:
                desc_ko = desc_en

            repos.append({
                'name': item['full_name'],
                'link': item['html_url'],
                'stars': int(item['stargazers_count']),
                'forks': int(item['forks_count']), 
                'desc': desc_ko
            })
        return repos
    except:
        return []

# ==========================================
# 3. 메시지 전송: Discord Webhook 연동
# ==========================================
def send_discord_message(category_name, all_results):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url: return

    now_kst = datetime.utcnow() + timedelta(hours=9)
    date_str = f"{now_kst.month}월 {now_kst.day}일"
    
    # 디스코드 요약본에 쓸 깔끔한 키워드 추출
    clean_keywords = []
    for q in all_results.keys():
        base_word = q.split()[0]
        clean_word = base_word.replace("topic:", "").replace("language:", "").upper()
        clean_keywords.append(clean_word)
        
    total_count = sum(len(repos) for repos in all_results.values())

    content = f"# 📢 {date_str} QA Tech Report\n"
    
    if total_count == 0:
        content += "오늘은 새로운 주요 업데이트 소식이 없습니다.\n"
    else:
        content += f"오늘의 {category_name} 트렌드는\n"
        content += f"**{', '.join(clean_keywords)}** 중심으로\n"
        content += f"총 {total_count}개의 핫한 프로젝트가 선정되었습니다.\n\n"

    for query, repos in all_results.items():
        if not repos: continue
        
        # 키워드 정리 (예: "topic:react -repo:..." -> "REACT")
        keyword = query.split()[0].replace("topic:", "").replace("language:", "").upper()
        emoji = EMOJI_MAP.get(keyword, "📌")
        
        content += f"## {emoji} {keyword} 테마 TOP {len(repos)}\n\n"
            
        for idx, repo in enumerate(repos, 1):
            stars_fmt = f"{repo['stars']:,}"
            forks_fmt = f"{repo['forks']:,}"
            
            content += f"### {idx}. [{repo['name']}]({repo['link']})\n"
            content += f" (⭐️ {stars_fmt} | 🍴 {forks_fmt})\n"
            content += f"> {repo['desc']}\n\n"
            
    if len(content) > 2000:
        content = content[:1900] + "...\n\n(🚨 메시지가 길어 일부가 생략되었습니다.)"
        
    requests.post(webhook_url, json={"content": content})
    print(f"✅ [{category_name}] 디스코드 전송 완료!")

# ==========================================
# 4. 메인 실행 로직
# ==========================================
if __name__ == "__main__":
    current_day = (datetime.utcnow() + timedelta(hours=9)).weekday()
    
    # 🛠️ [테스트 모드] 변경된 백엔드(금요일) 테마를 확인해봅시다!
    TEST_MODE = True
    TEST_DAY_NUMBER = 0  # 4: 금요일(백엔드/자프링/고/러스트/노드)
    
    if TEST_MODE:
        current_day = TEST_DAY_NUMBER
        print(f"🛠️ [테스트 모드] {current_day}번 요일 데이터를 임시로 불러옵니다.")
    
    if current_day in CATEGORY_MAP:
        category = CATEGORY_MAP[current_day]
        print(f"=== {category['name']} 분석 시작 ===")
        
        # 🔥 개선: 항목이 4개 이상이면 상위 2개, 3개 이하면 상위 3개로 노출 제한
        query_count = len(category['queries'])
        fetch_limit = 2 if query_count >= 4 else 3
        
        final_results = {}
        for q in category['queries']:
            trends = get_github_search_trends(q, fetch_limit)
            if trends:
                final_results[q] = trends
            time.sleep(1)
            
        send_discord_message(category['name'], final_results)
    else:
        print("오늘은 휴식일입니다! 💤")
