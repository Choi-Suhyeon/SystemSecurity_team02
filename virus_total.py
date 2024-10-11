from process import Proc
import hashlib
import vt

def get_file_hash(file_path):
    '''
    [param]
    file_path : (str) 해시를 취할 파일의 경로
    [return]
    (None | str) 실패하면 None, 성공하면, hash 값을 문자열로 반환.
    '''

    try:
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
    except:
        return None

def check_virustotal(file_hash, api_key):
    '''
    [param]
    file_hash : (str) 파일에 대한 해시
    api_key   : virus total의 api key

    [return]
    (None | tuple[int, int]) : 가져오는데 성공했으면 tuple에 악성으로 판단한 엔진 수와 전체 엔진 수를 넣어 반환.
    '''
    client = vt.Client(api_key)
    
    try:
        file_report = client.get_object(f"/files/{file_hash}")
        positives   = file_report.last_analysis_stats['malicious']  # 악성으로 판단한 엔진 수
        total       = sum(file_report.last_analysis_stats.values())  # 전체 엔진 수
        result      = (positives, total)

    except vt.error.APIError as e:
        result = None

    client.close()

    return result

def analyze_process(proc, api_key):
    '''
    [param]
    proc    : (Proc) 검사를 진행할 프로세스의 Proc 객체
    api_key : virus total의 api key

    [return]
    (None | tuple[int, int]) : hash를 구했으면 check_virustotal의 결과를 그대로 반환. 그렇지 않으면 None 반환.
    '''

    return check_virustotal(file_hash, api_key) if (file_hash := get_file_hash(proc.exe())) else None
              
# pid     = 0
# api_key = ''  
# result  = analyze_process(Proc(pid), api_key)

# print(f'{result[0]}/{result[1]}' if result else 'None')

