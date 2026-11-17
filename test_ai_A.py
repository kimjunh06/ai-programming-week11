# test_load_scores.py
#
# load_scores.load_scores(path) 단위 테스트 (pytest)
# 실행: pytest -v test_load_scores.py
#
# 구성
#   1) 정상 동작
#   2) 건너뛰는 줄(예외적 입력) - 열 개수 / 이름 / 점수 비어 있음 / 정수 아님 / 범위 밖
#   3) 경계값 (0, 100, -1, 101 등)
#   4) 파일 형식(BOM, CRLF, 빈 파일, 빈 줄, 따옴표 등)
#   5) 파일 자체의 오류 (없는 파일, 인코딩 오류)

import pytest

from load_scores import MAX_SCORE, MIN_SCORE, load_scores

HEADER = "이름,점수\n"

# 건너뛴 줄에 기록되는 사유 문자열 (구현과 동일하게 맞춤)
REASON_COLS = "열 개수가 2가 아님"
REASON_NAME = "이름이 비어 있음"
REASON_EMPTY_SCORE = "점수가 비어 있음"
REASON_NOT_INT = "점수가 정수가 아님"
REASON_RANGE = "점수가 0~100 밖"


@pytest.fixture
def write_csv(tmp_path):
    """문자열을 바이트로 그대로 써서 CSV 파일 경로를 돌려주는 도우미.

    write_text 는 줄바꿈을 바꿀 수 있으므로 write_bytes 로 \\r\\n 등을 보존한다.
    """

    def _write(content, encoding="utf-8", name="scores.csv"):
        path = tmp_path / name
        path.write_bytes(content.encode(encoding))
        return path

    return _write


# ---------------------------------------------------------------------------
# 1) 정상 동작
# ---------------------------------------------------------------------------
class TestNormal:
    def test_valid_rows_are_kept_in_file_order(self, write_csv):
        path = write_csv(HEADER + "홍길동,90\n김영희,75\n이철수,100\n")
        kept, skipped = load_scores(path)
        assert kept == [("홍길동", 90), ("김영희", 75), ("이철수", 100)]
        assert skipped == []

    def test_returns_tuple_of_two_lists(self, write_csv):
        result = load_scores(write_csv(HEADER + "a,1\n"))
        assert isinstance(result, tuple) and len(result) == 2
        kept, skipped = result
        assert isinstance(kept, list)
        assert isinstance(skipped, list)
        # 점수는 문자열이 아니라 int 로 변환되어야 한다
        assert isinstance(kept[0][1], int)

    def test_accepts_str_path_as_well_as_pathlib(self, write_csv):
        path = write_csv(HEADER + "a,1\n")
        assert load_scores(str(path)) == load_scores(path)

    def test_header_is_always_skipped_even_if_it_looks_like_data(self, write_csv):
        # 1번째 줄은 내용과 상관없이 헤더로 취급되어 무시되고, 기록도 남지 않는다
        path = write_csv("홍길동,90\n김영희,80\n")
        kept, skipped = load_scores(path)
        assert kept == [("김영희", 80)]
        assert skipped == []

    def test_whitespace_around_name_and_score_is_stripped(self, write_csv):
        path = write_csv(HEADER + "  홍길동  ,  85  \n")
        kept, skipped = load_scores(path)
        assert kept == [("홍길동", 85)]
        assert skipped == []

    def test_duplicate_names_are_both_kept(self, write_csv):
        path = write_csv(HEADER + "홍길동,70\n홍길동,80\n")
        kept, _ = load_scores(path)
        assert kept == [("홍길동", 70), ("홍길동", 80)]

    def test_quoted_name_containing_comma_is_one_column(self, write_csv):
        path = write_csv(HEADER + '"Kim, Jr",90\n')
        kept, skipped = load_scores(path)
        assert kept == [("Kim, Jr", 90)]
        assert skipped == []

    @pytest.mark.parametrize("raw, expected", [("+85", 85), ("0085", 85), ("-0", 0)])
    def test_int_style_variants_are_accepted(self, write_csv, raw, expected):
        # int() 가 받아주는 표기(부호, 앞자리 0)는 그대로 유효 점수로 처리된다
        path = write_csv(HEADER + f"a,{raw}\n")
        kept, skipped = load_scores(path)
        assert kept == [("a", expected)]
        assert skipped == []

    def test_mixed_valid_and_invalid_rows(self, write_csv):
        content = HEADER + (
            "홍길동,90\n"      # 2: 유효
            "김영희,abc\n"     # 3: 정수 아님
            "이철수,100\n"     # 4: 유효
            "박민수,101\n"     # 5: 범위 밖
            "최지우,0\n"       # 6: 유효
        )
        kept, skipped = load_scores(write_csv(content))
        assert kept == [("홍길동", 90), ("이철수", 100), ("최지우", 0)]
        assert skipped == [
            (3, "김영희,abc", REASON_NOT_INT),
            (5, "박민수,101", REASON_RANGE),
        ]


# ---------------------------------------------------------------------------
# 2) 예외적 입력: 건너뛰는 줄과 사유
# ---------------------------------------------------------------------------
class TestSkippedRows:
    @pytest.mark.parametrize(
        "line, expected_original",
        [
            ("홍길동", "홍길동"),                 # 열 1개
            ("홍길동,90,추가", "홍길동,90,추가"),  # 열 3개
            (",,", ",,"),                         # 빈 열 3개
            ("   ", "   "),                       # 공백만 있는 줄은 '빈 줄'이 아니라 열 1개
        ],
    )
    def test_wrong_column_count(self, write_csv, line, expected_original):
        kept, skipped = load_scores(write_csv(HEADER + line + "\n"))
        assert kept == []
        assert skipped == [(2, expected_original, REASON_COLS)]

    @pytest.mark.parametrize("line, original", [(",90", ",90"), ("   ,90", "   ,90")])
    def test_empty_or_blank_name(self, write_csv, line, original):
        kept, skipped = load_scores(write_csv(HEADER + line + "\n"))
        assert kept == []
        assert skipped == [(2, original, REASON_NAME)]

    @pytest.mark.parametrize("line", ["홍길동,", "홍길동,   "])
    def test_empty_or_blank_score(self, write_csv, line):
        kept, skipped = load_scores(write_csv(HEADER + line + "\n"))
        assert kept == []
        assert skipped == [(2, line, REASON_EMPTY_SCORE)]

    @pytest.mark.parametrize(
        "raw", ["abc", "85.0", "85.5", "85점", "1e2", "0x10", "--5", "N/A"]
    )
    def test_score_not_an_integer(self, write_csv, raw):
        kept, skipped = load_scores(write_csv(HEADER + f"홍길동,{raw}\n"))
        assert kept == []
        assert skipped == [(2, f"홍길동,{raw}", REASON_NOT_INT)]

    def test_name_and_score_both_empty_reports_name_first(self, write_csv):
        # 검사 순서: 이름 -> 점수 비어 있음 이므로 이름 사유가 기록되어야 한다
        kept, skipped = load_scores(write_csv(HEADER + ",\n"))
        assert kept == []
        assert skipped == [(2, ",", REASON_NAME)]

    def test_empty_name_takes_priority_over_bad_score(self, write_csv):
        kept, skipped = load_scores(write_csv(HEADER + ",abc\n"))
        assert skipped == [(2, ",abc", REASON_NAME)]

    def test_skipped_original_is_unstripped_raw_row(self, write_csv):
        # 기록되는 원본은 strip 하기 전의 값을 ',' 로 다시 이은 문자열이다
        kept, skipped = load_scores(write_csv(HEADER + " a , x \n"))
        assert kept == []
        assert skipped == [(2, " a , x ", REASON_NOT_INT)]

    def test_original_of_quoted_row_is_rejoined_with_commas(self, write_csv):
        # 따옴표는 csv 파서가 제거하므로 원본에는 남지 않는다(현재 동작 확인)
        kept, skipped = load_scores(write_csv(HEADER + '"Kim, Jr",90,x\n'))
        assert kept == []
        assert skipped == [(2, "Kim, Jr,90,x", REASON_COLS)]

    def test_multiple_skipped_rows_keep_order_and_line_numbers(self, write_csv):
        content = HEADER + "a\n,1\nb,\nc,x\nd,999\n"
        _, skipped = load_scores(write_csv(content))
        assert skipped == [
            (2, "a", REASON_COLS),
            (3, ",1", REASON_NAME),
            (4, "b,", REASON_EMPTY_SCORE),
            (5, "c,x", REASON_NOT_INT),
            (6, "d,999", REASON_RANGE),
        ]


# ---------------------------------------------------------------------------
# 3) 경계값
# ---------------------------------------------------------------------------
class TestBoundaries:
    def test_constants(self):
        assert MIN_SCORE == 0
        assert MAX_SCORE == 100

    @pytest.mark.parametrize("score", [0, 1, 99, 100])
    def test_scores_inside_range_are_kept(self, write_csv, score):
        kept, skipped = load_scores(write_csv(HEADER + f"a,{score}\n"))
        assert kept == [("a", score)]
        assert skipped == []

    @pytest.mark.parametrize("score", [-1, 101, -100, 1000, 999999999999999999999])
    def test_scores_outside_range_are_skipped(self, write_csv, score):
        kept, skipped = load_scores(write_csv(HEADER + f"a,{score}\n"))
        assert kept == []
        assert skipped == [(2, f"a,{score}", REASON_RANGE)]

    def test_lowest_and_highest_together_with_just_outside_values(self, write_csv):
        content = HEADER + "lo_out,-1\nlo,0\nhi,100\nhi_out,101\n"
        kept, skipped = load_scores(write_csv(content))
        assert kept == [("lo", 0), ("hi", 100)]
        assert [s[0] for s in skipped] == [2, 5]
        assert all(s[2] == REASON_RANGE for s in skipped)


# ---------------------------------------------------------------------------
# 4) 파일 형식: 빈 파일, 헤더만, 빈 줄, BOM, CRLF
# ---------------------------------------------------------------------------
class TestFileFormat:
    def test_empty_file(self, write_csv):
        assert load_scores(write_csv("")) == ([], [])

    def test_header_only(self, write_csv):
        assert load_scores(write_csv(HEADER)) == ([], [])

    def test_header_only_without_trailing_newline(self, write_csv):
        assert load_scores(write_csv("이름,점수")) == ([], [])

    def test_last_row_without_trailing_newline(self, write_csv):
        kept, skipped = load_scores(write_csv(HEADER + "a,50"))
        assert kept == [("a", 50)]
        assert skipped == []

    def test_blank_lines_are_ignored_and_not_recorded(self, write_csv):
        content = HEADER + "\n\na,10\n\n\n"
        kept, skipped = load_scores(write_csv(content))
        assert kept == [("a", 10)]
        assert skipped == []

    def test_blank_lines_still_count_toward_line_numbers(self, write_csv):
        # 빈 줄도 줄 번호는 센다: 2(빈 줄), 3(a), 4(빈 줄), 5(b)
        content = HEADER + "\na,10\n\nb,abc\n"
        kept, skipped = load_scores(write_csv(content))
        assert kept == [("a", 10)]
        assert skipped == [(5, "b,abc", REASON_NOT_INT)]

    def test_utf8_bom_is_handled(self, write_csv):
        # utf-8-sig 로 열기 때문에 BOM 이 있어도 정상적으로 읽혀야 한다
        path = write_csv(HEADER + "홍길동,90\n", encoding="utf-8-sig")
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # BOM 이 실제로 있는지 확인
        kept, skipped = load_scores(path)
        assert kept == [("홍길동", 90)]
        assert skipped == []

    def test_crlf_line_endings(self, write_csv):
        content = "이름,점수\r\n홍길동,90\r\n김영희,abc\r\n"
        kept, skipped = load_scores(write_csv(content))
        assert kept == [("홍길동", 90)]
        # 원본 문자열에 '\r' 이 섞이지 않아야 한다
        assert skipped == [(3, "김영희,abc", REASON_NOT_INT)]

    def test_non_ascii_names_are_preserved(self, write_csv):
        kept, _ = load_scores(write_csv(HEADER + "홍길동,90\nJosé,80\n山田,70\n"))
        assert kept == [("홍길동", 90), ("José", 80), ("山田", 70)]

    def test_large_file(self, write_csv):
        rows = "".join(f"s{i},{i % 101}\n" for i in range(5000))
        kept, skipped = load_scores(write_csv(HEADER + rows))
        assert len(kept) == 5000
        assert skipped == []


# ---------------------------------------------------------------------------
# 5) 파일 자체의 오류 (함수가 예외를 그대로 전달하는지)
# ---------------------------------------------------------------------------
class TestFileErrors:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_scores(tmp_path / "does_not_exist.csv")

    def test_directory_path_raises(self, tmp_path):
        # 디렉터리를 파일처럼 열면 OSError 계열(IsADirectoryError 등)이 발생한다
        with pytest.raises(OSError):
            load_scores(tmp_path)

    def test_non_utf8_file_raises_unicode_error(self, write_csv):
        # cp949 로 저장된 한글 파일은 utf-8 로 읽을 수 없다
        path = write_csv(HEADER + "홍길동,90\n", encoding="cp949")
        with pytest.raises(UnicodeDecodeError):
            load_scores(path)

    def test_none_path_raises_type_error(self):
        with pytest.raises(TypeError):
            load_scores(None)