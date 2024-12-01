from process_tree import get_process_tree
from process import Proc
import psutil
import lupa

output = []

def redirect_print(*args):
    output.append(' '.join(str(arg) for arg in args)) 

lua = lupa.LuaRuntime(unpack_returned_tuples=True)

lua.globals().process_viewer = {
    'Proc': Proc,
    'get_process_tree': get_process_tree,
    'get_procs': lambda: [Proc(i) for i in psutil.process_iter()],
}

lua.globals().print = redirect_print

lua.execute(
    """
    os = nil
    io = nil
    debug = nil
    """
)

def run_user_script(script):
    try:
        lua.execute(script)
        
        result = '\n'.join(output)

        output.clear()
        return result

    except lupa.LuaError as e:
        return str(e)
        
'''
# 허용된 기능 테스트
safe_script = """
local pv = process_viewer
local procs = pv.get_procs()

print(procs)
print(type(procs))
print(wow)

print(procs[0])

local proc = pv.Proc(21683)  -- 첫 번째 PID의 Proc 객체 생성
print("Handle Info: ", proc:get_handles_info())
print("wow2")
"""

print("=== Safe Script Execution ===")
print(run_user_script(safe_script))


# 허용되지 않은 기능 테스트
unsafe_script = """
-- os 접근 시도
local f = io.open("/etc/passwd", "r")  -- 파일 접근 시도
local g = os.execute("ls")  -- os 명령어 실행
"""

print("\n=== Unsafe Script Execution ===")
print(run_user_script(unsafe_script))
'''
