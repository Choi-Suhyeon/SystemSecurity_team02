from functools import reduce
from process import Proc
import psutil

def get_process_tree(procs):
    '''
    [param]
    procs: (iterable) process tree를 구할 Proc 객체들의 시퀀스.

    [return]
    pid를 key로 key의 자식 프로세스들을(Proc 객체들의 집합) value로 하는 딕셔너리.
    '''
    result = dict()

    for p in procs:
        try:
            key = p.ppid()
        except Exception:
            continue

        result[key] = result.get(key, set()) | set((p,))

    return result

