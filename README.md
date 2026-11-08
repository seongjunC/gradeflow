# GradeFlow · Streamlit

Python 3.12를 권장합니다. Python 3.15 대신 3.12 가상환경을 사용하세요. 프로젝트 폴더에서 아래 명령을 실행하세요.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

접속: http://127.0.0.1:8501 · 종료: 서버 터미널에서 Ctrl+C

가상환경 활성화나 PowerShell 실행 정책 변경은 필요 없습니다. 가상환경이 이미 있다면 첫 줄은 생략합니다. 다른 컴퓨터에는 Python을 설치하고 가상환경을 새로 만들어야 합니다.

## API 키

서버 환경 변수, 프로젝트 `.env.local` 또는 `.streamlit/secrets.toml`의 `OPENAI_API_KEY`를 읽습니다. 이 폴더에는 API 키 파일을 포함하지 않았습니다. 웹페이지에는 키 입력창이 없습니다. 환경 변수가 파일보다 우선합니다. 기존에 만든 키는 7일 만료 설정이므로 만료 후 서버 키를 교체해야 합니다.

Streamlit Community Cloud 배포 시 저장소와 `streamlit_app.py`를 선택하고, 관리 화면의 Secrets에 `OPENAI_API_KEY`를 설정하세요. `.env.local`, `.streamlit/secrets.toml`, `.venv`는 저장소에 올리지 않습니다. Community Cloud의 실행 환경은 로컬 가상환경과 별개이며 `requirements.txt`로 설치합니다. 로컬 주소 설정을 덮어써야 하는 서버에서는 `--server.address 0.0.0.0 --server.port 8501`을 실행 명령에 추가하세요.

## 자료 형식

- 정답표: 텍스트를 포함한 PDF. 각 행은 `문항번호 정답 배점`, 예: `1 3 5`. 1번부터 연속, 정답 1~5, 양수 배점입니다.
- OMR: `.xlsx` 첫 시트 또는 UTF-8/CP949 CSV. 첫 열은 학생명, 나머지는 `Q01,Q02,…`. 빈칸은 미응답입니다. 기존 `.xls`는 `.xlsx`로 저장하세요.

분석 후 **AI 맥락 준비 / 다시 시도**를 누르면 채팅할 수 있습니다. 모델은 `gpt-6-luna`로 고정하고 Responses API에 `store:false`를 전달합니다. API 사용에는 해당 모델 권한과 사용 한도가 필요합니다.

자료·성적·대화는 사용자별 Streamlit 세션 메모리에만 유지하며 파일이나 DB에 저장하지 않습니다. 입력이 바뀌면 결과와 대화를 초기화합니다. 채팅에는 계산된 평가 결과와 문제지 텍스트가 OpenAI로 전송됩니다. Streamlit 버전에서는 업로드한 파일이 Python 서버 메모리로 전송됩니다.

앱의 실행 진입점은 `streamlit_app.py`입니다. 이 폴더에는 Streamlit 실행에 필요한 파일만 포함되어 있으며 가상환경은 직접 설치합니다.


## 화면과 정답표 추출



## 페이지 구성

서비스 소개 메인페이지의 평가 분석 시작하기 버튼으로 분석 화면에 진입합니다. 헤더 오른쪽 평가 분석 버튼으로 분석 화면에 들어가고 왼쪽 GradeFlow 로고로 소개 화면에 돌아갈 수 있으며 이동 중 업로드 자료와 분석 결과는 유지됩니다.

문제지 PDF, 정답·배점표 PDF, 학생 OMR Excel·CSV만 업로드합니다. 학생 응답 및 정답표 직접 입력 기능은 없습니다. 스캔 이미지 PDF의 OCR은 지원하지 않습니다. ui.css는 앱과 같은 폴더에 두세요.


## 문제지 PDF 뷰어

문제지 PDF 탭은 업로드한 원본 PDF를 고정 높이 뷰어로 표시합니다. 기존 환경은 python -m pip install -r requirements.txt 실행 후 서버를 다시 시작하세요. 원본 PDF는 현재 세션 메모리에만 유지됩니다.

