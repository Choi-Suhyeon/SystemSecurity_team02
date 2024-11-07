import os
import re
import psutil

def check_file_exists_on_disk(file_path):
    """
    [explain]
        지정된 경로에 파일이 실제로 존재하는지 확인하는 함수
    [param]
        file_path : str - 파일의 절대 경로 또는 상대 경로
    [return]
        bool - 파일 존재 여부 (True 또는 False)
        None - 유효하지 않은 경로 또는 기타 오류 발생 시
    """
    try:
        # 파일이 존재하면 True 반환, 존재하지 않으면 False 반환
        return os.path.isfile(file_path)
    except Exception as e:
        # 예외 발생 시 None 반환
        return None