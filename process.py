import hashlib
import psutil
import signal
import os
import vt

class Proc(psutil.Process):
    def __init__(self, arg=None):
        '''
        [param]
        arg : (psutil.Process | int | None) 부모 클래스의 __init__에 인수로 넣을 매개변수

        [return]
        Proc 객체

        [exception]
        ValueError : 적절한 타입의 매개변수가 주어지지 않은 경우
        psutil.NoSuchProcess : 주어진 pid가 존재하지 않는 경우
        '''
        self.does_exist = ''
        self.vt         = ''

        self.api_key = 'e90aa4ffe5d2df373fabc7f00dcc22db00c978da9a9916331c8b23311c648883'

        match arg:
            case psutil.Process():
                super().__init__(arg.pid)
            case int():
                super().__init__(arg)
            case None:
                super().__init__()
            case _:
                raise ValueError

    def kill(self):
        '''
        [return]
        None

        [exception]
        ProcessLookupError : PID에 해당하는 프로세스가 존재하지 않는 경우
        PermissionError : 프로세스 종료 권한이 없는 경우
        ValueError : PID가 정수형으로 입력되지 않은 경우
        '''

        os.kill(self.pid, signal.SIGTERM)

    def increase_priority(self):
        try:
            self.change_priority(self.nice() - 1)
            print('debug : accepted')
        except Exception as e:
            print(f'debug : {e}')
            print('debug : denied')
            pass

    def decrease_priority(self):
        try:
            self.change_priority(self.nice() + 1)
        except:
            pass

    def change_priority(self, priority):
        '''
        [param]
        priority : (int) 설정할 우선순위 값 (-20 ~ +19)

        [return]
        None

        [exception]
        psutil.NoSuchProcess : PID가 해당하는 프로세스가 존재하지 않는 경우
        psutil.AccessDenied : 프로세스 우선순위를 변경할 권한이 없는 경우
        ValueError : 우선순위 값이 잘못된 경우
        '''

        # 리눅스에서의 우선순위 값은 -20에서 19 사이 (음수일수록 높은 우선순위)
        if priority < -20 or priority > 19:
            raise ValueError()

        # 리눅스에서 우선순위 설정
        self.nice(priority)

    def get_shared_objects(self):
        '''
        [return]
        (tuple) path만 문자열 형태로 tuple에 담아 반환.

        [exception]
        psutil.NoSuchProcess : 프로세스 부재.
        psutil.AccessDenied : 프로세스에 대한 접근 거부.
        '''

        return tuple(path for mmap in self.memory_maps() if '.so' in (path := mmap.path))

    def check_process_with_vt(self):
        '''
        [return]
        (None | tuple[int, int]) : hash를 구했으면 check_virustotal의 결과를 그대로 반환. 그렇지 않으면 None 반환.
        '''

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
            except Exception as e:
                return None

        def check_virustotal(file_hash):
            '''
            [param]
            file_hash : (str) 파일에 대한 해시

            [return]
            (None | tuple[int, int]) : 가져오는데 성공했으면 tuple에 악성으로 판단한 엔진 수와 전체 엔진 수를 넣어 반환.
            '''

            client = vt.Client(self.api_key)

            try:
                file_report = client.get_object(f"/files/{file_hash}")
                positives   = file_report.last_analysis_stats['malicious']  # 악성으로 판단한 엔진 수
                total       = sum(file_report.last_analysis_stats.values())  # 전체 엔진 수

                client.close()
                return f'{positives}/{total}'
            except vt.error.APIError as e:
                client.close()
                return 'Not Found'

        if not self.is_file_exists():
            return None

        self.vt = check_virustotal(file_hash) if (file_hash := get_file_hash(self.exe())) else ''


    def get_handles_info(self):
        limits_path = f'/proc/{self.pid}/limits'
        fd_path     = f'/proc/{self.pid}/fd'

        if not (os.path.exists(limits_path) and os.path.exists(fd_path)):
            return None

        handle_info = () 

        for fd in os.listdir(fd_path):
            try:
                handle_info += (os.readlink(os.path.join(fd_path, fd)),)
            except OSError:
                handle_info += (None,)

        with open(limits_path) as f:
            for l in f.readlines():
                if l.startswith('Max open files'):
                    soft_limit = l.removeprefix('Max open files').strip().split()[0]
                    break
            else:
                soft_limit = None


        return (soft_limit, handle_info)

    def is_file_exists(self):
        '''
        [return]
        bool : 파일 존재 여부
        '''

        try:
            self.does_exist = 'N' if os.readlink(f'/proc/{self.pid}/exe').endswith(' (deleted)') else 'Y'
            return self.does_exist == 'Y'
        except:
            self.does_exist = 'N'
            return False

