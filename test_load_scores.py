# test_load_scores.py
# ---------------------------------------------------------------------------
# load_scores(path) -> (kept, skipped) 의 단위 테스트
#
# 실행:  py -m pytest -v
# 커버리지: py -m pytest --cov=load_scores --cov-report=term-missing
#
# 구성
#   1. 정상     : 올바른 줄은 (이름, 점수) 로 남는다
#   2. 예외     : 명세 ①~⑥ 각각을 하나씩 확인
#   3. 경계값   : 0 · 100 은 남고 -1 · 101 은 건너뛴다
#   4. 특수 규칙 : 동명이인 · 빈 줄 · 줄번호 · BOM · 따옴표 안 쉼표
#   5. 실습 파일 : scores.csv · weird.csv · empty.csv 전체 결과
#   6. 명령줄 실행 (__main__)
# ---------------------------------------------------------------------------

import runpy
import sys
from pathlib import Path

import pytest

from load_scores import load_scores

HERE = Path(__file__).parent


def make_csv(tmp_path, text, encoding="utf-8"):
    """tmp_path 안에 CSV 파일을 만들고 경로를 돌려준다."""
    p = tmp_path / "tmp.csv"
    p.write_text(text, encoding=encoding, newline="")
    return p


# ---------------------------------------------------------------------------
# 1. 정상
# ---------------------------------------------------------------------------

def test_정상_줄은_이름과_정수점수로_남는다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n이두리,70\n")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", 88), ("이두리", 70)]
    assert skipped == []


def test_점수는_int_타입이다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n")
    kept, _ = load_scores(p)
    assert type(kept[0][1]) is int


def test_이름과_점수의_앞뒤_공백은_제거된다(tmp_path):
    p = make_csv(tmp_path, "name,score\n  김하나  ,  88  \n")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", 88)]
    assert skipped == []


def test_str_경로도_받는다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n")
    kept, _ = load_scores(str(p))
    assert kept == [("김하나", 88)]


# ---------------------------------------------------------------------------
# 2. 예외 — 명세 ①~⑥
# ---------------------------------------------------------------------------

def test_명세1_파일이_없으면_FileNotFoundError(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_scores(tmp_path / "없는파일.csv")


def test_명세2_헤더만_있으면_빈_결과(tmp_path):
    p = make_csv(tmp_path, "name,score\n")
    assert load_scores(p) == ([], [])


def test_명세2_완전히_빈_파일도_빈_결과(tmp_path):
    p = make_csv(tmp_path, "")
    assert load_scores(p) == ([], [])


@pytest.mark.parametrize("line", [
    "김하나",              # 1열
    "김하나,88,비고",      # 3열
    "김하나,88,,",         # 4열 (빈 칸 포함)
])
def test_명세3_열_개수가_2가_아니면_건너뛴다(tmp_path, line):
    p = make_csv(tmp_path, f"name,score\n{line}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, line, "열 개수가 2가 아님")]


@pytest.mark.parametrize("raw", ["", "   "])
def test_명세4_점수가_비면_건너뛴다(tmp_path, raw):
    p = make_csv(tmp_path, f"name,score\n김하나,{raw}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, f"김하나,{raw}", "점수가 비어 있음")]


@pytest.mark.parametrize("raw", ["결석", "88.5", "7 2", "abc", "1e2"])
def test_명세4_점수가_정수가_아니면_건너뛴다(tmp_path, raw):
    p = make_csv(tmp_path, f"name,score\n김하나,{raw}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, f"김하나,{raw}", "점수가 정수가 아님")]


@pytest.mark.parametrize("raw", ["-5", "105", "1000", "-100"])
def test_명세5_점수가_범위_밖이면_건너뛴다(tmp_path, raw):
    p = make_csv(tmp_path, f"name,score\n김하나,{raw}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, f"김하나,{raw}", "점수가 0~100 밖")]


@pytest.mark.parametrize("name", ["", "   "])
def test_명세6_이름이_비면_건너뛴다(tmp_path, name):
    p = make_csv(tmp_path, f"name,score\n{name},90\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, f"{name},90", "이름이 비어 있음")]


def test_이름과_점수가_모두_비면_이름_검사가_먼저다(tmp_path):
    p = make_csv(tmp_path, "name,score\n,\n")
    _, skipped = load_scores(p)
    assert skipped == [(2, ",", "이름이 비어 있음")]


# ---------------------------------------------------------------------------
# 3. 경계값
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score", [0, 1, 99, 100])
def test_경계값_안쪽은_남는다(tmp_path, score):
    p = make_csv(tmp_path, f"name,score\n김하나,{score}\n")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", score)]
    assert skipped == []


@pytest.mark.parametrize("score", [-1, 101])
def test_경계값_바로_바깥은_건너뛴다(tmp_path, score):
    p = make_csv(tmp_path, f"name,score\n김하나,{score}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == [(2, f"김하나,{score}", "점수가 0~100 밖")]


# ---------------------------------------------------------------------------
# 4. 특수 규칙
# ---------------------------------------------------------------------------

def test_동명이인은_둘_다_남는다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n김하나,91\n")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", 88), ("김하나", 91)]
    assert skipped == []


def test_빈_줄은_기록하지_않고_건너뛴다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n\n\n이두리,70\n")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", 88), ("이두리", 70)]
    assert skipped == []


def test_줄번호는_헤더를_1로_빈_줄도_세어서_매긴다(tmp_path):
    # 1 헤더 / 2 정상 / 3 빈 줄 / 4 잘못된 줄
    p = make_csv(tmp_path, "name,score\n김하나,88\n\n이두리,105\n")
    _, skipped = load_scores(p)
    assert skipped == [(4, "이두리,105", "점수가 0~100 밖")]


def test_건너뛴_줄이_여러_개면_순서대로_기록된다(tmp_path):
    p = make_csv(tmp_path, "name,score\n,1\n김하나,\n이두리,x\n박세찬,200\n정오름,1,2\n")
    _, skipped = load_scores(p)
    assert [(n, why) for n, _, why in skipped] == [
        (2, "이름이 비어 있음"),
        (3, "점수가 비어 있음"),
        (4, "점수가 정수가 아님"),
        (5, "점수가 0~100 밖"),
        (6, "열 개수가 2가 아님"),
    ]


def test_따옴표_안의_쉼표는_이름의_일부다(tmp_path):
    p = make_csv(tmp_path, 'name,score\n"최,네번",77\n')
    kept, skipped = load_scores(p)
    assert kept == [("최,네번", 77)]
    assert skipped == []


def test_BOM이_있어도_헤더가_정상_처리된다(tmp_path):
    p = make_csv(tmp_path, "name,score\n김하나,88\n", encoding="utf-8-sig")
    kept, skipped = load_scores(p)
    assert kept == [("김하나", 88)]
    assert skipped == []


def test_CRLF_줄바꿈도_처리된다(tmp_path):
    p = make_csv(tmp_path, "name,score\r\n김하나,88\r\n이두리,70\r\n")
    kept, _ = load_scores(p)
    assert kept == [("김하나", 88), ("이두리", 70)]


# ---------------------------------------------------------------------------
# 5. 실습 파일
# ---------------------------------------------------------------------------

def test_scores_csv_전체_결과():
    kept, skipped = load_scores(HERE / "scores.csv")
    assert kept == [
        ("김하나", 88),
        ("최,네번", 77),
        ("김하나", 91),
        ("윤보람", 64),
        ("서한별", 95),
    ]
    assert skipped == [
        (3, "이두리,105", "점수가 0~100 밖"),
        (4, "박세찬,", "점수가 비어 있음"),
        (7, "정오름,-5", "점수가 0~100 밖"),
        (8, "한겨울,결석", "점수가 정수가 아님"),
        (9, "장미르,72,비고없음", "열 개수가 2가 아님"),
    ]


def test_weird_csv_전체_결과():
    kept, skipped = load_scores(HERE / "weird.csv")
    assert kept == [("한겨울", 77), ("윤보람", 88)]
    assert skipped == [
        (2, ",90", "이름이 비어 있음"),
        (3, "서한별,", "점수가 비어 있음"),
        (4, "서한별,", "점수가 비어 있음"),
        (5, "김,쉼표,1000", "점수가 0~100 밖"),
        (6, "이두리,-100", "점수가 0~100 밖"),
        (7, "박세찬,88.5", "점수가 정수가 아님"),
        (9, "장미르,7 2", "점수가 정수가 아님"),
    ]


def test_empty_csv는_빈_결과():
    assert load_scores(HERE / "empty.csv") == ([], [])


# ---------------------------------------------------------------------------
# 6. 명령줄 실행 (python load_scores.py [경로])
# ---------------------------------------------------------------------------

def test_명령줄_실행은_결과를_출력한다(tmp_path, monkeypatch, capsys):
    p = make_csv(tmp_path, "name,score\n김하나,88\n이두리,105\n")
    monkeypatch.setattr(sys, "argv", ["load_scores.py", str(p)])
    runpy.run_path(str(HERE / "load_scores.py"), run_name="__main__")
    out = capsys.readouterr().out
    assert "읽은 줄 : 1개" in out
    assert "김하나 88" in out
    assert "건너뛴 줄 : 1개" in out
    assert "3행  이두리,105   ← 점수가 0~100 밖" in out


def test_명령줄_인자가_없으면_scores_csv를_읽는다(monkeypatch, capsys):
    monkeypatch.chdir(HERE)
    monkeypatch.setattr(sys, "argv", ["load_scores.py"])
    runpy.run_path(str(HERE / "load_scores.py"), run_name="__main__")
    out = capsys.readouterr().out
    assert "읽은 줄 : 5개" in out
    assert "건너뛴 줄 : 5개" in out
