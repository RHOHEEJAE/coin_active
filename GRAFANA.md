# Grafana 연동 가이드

PostgreSQL에 저장된 `top_holders`, `holder_alerts`를 Grafana에서 조회하는 방법입니다.

## 1. Data Source 추가

- **Type**: PostgreSQL
- **Host**: `localhost:5432` (또는 Docker 호스트)
- **Database**: `mydb`
- **User**: `admin` / **Password**: `admin`
- **SSL Mode**: disable (로컬 기준)

## 2. 테이블 구조 요약

| 테이블 | 설명 |
|--------|------|
| **top_holders** | 상위 100명 보유자 스냅샷. `(symbol, rank)` PK, 매 체크마다 upsert |
| **holder_last_balance** | 지갑별 직전 보유량 (변동 감지용) |
| **holder_alerts** | 상위 100명 전원 매수/매도 알럿 이력. `rank` = 해당 시점 순위 |

## 3. 추천 패널

### 3-1. PEPE 상위 100명 (테이블)

- **Visualization**: Table
- **Query** (PostgreSQL) — 지갑 컬럼을 Etherscan 주소 링크로 반환:

```sql
SELECT
  rank AS "순위",
  balance_human AS "보유량(PEPE)",
  updated_at::date AS "갱신일시",
  'https://etherscan.io/address/' || wallet_address AS "지갑 링크"
FROM top_holders
WHERE symbol = 'PEPE'
ORDER BY rank;
```

- **지갑 링크를 클릭 가능한 하이퍼링크로 만들기**  
  - Overrides → **Add override** → **Fields with name** → **"지갑 링크"** 선택  
  - **Data links** → **Add link**  
    - **Title**: `Etherscan` (또는 `보기`)  
    - **URL**: `${__value.raw}`  
  - 셀 값이 전체 URL이므로 `${__value.raw}`가 그대로 링크 주소가 됩니다. 저장 후 해당 컬럼 클릭 시 Etherscan이 열립니다.

- rank를 PK로 매 회차 업데이트되므로, 항상 “현재” 상위 100명이 나옵니다.

---

### 3-2. 매수/매도 알럿 이력 (테이블) — 추천

- **Visualization**: Table
- **아래 쿼리 그대로 Grafana 패널 SQL에 붙여넣기**  
  - **순위(rank) 기준 중복 제거**: 각 순위별 **가장 최근 알럿 1건**만 표시  
  - **변동 수량**: (변동 후 − 변동 전)을 10^18로 나눠 **천 단위 콤마 + 소수 2자리**로 표시 (매수 +, 매도 −)

```sql
WITH latest_per_rank AS (
  SELECT DISTINCT ON (rank)
    rank,
    created_at,
    symbol,
    alert_type,
    balance_before,
    balance_after
  FROM holder_alerts
  ORDER BY rank, created_at DESC
)
SELECT
  rank AS "순위",
  created_at AS "발생시각",
  symbol AS "코인",
  alert_type AS "구분",
  to_char(
    (COALESCE(balance_after::numeric, 0) - COALESCE(balance_before::numeric, 0)) / 1e18,
    'FM999,999,999,999,990.00'
  ) AS "변동 수량",
  CASE WHEN alert_type = 'buy' THEN 1 ELSE 0 END AS "행색"
FROM latest_per_rank
ORDER BY created_at DESC
LIMIT 200;
```

- **구분**이 `buy` / `sell` 이므로, 컬럼으로 바로 매수·매도 구분 가능.

**매수=초록, 매도=빨강이 적용 안 될 때 (Value mappings만으로는 색이 안 들어가는 경우)**

Grafana Table에서는 **문자(buy/sell)에는 Thresholds 색이 안 들어가고**, Value mappings는 **표시 텍스트**만 바꿉니다. 그래서 **숫자 컬럼 하나**를 두고, 그 컬럼에 Thresholds로 색을 준 뒤 **행 전체**에 칠하는 방식으로 하면 됩니다.

1. **쿼리에 위처럼 `행색` 컬럼 추가**  
   - `CASE WHEN alert_type = 'buy' THEN 1 ELSE 0 END AS "행색"`  
   - 매수=1, 매도=0.

2. **Overrides** → **Add override** → **Fields with name** → **"행색"** 선택.

3. **"행색" 오버라이드에서**:
   - **Cell options** → **Cell type** = **Colored background**.
   - **Apply to entire row** = **켬** (행 전체가 같은 색).
   - **Thresholds**:
     - **Base** = 0 → 색상 **Red** (매도).
     - **Add threshold** = 1 → 색상 **Green** (매수).

4. **"행색" 컬럼 숨기기** (선택):
   - 같은 **행색** 오버라이드에 **Column width** = `0`  
     또는 Table 설정에서 **Column width**를 최소로 두면, 맨 끝에 얇은 색 막대만 보이거나 아예 안 보이게 할 수 있습니다.
   - 또는 **Transform** → "Filter by name"에서 "행색" 제외해도 됩니다 (단, 오버라이드는 필드 이름으로 걸었으므로 필드를 제거하면 오버라이드가 동작 안 할 수 있음).  
   → **Column width = 0** 으로 두고 "Apply to entire row"만 켜 두는 게 가장 무난합니다.

5. **(선택) "구분" 컬럼 Value mappings**  
   - **Fields with name** = **"구분"** → Value mappings: `buy` → "매수", `sell` → "매도"  
   → 글자만 한글로 바꾸는 용도.

정리하면, **색은 "행색" 숫자 컬럼 + Thresholds + Apply to entire row** 로 넣고, **구분**은 Value mappings로 "매수"/"매도" 표시만 하면 됩니다.

---

### 3-3. 최근 알럿 요약 (Stat)

- **Visualization**: Stat
- **Query** (최근 1건):

```sql
SELECT
  alert_type AS "최근 알럿",
  created_at AS "시각",
  wallet_address AS "지갑"
FROM holder_alerts
ORDER BY created_at DESC
LIMIT 1;
```

- 또는 **매수/매도 각각 Stat 패널**로 나누려면:
  - 매수: `SELECT COUNT(*) FROM holder_alerts WHERE alert_type = 'buy' AND created_at > NOW() - INTERVAL '7 days';`
  - 매도: `SELECT COUNT(*) FROM holder_alerts WHERE alert_type = 'sell' AND created_at > NOW() - INTERVAL '7 days';`

---

### 3-4. 알럿 시계열 (시간별 건수)

- **Visualization**: Time series (Bar chart 또는 Line)
- **Query** — 시간 1컬럼 + 매수/매도 건수 각 1컬럼이면 타임시리즈가 바로 뜹니다:

```sql
SELECT
  date_trunc('hour', created_at) AS time,
  COUNT(*) FILTER (WHERE alert_type = 'buy') AS "매수",
  COUNT(*) FILTER (WHERE alert_type = 'sell') AS "매도"
FROM holder_alerts
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', created_at)
ORDER BY time;
```

- **패널 설정**: 쿼리에서 **Format as** = **Time series**, “Series as rows” 또는 “(생략)”로 **Time column** = `time` 이면 x축 시간, y축에 "매수"/"매도" 두 시리즈가 나옵니다.

---

### 3-5. 알럿 타임라인 (Annotation)

- **Dashboard → Settings → Annotations** 에서 New annotation 추가:
  - **Query**:

```sql
SELECT
  created_at AS time,
  alert_type || ' - ' || LEFT(wallet_address, 10) || '...' AS text
FROM holder_alerts
WHERE $__timeFilter(created_at);
```

- 다른 시계열 패널이 있으면, 해당 시각에 매수/매도가 점(또는 선)으로 표시됩니다.

## 4. 매수/매도 구분 표시 팁

- **Table**  
  - `alert_type` 컬럼에 **Cell display mode → Color background** 또는 **Color text** 적용  
  - Value mapping: `buy` → 초록, `sell` → 빨강
- **Stat**  
  - Value mapping으로 `buy` → "매수", `sell` → "매도" 로 한글 표기
- **Time series**  
  - metric으로 `alert_type`을 쓰면 시리즈별로 색이 나뉘어 매수/매도 추이를 한눈에 볼 수 있습니다.

## 5. 대시보드에 이미지 넣기

1. **패널 추가**  
   대시보드에서 **Add** → **Visualization** (또는 **Add panel**) 선택.

2. **이미지 패널 선택**  
   - **Visualization** 목록에서 **Image** 를 고릅니다.  
   - (버전에 없으면) **Text** 를 선택한 뒤 아래 3번처럼 URL/마크다운으로 넣습니다.

3. **이미지 지정**  
   - **Image** 패널: **URL** 에 이미지 주소 입력 (예: `https://example.com/logo.png`).  
     로컬 파일은 Grafana가 접근할 수 있는 **공개 URL** 이나 **External image storage** 로 올린 뒤 그 URL을 넣어야 합니다.  
   - **Text** 패널: **Content** 에 마크다운  
     `![설명](https://이미지URL)`  
     또는 HTML  
     `<img src="https://이미지URL" width="200" />`  
     로 넣으면 됩니다.

4. **저장**  
   패널 제목·크기 조정 후 **Apply** / **Save dashboard**.

- **로고/배너** 같은 건 대시 상단에 넓은 Text 패널 하나 두고, 그 안에 이미지 URL 넣어 쓰면 됩니다.

---

## 6. 요약

- **rank를 PK로** 쓴 `top_holders`는 “현재 상위 10명”을 계속 갱신하므로, 위 테이블 쿼리만으로 항상 최신이 나옵니다.
- **매수/매도 알럿**은 `holder_alerts`에만 쌓이므로, “알럿 이력 테이블 + (선택) 시계열/Stat/Annotation” 조합으로 Grafana에 나타내는 구성을 추천합니다.
