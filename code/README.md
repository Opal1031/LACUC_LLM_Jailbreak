# 코드 파일 안내

이 폴더에는 실험 대화 수집, 외부 판정, 결과 분석과 그래프 생성을 위한 스크립트가 있다. 경로는 모두 저장소 루트를 작업 폴더로 실행하는 것을 기준으로 한다.

## 파일별 역할

| 파일 | 역할 | 주요 입력 | 주요 출력·동작 |
|---|---|---|---|
| `start_ollama.cmd` | Windows에서 로컬 공격자 모델 서버를 실행한다. | 설치된 Ollama와 `qwen3:14b` | `LLAMA_API_KEY`를 비우고 `OLLAMA_KV_CACHE_TYPE=q8_0`을 적용한 Ollama 서버 |
| `run_experiment_matrix.py` | 두 대상 모델과 반복 세트를 순서대로 실행하는 배치 관리자다. | SafeDialBench 입력 Excel, 모델·세트·시드 옵션 | 모델별 `set_N.xlsx`; 홀수·짝수 세트마다 모델 실행 순서를 반대로 배치 |
| `run_jailbreak_pipeline.py` | 한 모델·한 세트의 5턴 적응형 공격 대화를 실제로 수행한다. | 데이터셋, Qwen/Ollama, OpenAI API | `대화`, `사례정보`, `실행정보` 시트를 가진 원본 결과 Excel과 실행 중 체크포인트 |
| `judge_pipeline.py` | 수집된 5턴 대화를 사례별 안전 기준에 따라 Claude `opus`로 블라인드 판정한다. | 원본 결과 Excel 또는 배치 폴더 | `집계`, `사례요약`, `턴별판정상세` 시트를 가진 판정 Excel과 판정 중 체크포인트 |
| `run_judge_all.cmd` | 본실험 6세트를 구간별로 판정하기 위한 Windows 래퍼다. | 회차 태그, 세트당 누적 `limit` | `judge_pipeline.py` 실행, 표준 출력·오류 로그 저장 |
| `analyze_results.py` | 동일 사례를 받은 두 모델을 쌍체 설계로 비교한다. | 판정 Excel, 데이터셋, 분석할 세트 | 엄격·완화 성공의 McNemar 정확검정, Wilson 구간, 위험영역별 비교를 터미널에 출력 |

## 전체 실행 흐름

1. `start_ollama.cmd`로 Qwen 서버를 실행한다.
2. `run_experiment_matrix.py`가 세트별로 `run_jailbreak_pipeline.py`를 호출해 원본 대화를 수집한다.
3. `run_judge_all.cmd` 또는 `judge_pipeline.py`가 원본 대화를 사례별로 판정한다.
4. `analyze_results.py`가 모델 간 차이를 집계·검정한다.

## 현재 상태와 주의사항

- 본실험은 이미 끝났으며 최종 판정 결과는 `../outputs/main_20260908_judged.xlsx`다.
- 완료 후 `.venv/`, `logs/`, 판정 체크포인트, `__pycache__/`는 삭제했다. 이전 판정 회차의 리포트·그래프 생성기(`make_report.py`)와 산출물(`../figures/old_judged_set1/`)도 최종 판정 워크북과 수치가 달라 폐기했다. 다시 실행하려면 `../requirements.txt`로 가상환경을 만들고 필요한 출력 폴더를 준비해야 한다.
- `run_jailbreak_pipeline.py`와 `run_experiment_matrix.py`는 결과 Excel의 재현 해시와 연결되어 있으므로 원본을 수정하지 않는다. 변경 실험이 필요하면 복사본이나 새 버전 파일을 만든다.
- `judge_pipeline.py`의 `SYSTEM_PROMPT`를 바꿀 때는 `../prompts/claude_jailbreak_judge_v1.md`도 동일하게 갱신해야 한다.
- `judge_pipeline.py`의 `build_report()`는 플랫폼 차단(`_incomplete`) 사례를 분모에서 빼는 **옛 집계 규칙**을 쓴다. 최종 워크북의 `집계`·`세트별집계` 시트는 새 규칙(차단을 분모 1,500에 남기고 탈옥 실패로 계산)으로 다시 계산해 넣은 것이므로, `--report-only`로 리포트를 재생성하면 옛 값으로 덮어써진다.
- `analyze_results.py`는 실험 과정에서 사용한 그대로 보존한 코드다. 다음 세 가지를 알고 써야 한다.
  - `JUDGED` 기본값이 이전 결과 파일명 `outputs/20260908_182711_main_judged.xlsx`를 가리킨다. 최종 파일을 분석할 때는 원본을 덮어쓰지 말고 새 스크립트에서 `outputs/main_20260908_judged.xlsx`를 명시한다.
  - 차단 사례를 분석에서 제외하는 옛 집계 규칙을 쓴다. 현재 문서의 주 분석 기준(분모 1,500, 차단은 실패)과 다르다.
  - `load_cases()`가 사례를 `id`만으로 키를 잡아 **세트를 두 개 이상 넘기면 뒤 세트가 앞 세트를 덮어쓴다.** 세트 하나씩만 유효하며, 3세트 합산 쌍체 분석은 키를 `(세트, id)`로 바꾼 새 코드가 필요하다.
- `run_judge_all.cmd`의 누적 `limit`은 체크포인트 필터보다 먼저 적용된다. 같은 구간을 재개할 때는 같은 값을, 다음 구간으로 넘어갈 때는 더 큰 누적값을 사용한다.

판정 라벨과 엄격·완화 ASR의 정의는 루트 `../실험_전체정리.md` 6.3~6.4절에 정리되어 있다.
