import psutil
import time

def get_socket_info():
    '''
    [explain]
    

    [param] 
        None 

    [return]
    Tuple[List[Tuple[str|None, str|None, str|None, str|None]], List[Tuple[str|None, str|None, str|None, str|None]]]    
    '''

    def get_info(conn, is_tcp):
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None 
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
        pid   = str(conn.pid) if conn.pid else None

        return (laddr, raddr, pid) + ((conn.status if conn.status else None,) if is_tcp else ())

    return tuple([get_info(conn, kind == "tcp") for conn in psutil.net_connections(kind=kind)] for kind in ("tcp", "udp"))

# print(get_socket_info())
