@echo off
rem 본실험 6세트를 한 번에 판정한다. (2026-09-12 재판정용)
rem
rem 사용법: run_judge_all.cmd <회차> [세트당누적limit]
rem   예) run_judge_all.cmd c1 50    -> 6세트 각각 1~50번   (총 300건)
rem       run_judge_all.cmd c2 100   -> 6세트 각각 51~100번 (총 300건)
rem       run_judge_all.cmd c10 500  -> 6세트 각각 451~500번
rem       run_judge_all.cmd full     -> 제한 없이 남은 전체
rem
rem --input에 배치 폴더를 주면 judge_pipeline.py가 6개 xlsx를 모두 잡는다:
rem       for model_dir in sorted(...): for xlsx in model_dir.glob("set_*.xlsx")
rem   따라서 --limit은 "파일당" 적용된다. limit 50이면 6세트에서 50건씩 균등하게
rem   나가므로, 어느 한 세트만 먼저 끝나는 일이 없다.
rem
rem [누적limit] 주의 -- judge_pipeline.py는 --limit을 체크포인트 필터보다 먼저 적용한다:
rem       ids = ids[:limit]                # 먼저 앞에서 N개를 자르고
rem       if key in checkpoint: continue   # 그 다음 완료분을 건너뛴다
rem   같은 숫자로 다시 돌리면 "채점할 새 사례 없음"만 뜬다. 구간을 넘기려면
rem   숫자를 계속 키워야 한다(50 -> 100 -> 150 ...). 한도로 중간에 끊겼을 때는
rem   같은 숫자로 다시 돌리면 그 구간의 남은 것만 이어서 한다.
rem
rem 판정 모델은 opus 고정. 한 체크포인트 안에서는 절대 바꾸지 않는다(문서 6.6).
rem PYTHONIOENCODING이 없으면 리다이렉션된 stdout이 cp1252로 잡혀 한글 로그에서 죽는다.
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0.."

set "BATCH=outputs\main_20260908"
set "JUDGED=outputs\main_20260908_judged"
set "WORKERS=3"

set "RUNTAG=%~1"
set "LIMIT=%~2"
if "%RUNTAG%"=="" set "RUNTAG=c1"

set "LIMITARG="
if not "%LIMIT%"=="" set "LIMITARG=--limit %LIMIT%"

echo [run_judge_all] tag=%RUNTAG%  limit=%LIMIT%  workers=%WORKERS%
echo [run_judge_all] input=%BATCH%  output=%JUDGED%.xlsx

.venv\Scripts\python.exe code\judge_pipeline.py --input "%BATCH%" --output "%JUDGED%.xlsx" --checkpoint "%JUDGED%.checkpoint.json" --judge-model opus --workers %WORKERS% %LIMITARG% > "logs\judge_all_%RUNTAG%.out.log" 2> "logs\judge_all_%RUNTAG%.err.log"

echo [run_judge_all] exit code %ERRORLEVEL%
echo [run_judge_all] logs: logs\judge_all_%RUNTAG%.out.log  /  .err.log
endlocal
