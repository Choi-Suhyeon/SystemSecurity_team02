from process import Proc

def get_shared_objects(proc):
    '''
    [param]
    proc : (Proc) 메모리맵을 구할 process의 Proc 객체

    [return]
    (tuple) path만 문자열 형태로 tuple에 담아 반환.

    [exception]
    psutil.NoSuchProcess : 프로세스 부재.
    psutil.AccessDenied : 프로세스에 대한 접근 거부.
    '''
    return tuple(path for mmap in proc.memory_maps() if '.so' in (path := mmap.path))
    
# shared_objects = get_shared_objects(Proc(11593))
# print(shared_objects)

