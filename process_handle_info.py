import os

class ProcessHandleInfo:
    def __init__(self, pid):
        '''
        init class and save process ID

        [param]
          pid : (int) Remote process ID
        '''
        self.pid = pid
        self.fd_path = f"/proc/{pid}/fd"
        
        

    def get_process_handles(pid):
        '''
	    [param]
	        pid: (int) 파일 handle 정보를 얻고자 하는 프로세스 ID
	    [return]
            (tuple) 해당 프로세스의 모든 파일 handle 정보를 담고 있는 tuple

        이 함수는 프로세스 ID (PID)를 받아 해당 프로세스와 연관된 모든 파일 handle 정보를 반환
        반환 값은 tuple로, 각 handle의 경로를 포함합니다.
	    '''
    
        handle_info = []

        fd_path = f"/proc/{pid}/fd"
    
        if os.path.exists(fd_path):
            for fd in os.listdir(fd_path):
                try:
                    # 각 파일 disk creator에 해당하는 자원 정보를 가져와 handle 정보 리스트에 추가
                    handle = os.readlink(os.path.join(fd_path, fd))
                    handle_info.append(handle)
                except OSError:
                    # 특정 파일 disk creator를 읽을 수 없는 경우(예: 권한 문제) 해당 핸들은 SKIP
                    continue  

        # 반환된 handle 정보 리스트를 tuple로 변환
        return tuple(handle_info)
    
    def get_max_handles(pid):
        '''
        [param]
          pid : (int) 최대 핸들 수를 얻고자 하는 프로세스 ID
        [return]
          (int) 해당 프로세스에서 허용되는 최대 핸들 수

        이 함수는 /proc/[PID]/limits 파일을 읽어, 해당 프로세스가 가질 수 있는 최대 핸들 수를 반환
        '''
        limits_file = f"/proc/{pid}/limits"
    
        if os.path.exists(limits_file):
            with open(limits_file, 'r') as file:
                for line in file:
                    if 'Max open files' in line:
                        # 최대 핸들 수를 반환
                        # 네 번째 열이 최대 값임
                        return int(line.split()[3])  
    
        # 파일이 존재하지 않거나 값을 얻을 수 없으면 None 반환
        return None
    
    def get_current_handles(pid):
        '''
        [param]
          pid : (int) 현재 핸들 수를 얻고자 하는 프로세스 ID
        [return]
          (int) 해당 프로세스가 현재 가지고 있는 핸들 수

        이 함수는 /proc/[PID]/fd/ 디렉토리 내 파일 수를 확인하여, 해당 프로세스가 현재 가지고 있는 핸들 수를 반환
        '''
        fd_path = f"/proc/{pid}/fd"
    
        if os.path.exists(fd_path):
            # 파일 handle 수를 반환, 즉 디렉토리 내 파일의 수를 반환
            return len(os.listdir(fd_path))
    
        # 디렉토리가 존재하지 않으면 0 반환
        return 0
    

# Process handle object create
pid = 367
process_info = ProcessHandleInfo(pid)

# Get all info from process handles
handles = process_info.get_process_handles()
print(f"PID: {pid}, Handles: {handles}")

# get max handles number
max_handles = process_info.get_max_handles()
print(f"PID: {pid}, Max Handles: {max_handles}")

# get current handles number
current_handles = process_info.get_current_handles()
print(f"PID: {pid}, Current Handles: {current_handles}")
