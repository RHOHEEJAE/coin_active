# PEPE 보유자 · 매수/매도 차트 대시보드 (Vercel 배포용)

Supabase에 쌓인 `top_holders`, `holder_alerts`를 읽어서 테이블·차트로 보여주는 Next.js 앱입니다.

## 설정

1. **Supabase 테이블**  
   `coin_active/supabase_schema.sql` 을 Supabase Dashboard > SQL Editor에서 한 번 실행해 두세요.

2. **환경 변수**  
   - 로컬: `dashboard/.env.local` 생성 후 아래 값 입력  
   - Vercel: Project Settings > Environment Variables 에 동일하게 추가  

   ```
   NEXT_PUBLIC_SUPABASE_URL=https://hbbpukwapwykstgtdzty.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```

3. **실행**

   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

   브라우저에서 http://localhost:3000 확인.

## Vercel 배포

1. GitHub에 `coin_active` 저장소 푸시 후 Vercel에서 해당 repo 연결.
2. **Root Directory** 를 `dashboard` 로 지정.
3. **Environment Variables** 에 `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 설정.
4. Deploy.

수집 스크립트는 로컬에서만 돌리고, DB는 Supabase를 쓰면 이 대시보드에서 동일 데이터를 볼 수 있습니다.
