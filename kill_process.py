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
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"프로세스 {pid}가 정상적으로 종료되었습니다.")
    except ProcessLookupError:
        print(f"PID {pid}에 해당하는 프로세스가 존재하지 않습니다.")
    except PermissionError:
        print(f"PID {pid} 프로세스를 종료할 권한이 없습니다.")
    except ValueError:
        print("올바른 숫자 형태의 PID를 입력해주세요.")
    except Exception as e:
        print(f"예상치 못한 에러가 발생했습니다: {e}")