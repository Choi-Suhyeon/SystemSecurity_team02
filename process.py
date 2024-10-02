import psutil

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

        match arg:
            case psutil.Process():
                super().__init__(arg.pid)
            case int():
                super().__init__(arg)
            case None:
                super().__init__()
            case _:
                raise ValueError

