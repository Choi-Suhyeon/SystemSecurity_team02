from process import Proc

import tabulate
import psutil


def get_snapshot(procs):
    cpu_count = psutil.cpu_count()
    info      = list()

    for p in procs:
        try:
            info.append([
                p.name(),      str(p.pid),                              str(p.ppid()),                    p.username(),
                str(p.nice()), f'{p.cpu_percent(0)/cpu_count:0>6.3f}%', f'{p.memory_percent():0>6.3f}%',
            ])
        except Exception:
            continue

    headers = ['name', 'pid', 'ppid', 'user', 'priority', 'cpu(%)', 'memory(%)']

    return tabulate.tabulate(info, headers=headers)

def save_snapshot(procs, file_path):
    content = get_snapshot(procs)

    with open(file_path, 'w') as f:
        f.write(content)

'''
if __name__ == "__main__":
    procs = [Proc(i) for i in psutil.process_iter()]
    save_snapshot(procs, './snapshott')
'''
