# 11주차 실습 — `load_scores` 단위 테스트

10주차에 만든 `load_scores(path)`를 pytest로 시험하는 실습입니다.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `load_scores.py` | 시험 대상 함수. 성적 CSV를 읽어 `(kept, skipped)`를 돌려줍니다. |
| `test_load_scores.py` | pytest 단위 테스트 (42개) |
| `scores.csv` | 기본 실습 데이터 |
| `weird.csv` | 이상한 줄만 모은 데이터 |
| `empty.csv` | 헤더만 있는 데이터 |
| `bug3_logic.py` | 함정 실험용 고장난 코드 (`find_max`, `count_pass`) |
| `prompts.txt` | AI 비교 실험용 프롬프트 원문 |

## 함수 명세

```
load_scores(path) -> (kept, skipped)
  kept    : [(이름, 점수), ...]                 점수는 0~100 정수
  skipped : [(줄번호, 원본줄, 이유), ...]
```

1. 파일이 없으면 `FileNotFoundError`를 그대로 올린다
2. 헤더만 있으면 `([], [])`
3. 열 개수가 2가 아니면 건너뛰고 기록
4. 점수가 비었거나 정수가 아니면 건너뛰고 기록
5. 점수가 0~100 밖이면 건너뛰고 기록
6. 이름이 비었으면 건너뛰고 기록

- 같은 이름이 두 번 나오면 둘 다 남긴다 (동명이인일 수 있음)
- 빈 줄은 기록 없이 건너뛴다

## 실행 방법

> 이 PC에서는 `pip.exe`·`pytest.exe`가 막혀 있고 `python`도 Store 별칭에 걸려 있으므로
> `py -m ...` 형태로 실행합니다.

```bash
py -m pip install pytest pytest-cov
py -m pytest -v
py -m pytest --cov=load_scores --cov-report=term-missing
py load_scores.py scores.csv
```

## 테스트 구성

| 구분 | 확인하는 것 |
|---|---|
| 정상 | 올바른 줄이 `(이름, int 점수)`로 남음, 앞뒤 공백 제거, `str` 경로 |
| 예외 ①~⑥ | 명세 각 항목과 기록되는 이유 문자열 |
| 경계값 | 0·1·99·100은 남고 -1·101은 건너뜀 |
| 특수 규칙 | 동명이인, 빈 줄, 줄번호, 따옴표 안 쉼표, BOM, CRLF |
| 실습 파일 | `scores.csv`·`weird.csv`·`empty.csv`의 전체 결과 |
| 명령줄 | `python load_scores.py [경로]` 출력 |

## 결과

```
42 passed

Name             Stmts   Miss  Cover   Missing
----------------------------------------------
load_scores.py      45      0   100%
```
