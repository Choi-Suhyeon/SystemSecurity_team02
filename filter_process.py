import os
import re
import psutil

def filter_process_by_name(pattern):
    """
    [explain]
        주어진 정규 표현식 패턴을 사용하여 프로세스 이름을 필터링하는 함수
    [param]
        pattern : str - 필터링에 사용할 정규 표현식 패턴
    [return]
        list - 정규 표현식 패턴과 일치하는 프로세스 이름 목록
        None - 유효하지 않은 패턴 또는 기타 오류 발생 시
    """
    try:
        # 일치하는 프로세스 이름 목록을 저장할 리스트 초기화
        matching_processes = []

        # 시스템의 모든 프로세스를 순회
        for proc in psutil.process_iter(['name']):
            proc_name = proc.info.get('name', '')
            # 정규 표현식과 일치하는 프로세스 이름만 리스트에 추가
            if re.search(pattern, proc_name):
                matching_processes.append(proc_name)
                
        return matching_processes if matching_processes else None
    except re.error:
        # 잘못된 정규 표현식 사용 시 None 반환
        return None
    except psutil.Error:
        # 프로세스 정보를 얻는 데 실패할 경우 None 반환
        return None