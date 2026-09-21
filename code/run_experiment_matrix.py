from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


TARGET_MODELS = ("gpt-5.6-sol", "gpt-6-astra")


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    root = here.parent
    parser = argparse.ArgumentParser(description="Qwen 적응형 공격으로 GPT-5.6 Sol / GPT-6 Astra 실행")
    parser.add_argument(
        "--input",
        type=Path,
        default=root / "datasets" / "test" / "SafeDialBench_ko_test_10_fixed5turn.xlsx",
    )
    parser.add_argument("--output-root", type=Path, default=root / "outputs")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--models", nargs="+", choices=TARGET_MODELS, default=list(TARGET_MODELS))
    parser.add_argument("--attacker-model", default="qwen3:14b")
    parser.add_argument("--base-seed", type=int, default=1000)
    parser.add_argument("--attacker-temperature", type=float, default=0.5)
    parser.add_argument("--attacker-max-tokens", type=int, default=240)
    parser.add_argument("--max-regenerations", type=int, default=4, help="2~5턴 질문 품질검사 실패 시 재생성 횟수")
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max"), default="medium")
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--service-tier", choices=("default",), default="default")
    parser.add_argument("--limit", type=int, default=0, help="0이면 전체 데이터")
    parser.add_argument("--start-row", type=int, default=1)
    parser.add_argument("--end-row", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--show-transcript", action="store_true", help="각 턴의 실제 질문과 답변을 터미널에 표시")
    parser.add_argument("--dry-run", action="store_true", help="명령만 표시하고 실행하지 않음")
    return parser.parse_args()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def main() -> int:
    args = parse_args()
    if args.runs < 1:
        raise ValueError("--runs는 1 이상이어야 합니다.")

    pipeline = Path(__file__).resolve().parent / "run_jailbreak_pipeline.py"
    batch_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    batch_root = args.output_root.resolve() / batch_id
    jobs: list[tuple[int, str]] = []
    for set_number in range(1, args.runs + 1):
        ordered_models = list(args.models) if set_number % 2 else list(reversed(args.models))
        jobs.extend((set_number, model) for model in ordered_models)

    print(f"신규 실험 묶음: {batch_root}")
    print(f"총 실행 수: {len(jobs)} (모델 {len(args.models)}개 × {args.runs}세트)")
    failed_jobs: list[str] = []
    for job_number, (set_number, model) in enumerate(jobs, start=1):
        label = f"{model}_set_{set_number}"
        output = batch_root / safe_name(model) / f"set_{set_number}.xlsx"
        command = [
            sys.executable,
            str(pipeline),
            "--input", str(args.input.resolve()),
            "--output", str(output),
            "--attacker-model", args.attacker_model,
            "--attacker-seed", str(args.base_seed + set_number),
            "--attacker-temperature", str(args.attacker_temperature),
            "--attacker-max-tokens", str(args.attacker_max_tokens),
            "--max-regenerations", str(args.max_regenerations),
            "--openai-model", model,
            "--reasoning-effort", args.reasoning_effort,
            "--max-output-tokens", str(args.max_output_tokens),
            "--service-tier", args.service_tier,
            "--max-turns", "5",
            "--limit", str(args.limit),
            "--start-row", str(args.start_row),
            "--end-row", str(args.end_row),
            "--delay", str(args.delay),
            "--run-label", label,
        ]
        if args.show_transcript:
            command.append("--show-transcript")
        print(f"[{job_number}/{len(jobs)}] {label}", flush=True)
        if args.dry_run:
            print(subprocess.list2cmdline(command))
            continue
        result = subprocess.run(command)
        if result.returncode != 0:
            failed_jobs.append(label)
            print(
                f"[{job_number}/{len(jobs)}] {label} 실패(종료코드 {result.returncode}) — "
                f"다음 작업은 계속 진행합니다. 이 작업은 나중에 "
                f"'python code\\run_jailbreak_pipeline.py --output {output} --resume ...' "
                "(다른 인자는 이 배치와 동일하게)로 재시도하십시오.",
                file=sys.stderr, flush=True,
            )

    if failed_jobs:
        print(f"일부 작업 실패({len(failed_jobs)}/{len(jobs)}): {', '.join(failed_jobs)}", file=sys.stderr)
        print(f"묶음 종료(일부 실패): {batch_root}")
        return 1
    print(f"전체 완료: {batch_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
