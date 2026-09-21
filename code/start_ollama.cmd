@echo off
rem === 반드시 이 스크립트로 Ollama를 띄울 것 ===
rem
rem 1) LLAMA_API_KEY: 설정돼 있으면 Ollama 0.33+ 런너가 인증을 켜서 자기 자신에게 401을 반환한다.
rem    그래서 이 변수를 비운 환경에서 서버를 띄운다.
rem
rem 2) OLLAMA_KV_CACHE_TYPE=q8_0: qwen3:14b(가중치 8,850MiB)가 10GB 카드에 약 150MiB 차이로
rem    안 들어가 층 일부가 CPU로 밀린다. KV 캐시를 8비트로 줄이면 CPU 비중이 18%->16%로 줄고
rem    생성 속도가 13.6 -> 16.6 tok/s로 약 22% 빨라진다. (2026-09-10 실측)
rem
rem 3) 재시작 전 반드시 런너를 먼저 정리할 것:
rem       taskkill /F /IM ollama.exe
rem       taskkill /F /IM llama-server.exe
rem    ollama.exe만 죽이면 자식 llama-server.exe가 살아남아 VRAM을 계속 점유한다.
rem    이게 쌓이면 새 서버가 가용 VRAM을 못 봐 모델을 거의 전부 CPU로 올리고 3 tok/s까지 떨어진다.
setlocal
set "LLAMA_API_KEY="
set "OLLAMA_HOST=127.0.0.1:11434"
set "OLLAMA_KV_CACHE_TYPE=q8_0"
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
