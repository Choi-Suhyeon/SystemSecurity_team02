import os
import re
import psutil

def filter_process_by_name(procs, pattern):
    """
    [explain]
        주어진 정규 표현식 패턴을 사용하여 프로세스 이름을 필터링하는 함수
    [param]
        procs : list[Proc] : Proc 객체들의 리스트
        pattern : str - 필터링에 사용할 정규 표현식 패턴
    [return]
        list - 정규 표현식 패턴과 일치하는 프로세스 이름 목록
        None - 유효하지 않은 패턴 또는 기타 오류 발생 시
    """
    try:
        return [p for p in procs if re.search(pattern, p.name())]
    except re.error:
        return None
