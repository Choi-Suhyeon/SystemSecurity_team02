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
    return reduce(lambda d, p: d | { p.ppid(): d.get(p.ppid(), set()) | set((p,)) }, procs, dict())

# a = get_process_tree(Proc(i) for i in psutil.process_iter())
# print(a)
# print('------\n', a.keys())

p = Proc(37099)
print([i.path for i in p.open_files()])
