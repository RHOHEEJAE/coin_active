# 코인 최대 보유자 변동 알럿

도지(DOGE), 페페(PEPE), 비트(BTC), 리플(XRP)의 **보유량 기준 상위 5명**을 조회하고,  
**1위(최대 보유자)**의 보유량이 변동되면 알럿을 보냅니다.

- 보유량 **증가** → **매수** 알럿  
- 보유량 **감소** → **매도** 알럿  

지갑 주소는 PK로 사용하며, `state.json`에 1위 지갑과 보유량을 저장해 이전 값과 비교합니다.

## 설치

```bash
cd coin_active
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## 설정

`.env.example`을 복사해 `.env`를 만들고 필요 시 수정합니다.

```bash
copy .env.example .env
```

- **BLOCKCHAIR_API_KEY**: DOGE, BTC, XRP 조회에 **권장**. 키 없으면 해당 API에서 430 등 제한이 걸릴 수 있음. [발급](https://blockchair.com/api)
- **BLOCKSCOUT_API_KEY**: (선택) Blockscout API 키. ERC-20(페페) 조회 시 사용.
- **TELEGRAM_BOT_TOKEN**, **TELEGRAM_CHAT_ID**: (선택) 텔레그램 알림 사용 시 설정.

## 실행

```bash
python main.py
```

- 최초 1회 즉시 체크 후, 기본 **5분(300초)**마다 DOGE, PEPE, BTC, XRP 순으로 조회합니다.
- 체크 주기는 `config.py`의 `CHECK_INTERVAL_SECONDS`에서 변경할 수 있습니다.

## 데이터 소스

| 코인 | 데이터 소스 | 비고 |
|------|-------------|------|
| DOGE | Blockchair `dogecoin/addresses` | 상위 주소 목록 |
| BTC  | Blockchair `bitcoin/addresses`  | 상위 주소 목록 |
| PEPE | Blockscout `getTokenHolders` (ERC-20) | 컨트랙트 기준 상위 보유자 |
| XRP  | Blockchair `ripple/addresses`   | API 키 필요. 리플 주소 목록 미지원 시 빈 결과 가능 |

## 프로젝트 구조

- `config.py` - 코인별 설정, API 키, 체크 주기
- `fetchers/` - Blockchair(DOGE, BTC, XRP), Blockscout(PEPE) 보유자 조회
- `storage.py` - 1위 지갑·보유량 저장(`state.json`) 및 변동 감지
- `alert.py` - 콘솔/텔레그램 알럿
- `main.py` - 주기 실행 진입점

## Supabase + Vercel 차트 대시보드

- **수집 스크립트**: 로컬에서 `python main.py` 로만 실행.
- **DB**: Supabase 사용 시 `.env`에 `SUPABASE_DATABASE_URL` 설정.  
  (Supabase Dashboard > Project Settings > Database > Connection string (URI) 에서 복사 후 `[YOUR-PASSWORD]` 치환.)
- **테이블 생성**: Supabase SQL Editor에서 `supabase_schema.sql` 한 번 실행.
- **차트 페이지**: `dashboard/` 가 Next.js 앱. Supabase에서 데이터 읽어 테이블·시간별 매수/매도 차트 표시.  
  로컬 실행: `cd dashboard && npm i && npm run dev`  
  배포: Vercel에서 Root Directory = `dashboard`, 환경 변수 `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 설정 후 배포.  
  자세한 설정은 `dashboard/README.md` 참고.

## 알럿만 테스트

1위 보유자 변동을 시뮬레이션하려면 `state.json`을 수정한 뒤 다음 체크가 돌 때 알럿이 나갑니다.
