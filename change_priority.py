import psutil

def change_priority(pid, priority):
    '''
    [param]
    pid : (int) 우선순위를 변경할 프로세스의 PID
    priority : (int) 설정할 우선순위 값 (-20 ~ +19)

    [return]
    None
    
    [variable]
    process : (psutil.Process) 주어진 PID를 기반으로 생성된 프로세스 객체
    
    [exception]
    psutil.NoSuchProcess : PID가 해당하는 프로세스가 존재하지 않는 경우
    psutil.AccessDenied : 프로세스 우선순위를 변경할 권한이 없는 경우
    ValueError : 우선순위 값이 잘못된 경우
    '''
    
    # 해당 PID의 프로세스 가져오기
    process = psutil.Process(pid)

    # 리눅스에서의 우선순위 값은 -20에서 19 사이 (음수일수록 높은 우선순위)
    if priority < -20 or priority > 19:
        raise ValueError()

    # 리눅스에서 우선순위 설정
    process.nice(priority)
        