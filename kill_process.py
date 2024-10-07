import os
import signal

def kill_process(pid):
    '''
    [param]
    pid : (int) 프로세스의 PID
    
    [return]
    None
    
    [exception]
    ProcessLookupError : PID에 해당하는 프로세스가 존재하지 않는 경우
    PermissionError : 프로세스 종료 권한이 없는 경우
    ValueError : PID가 정수형으로 입력되지 않은 경우
    '''
    
    os.kill(pid, signal.SIGTERM)