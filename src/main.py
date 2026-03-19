import os
import time
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ==========================================
# 1. 설정: 요일별 QA 기술 테마 (월~토)
# ==========================================
CATEGORY_MAP = {
    0: { 
        "name": "🌐 웹 프론트엔드", 
        # 🔥 TS 제거, Vue 추가, React 검색 시 모바일(React-Native) 완벽 분리
        "queries": ["topic:react -topic:react-native -repo:facebook/react", "topic:nextjs -repo:shadcn-ui/ui", "topic:vue -repo:vuejs/vue"] 
    },
    1: { 
        "name": "📱 모바일 앱", 
        "queries": ["topic:flutter", "topic:react-native", "language:kotlin topic:android", "language:swift topic:ios"] 
    },
    2: { 
        "name": "🧪 테스트 자동화 & API 도구", 
        "queries": ["topic:playwright", "topic:cypress", "topic:postman", "topic:selenium"] 
    },
    3: { 
        "name": "🏗️ CI/CD & 인프라 (DevOps)", 
        "queries": ["topic:jenkins", "topic:kubernetes", "topic:docker", "topic:github-actions"] 
    },
    4: { 
        "name": "⚙️ 백엔드", 
        "queries": ["topic:spring", "language:go", "language:rust", "topic:nodejs"] 
    },
    5: { 
        "name": "🤖 AI 에이전트 & 데이터 분석", 
        "queries": ["topic:ai-agent", "topic:langchain", "topic:pandas", "topic:grafana"] 
    }
}

EMOJI_MAP = {
    "REACT": "⚛️", "REACT-NATIVE": "📱", "VUE": "🟩", "NEXTJS": "▲",
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
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    # 🔥 핵심 비법: 최근 2년(730일) 이내에 만들어진 신규 핫플 프로젝트만 가져옵니다! (고인물 원천 차단)
    two_years_ago = (datetime.utcnow() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    url = "https://api.github.com/search/repositories"
    
    params = {
        # pushed(최근 업데이트)와 created(생성일) 조건을 동시에 적용
        "q": f"{query} pushed:>{seven_days_ago} created:>{two_years_ago}",
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
    
    # 🛠️ [테스트 모드] 문제가 되었던 월요일(웹 프론트엔드)을 다시 테스트해봅시다!
    TEST_MODE = True
    TEST_DAY_NUMBER = 2  # 0: 월요일 (웹 프론트엔드)
    
    if TEST_MODE:
        current_day = TEST_DAY_NUMBER
        print(f"🛠️ [테스트 모드] {current_day}번 요일 데이터를 임시로 불러옵니다.")
    
    if current_day in CATEGORY_MAP:
        category = CATEGORY_MAP[current_day]
        print(f"=== {category['name']} 분석 시작 ===")
        
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
