# test_load_scores.py
import pytest

from load_scores import load_scores


# ---------- 도우미 ----------
def make_csv(tmp_path, body, header="name,score\n", name="scores.csv"):
    """헤더 + 본문을 UTF-8 CSV 파일로 만들고 경로를 돌려준다."""
    p = tmp_path / name
    p.write_text(header + body, encoding="utf-8")
    return p


def skipped_lines(skipped):
    """skipped 에서 (줄번호, 원본줄) 만 뽑는다. 줄 끝 개행은 무시한다."""
    return [(no, raw.rstrip("\r\n")) for no, raw, _ in skipped]


def assert_reasons_present(skipped):
    """모든 skipped 기록에 비어 있지 않은 이유 문자열이 있어야 한다."""
    for rec in skipped:
        assert len(rec) == 3
        no, raw, reason = rec
        assert isinstance(no, int)
        assert isinstance(raw, str)
        assert isinstance(reason, str) and reason.strip() != ""


# ---------- 정상 ----------
def test_valid_rows_are_kept_in_order(tmp_path):
    p = make_csv(tmp_path, "kim,85\nlee,90\npark,70\n")
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85), ("lee", 90), ("park", 70)]
    assert skipped == []


def test_scores_are_int(tmp_path):
    p = make_csv(tmp_path, "kim,85\n")
    kept, _ = load_scores(p)
    assert isinstance(kept[0][1], int)
    assert isinstance(kept[0][0], str)


def test_accepts_str_path(tmp_path):
    p = make_csv(tmp_path, "kim,85\n")
    kept, skipped = load_scores(str(p))
    assert kept == [("kim", 85)]
    assert skipped == []


def test_utf8_korean_names(tmp_path):
    p = make_csv(tmp_path, "김철수,88\n이영희,92\n")
    kept, skipped = load_scores(p)
    assert kept == [("김철수", 88), ("이영희", 92)]
    assert skipped == []


def test_no_trailing_newline(tmp_path):
    p = make_csv(tmp_path, "kim,85\nlee,90")
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85), ("lee", 90)]
    assert skipped == []


# ---------- ④ 금지 사항: 중복 이름 보존, 조용한 폐기 금지 ----------
def test_duplicate_names_are_both_kept(tmp_path):
    p = make_csv(tmp_path, "kim,85\nkim,85\nkim,60\n")
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85), ("kim", 85), ("kim", 60)]
    assert skipped == []


def test_every_nonblank_data_line_is_kept_or_skipped(tmp_path):
    # 빈 줄을 뺀 데이터 줄은 반드시 kept 나 skipped 중 한 곳에 있어야 한다
    body = "kim,85\nbad\n,70\nlee,abc\npark,101\nchoi,100\n"
    p = make_csv(tmp_path, body)
    kept, skipped = load_scores(p)
    assert len(kept) + len(skipped) == 6
    assert kept == [("kim", 85), ("choi", 100)]
    assert_reasons_present(skipped)


# ---------- ③ 실패: 파일 없음 ----------
def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_scores(tmp_path / "no_such_file.csv")


# ---------- ⑤ 예외 상황: 헤더만 ----------
def test_header_only_returns_empty(tmp_path):
    p = make_csv(tmp_path, "")
    assert load_scores(p) == ([], [])


def test_header_only_without_newline(tmp_path):
    p = make_csv(tmp_path, "", header="name,score")
    assert load_scores(p) == ([], [])


# ---------- ⑤ 예외 상황: 건너뛰고 기록 ----------
@pytest.mark.parametrize(
    "line",
    [
        "kim",              # 열 1개
        "kim,85,extra",     # 열 3개
        "kim,85,",          # 끝 쉼표로 열 3개
    ],
    ids=["one_col", "three_cols", "trailing_comma"],
)
def test_wrong_column_count_is_skipped(tmp_path, line):
    p = make_csv(tmp_path, line + "\nlee,90\n")
    kept, skipped = load_scores(p)
    assert kept == [("lee", 90)]
    assert skipped_lines(skipped) == [(2, line)]
    assert_reasons_present(skipped)


@pytest.mark.parametrize(
    "line",
    ["kim,", "kim,abc", "kim,85.5", "kim,8 5", "kim,1e2"],
    ids=["empty", "letters", "float", "inner_space", "exponent"],
)
def test_empty_or_non_integer_score_is_skipped(tmp_path, line):
    p = make_csv(tmp_path, line + "\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped_lines(skipped) == [(2, line)]
    assert_reasons_present(skipped)


@pytest.mark.parametrize("score", ["-1", "101", "-100", "1000"])
def test_out_of_range_score_is_skipped(tmp_path, score):
    line = f"kim,{score}"
    p = make_csv(tmp_path, line + "\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped_lines(skipped) == [(2, line)]
    assert_reasons_present(skipped)


def test_empty_name_is_skipped(tmp_path):
    p = make_csv(tmp_path, ",80\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped_lines(skipped) == [(2, ",80")]
    assert_reasons_present(skipped)


def test_both_fields_empty_is_skipped(tmp_path):
    p = make_csv(tmp_path, ",\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped_lines(skipped) == [(2, ",")]
    assert_reasons_present(skipped)


# ---------- 경계값 ----------
@pytest.mark.parametrize("score", [0, 1, 99, 100])
def test_boundary_scores_are_kept(tmp_path, score):
    p = make_csv(tmp_path, f"kim,{score}\n")
    kept, skipped = load_scores(p)
    assert kept == [("kim", score)]
    assert skipped == []


@pytest.mark.parametrize("score", [-1, 101])
def test_just_outside_boundary_is_skipped(tmp_path, score):
    p = make_csv(tmp_path, f"kim,{score}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert len(skipped) == 1


# ---------- 빈 줄 ----------
def test_blank_lines_are_ignored_without_record(tmp_path):
    p = make_csv(tmp_path, "kim,85\n\nlee,90\n\n")
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85), ("lee", 90)]
    assert skipped == []


def test_only_blank_lines_after_header(tmp_path):
    p = make_csv(tmp_path, "\n\n\n")
    assert load_scores(p) == ([], [])


# ---------- ⑥ 줄번호: 헤더가 1번 ----------
def test_line_numbers_count_header_as_one(tmp_path):
    body = (
        "kim,85\n"     # 2
        "bad\n"        # 3
        "lee,90\n"     # 4
        "park,150\n"   # 5
    )
    p = make_csv(tmp_path, body)
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85), ("lee", 90)]
    assert skipped_lines(skipped) == [(3, "bad"), (5, "park,150")]


def test_line_numbers_include_blank_lines(tmp_path):
    body = (
        "kim,85\n"     # 2
        "\n"           # 3 (빈 줄, 기록 없음)
        "lee,xx\n"     # 4
    )
    p = make_csv(tmp_path, body)
    kept, skipped = load_scores(p)
    assert kept == [("kim", 85)]
    assert skipped_lines(skipped) == [(4, "lee,xx")]


def test_skipped_keeps_original_line_text(tmp_path):
    p = make_csv(tmp_path, "홍길동,백점\n")
    _, skipped = load_scores(p)
    assert skipped_lines(skipped) == [(2, "홍길동,백점")]
