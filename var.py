
def basicPath():
    # return 'D:\\work\\qianrushi\\onlinePlatformDir'
    return '/home/chu-jiao/onlinePlatformDir'

def toolChainPath():
    return 'none'

def boardIP():
    return '192.168.9.10'

def getDeviceIDList():
    # return [6000, 6001]
    return [6000, 6001, 6002]

def serverIP():
    return '192.168.9.100'

def device2ip(device_id):
    ip_dict = {
        '6000': '192.168.9.10',
        '6001':'192.168.9.11',
        '6002':'192.168.9.12'
    }
    if str(device_id) in ip_dict.keys():
        return ip_dict[str(device_id)]

def ip2port(board_ip):
    port_dict = {
        '192.168.9.10' : 8081,
        '192.168.9.11' : 8082,
        '192.168.9.12' : 8083
    }
    if board_ip in port_dict.keys():
        return port_dict[board_ip]
    

def ip_list():
    return ['192.168.9.10', '192.168.9.11','192.168.9.12']
    # return ['192.168.9.10']