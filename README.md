# 🤖 GitHub Trend Bot (Discord Notification)

매일 지정된 시간에 **GitHub Trending(인기 리포지토리)** 정보를 수집하여 **Discord**로 알림을 보내주는 자동화 봇입니다.
5가지 주요 언어(Python, Java, JavaScript, TypeScript, Kotlin)의 일간 트렌드를 분석하고, 설명을 한국어로 번역하여 각 언어별 전용 채널로 전송합니다.

## ✨ 주요 기능 (Key Features)

* **📅 자동화된 스케줄:** GitHub Actions를 이용해 매일 한국 시간 낮 12:00 (UTC 03:00)에 자동 실행됩니다.
* **🔤 다양한 언어 지원:** 5개 프로그래밍 언어의 트렌드를 각각 수집합니다.
* **💬 자동 번역:** 리포지토리의 영문 설명을 `deep-translator`를 사용해 한국어로 번역합니다.
* **📢 채널별 분리 전송:** 언어별로 서로 다른 Discord Webhook을 사용하여, 관련된 채널에만 알림을 보냅니다.
* **🔒 보안:** Webhook URL은 GitHub Secrets로 안전하게 관리됩니다.

## 🛠 기술 스택 (Tech Stack)

* **Language:** Python 3.9
* **Libraries:** `requests`, `beautifulsoup4`, `deep-translator`
* **Infrastructure:** GitHub Actions (Cron Job)
* **Notification:** Discord Webhook 

## 📂 프로젝트 구조 (Structure)

```text
github-trend-bot/
├── .github/
│   └── workflows/
│       └── daily_trend.yml    # GitHub Actions 스케줄 설정
├── src/
│   ├── __init__.py
│   └── main.py                # 크롤링 및 디스코드 전송 로직
├── .gitignore
├── README.md
└── requirements.txt           # 의존성 패키지 목록

# 🤖 QA Tech-Trend Bot (운영진 셋업 가이드)

안녕하세요, 운영진 여러분! 🎉
이 봇은 우리 QA 교육생들에게 매일 낮 12시(월~토) 최신 기술 트렌드를 요약하여 디스코드로 자동 배달해 주는 든든한 조수입니다.

코딩을 전혀 모르시더라도 걱정하지 마세요! 아래 가이드만 순서대로 천천히 따라 하시면, 서버 관리 스트레스 없이 GitHub에서 10분 만에 자동화 봇을 띄우실 수 있습니다. 🚀

---

## 🛠 Step 1. 우리 팀 저장소로 가져오기 (Fork)
원본 코드를 건드리지 않고, 내 계정으로 안전하게 복사본을 가져오는 과정입니다.

1. 우측 상단에 있는 **`Fork`** 버튼을 클릭합니다.
2. 초록색 **`Create fork`** 버튼을 누르면 성공적으로 내 저장소로 복사됩니다!

---

## 📺 Step 2. 디스코드 웹후크(Webhook) 주소 만들기
봇이 메시지를 보낼 도착지(디스코드 채널)의 전용 우체통을 만듭니다.

1. 메시지를 받을 채널 이름 우측의 **`톱니바퀴(채널 편집)`** 아이콘 클릭.
2. **`연동(Integrations)`** > **`웹후크(Webhooks)`** > **`새 웹후크`** 클릭.
3. 봇의 이름(예: QA-나침반)과 이미지를 꾸며주고, **`웹후크 URL 복사`**를 눌러 메모장에 잘 보관해 둡니다.

---

## 🔑 Step 3. GitHub에 비밀키(Secrets) 안전하게 보관하기
복사한 디스코드 주소를 봇이 사용할 수 있도록 GitHub의 안전한 금고에 넣습니다.

1. Fork 해온 내 GitHub 저장소 페이지에서 **`Settings`** 탭을 클릭합니다.
2. 좌측 메뉴에서 **`Secrets and variables`** > **`Actions`**를 클릭합니다.
3. 초록색 **`New repository secret`** 버튼을 클릭합니다.
4. 아래 내용을 하나씩 등록해 줍니다.
   - **Name**: `DISCORD_WEBHOOK_URL` / **Secret**: (복사한 웹후크 주소 붙여넣기) -> `Add secret` 클릭
   - *(선택)* **Name**: `GH_TOKEN` / **Secret**: (발급받은 GitHub 토큰 붙여넣기) -> `Add secret` 클릭

---

## 🚀 Step 4. 작동 테스트 및 알람 켜기
자, 모든 준비가 끝났습니다! 이제 봇을 깨워볼까요?

1. 상단의 **`Actions`** 탭을 클릭합니다.
2. "I understand my workflows, go ahead and enable them"이라는 초록 버튼이 나오면 클릭합니다.
3. 좌측 메뉴에서 **`QA Tech Trend Bot (점심시간 배송)`**을 클릭합니다.
4. 우측에 생긴 **`Run workflow`** 버튼을 누르고, 초록색 **`Run workflow`**를 한 번 더 누릅니다.
5. 잠시 기다리면 파이프라인이 돌아가며 디스코드 채널로 예쁜 기술 리포트가 도착합니다! 🎉

*(한 번 테스트가 성공했다면, 앞으로는 매일 낮 12시에 봇이 알아서 기상하여 메시지를 보냅니다.)*