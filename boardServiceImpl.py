import redis
from operation import makeGeneralProject, upload_program
import os
import uuid
import redis
import var
import pickle
import paramiko
import time
import re
import subprocess
import sys
import socket
from datetime import datetime

ssh_dict = {}

device_dict = {}
session_id2device = {}
transport_dict = {}


def environmentRequest(user_id, exp_id, exp_type):
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    sessionVo = {}
    toolchainPath = var.toolChainPath()
    basicPath = var.basicPath()
    if makeGeneralProject(toolchainPath, basicPath, os.path.join(basicPath,'workdir', user_id, exp_id), user_id+'_'+exp_id, exp_type) == False:
        sessionVo['fail'] = 1
        return sessionVo
    session_uuid = 'session_'+str(uuid.uuid1())
    experimentVO = {}
    experimentVO['exp_id'] = exp_id
    experimentVO['user_id'] = user_id
    red.set(session_uuid,  pickle.dumps(experimentVO))
    sessionVo['fail'] = 0
    sessionVo['session_id'] = session_uuid
    return sessionVo

def codeSubmit(session_id, code, code_name):
    basicPath = var.basicPath()
    codeSubmitVO = {}
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    if red.exists(session_id) == False:
        codeSubmitVO['fail'] = 1
        return codeSubmitVO
    experimentVO = red.get(session_id)
    experimentVO = pickle.loads(experimentVO)
    code_file_path = os.path.join(basicPath, 'workdir', experimentVO['user_id'], experimentVO['exp_id'],'src',code_name)
    f = open(code_file_path,'w')
    f.write(code)
    f.close()
    codeSubmitVO['fail'] = 0
    return codeSubmitVO

def compile(session_id):
    compileVO = {}
    basicPath = var.basicPath()
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    if red.exists(session_id) == False:
        compileVO['fail'] = 1
        return compileVO
    experimentVO = red.get(session_id)
    experimentVO = pickle.loads(experimentVO)
    os.popen('chmod 777 '+os.path.join(basicPath, 'workdir', experimentVO['user_id'], experimentVO['exp_id'], 'env', 'shell_compile.bat'))
    cmd_compile = os.path.join(basicPath, 'workdir', experimentVO['user_id'], experimentVO['exp_id'], 'env', 'shell_compile.bat')
    obj_path = os.path.join(basicPath, 'workdir', experimentVO['user_id'], experimentVO['exp_id'], 'src', experimentVO['user_id'] + '_' + experimentVO['exp_id'] )
    if os.path.exists(obj_path):
        os.remove(obj_path)
    ex = subprocess.Popen(cmd_compile, stdout=subprocess.PIPE, shell=True)
    out, err  = ex.communicate()
    status = ex.wait()
    compile_result = out.decode()
    compileVO['res'] = compile_result
    if status == 0:
        compileVO['fail'] = 0
    else:
        compileVO['fail'] = 1
    return compileVO

def programUpload(session_id, device_id, exp_type):
    basicPath = var.basicPath()
    programUploadVO = {}
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    if red.exists(session_id) == False:
        programUploadVO['fail'] = 1
        return programUploadVO
    experimentVO = red.get(session_id)
    experimentVO = pickle.loads(experimentVO)
    ip = var.device2ip(device_id)
    transport = paramiko.Transport((ip, 22))  # 建立一个加密的管道
    transport.start_client()
    # 用户名密码方式
    transport.auth_password("root", "root")
    # 打开一个通道
    channel = transport.open_session()
    channel.settimeout(7200)
    # 获取一个终端
    channel.get_pty()
    # 激活器
    channel.invoke_shell()
    cmd_cd = 'cd '+ os.path.join('/home/experiment',experimentVO['user_id'])
    cmd_chmod = 'chmod 777 '+experimentVO['user_id']+'_'+experimentVO['exp_id']
    cmd_mkdir = 'mkdir /home/experiment/'+experimentVO['user_id']
    channel.send(cmd_mkdir+'\r')
    channel.send(cmd_cd+'\r')
    channel.send(cmd_chmod+'\r')
    if upload_program(experimentVO['user_id'], experimentVO['exp_id'], exp_type, device_id) == False:
        programUploadVO['fail'] = 1
        return programUploadVO
    programUploadVO['fail'] = 0
    programUploadVO['app_name'] = experimentVO['user_id']+'_'+experimentVO['exp_id']
    ssh_dict[session_id] = channel
    transport_dict[session_id] = transport
    return programUploadVO

def deviceRequest(session_id, device_type, device_id):
    deviceVO = {}
    device_type = int(device_type)
    if device_type == 0:
        device_id = int(device_id)
        if not session_id in ssh_dict.keys() or not device_id in var.getDeviceIDList():
            deviceVO['fail'] = 0
            return deviceVO
        if session_id in transport_dict.keys():
            transport_dict[session_id].close()
            del(transport_dict[session_id])
            print(str(session_id)+'已经被释放')
        if session_id in ssh_dict.keys():
            if ssh_dict[session_id] != {}:
                ssh_dict[session_id].close()
            del(ssh_dict[session_id])
        if device_id in device_dict.keys():
            device_dict[device_id] -= 1
        if session_id in session_id2device.keys():
            del(session_id2device[session_id])
        if session_id in session_life.keys():
            del(session_life[session_id])
        deviceVO['fail'] = 0
        return deviceVO
    if len(device_dict) > 0 and len(device_dict)>=len(var.getDeviceIDList()) and device_dict[min(device_dict, key=device_dict.get)] > 0:
        deviceVO['fail'] = 1
        print('板子全都在使用中')
        return deviceVO
    if session_id in ssh_dict.keys():
        print('已经分配了板子')
        deviceVO['fail'] = 1
        return deviceVO
    device_list = var.getDeviceIDList()
    basicPath = var.basicPath()
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    if red.exists(session_id) == False:
        deviceVO['fail'] = 1
        return deviceVO
    experimentVO = red.get(session_id)
    experimentVO = pickle.loads(experimentVO)
    ssh_uuid = 'ssh_'+str(uuid.uuid1())
    ssh_dict[session_id] = {}
    # print(ret)
    # channel.send(cmd_cd)
    deviceVO['fail'] = 0
    # deviceVO['ssh_uuid'] = ssh_uuid
    session_life[session_id] = datetime.now()
    print(str(session_id)+'已经被请求')
    for m in device_list:
        if not m in device_dict.keys():
            device_dict[m] = 1
            deviceVO['device_id'] = m
            deviceVO['total_count'] = 1
            session_id2device[session_id] = m
            return deviceVO
    tmp = min(device_dict, key=device_dict.get)
    session_id2device[session_id] = tmp
    device_dict[tmp] += 1
    deviceVO['device_id'] = tmp
    deviceVO['total_count'] = device_dict[tmp]
    deviceVO['ip'] = var.device2ip(tmp)
    return deviceVO

def consoleSend(session_id, cmd):
    consoleVO = {}
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    red = redis.StrictRedis(connection_pool=pool)
    if red.exists(session_id) == False:
        consoleVO['fail'] = 1
        return consoleVO
    experimentVO = red.get(session_id)
    experimentVO = pickle.loads(experimentVO)
    if not session_id in ssh_dict.keys():
        consoleVO['fail'] = 99
        return consoleVO
    elif ssh_dict[session_id] == {}:
        consoleVO['fail'] = 99
        return consoleVO
        # if not session_id in session_id2device.keys():
        #     consoleVO['fail'] = 99
        #     return consoleVO
        # device_id = session_id2device[session_id]
        # ip = var.device2ip(device_id)
        # transport = paramiko.Transport((ip, 22))  # 建立一个加密的管道
        # transport.start_client()
        # # 用户名密码方式
        # transport.auth_password("root", "root")
        # # 打开一个通道
        # channel = transport.open_session()
        # channel.settimeout(7200)
        # # 获取一个终端
        # channel.get_pty()
        # # 激活器
        # channel.invoke_shell()
        # cmd_cd = 'cd '+ os.path.join('/home/experiment',experimentVO['user_id'])
        # channel.send(cmd_cd+'\r')
        # ssh_dict[session_id] = channel
    ssh = ssh_dict[session_id]
    if 'cd' in cmd:
        result = cmd +'\r\n' + '命令不能使用' + '\r\n'
        consoleVO['res'] = result
        consoleVO['fail'] = 0
        return consoleVO
    session_life[session_id] = datetime.now()
    cmd += '\r'
    ssh.send(cmd)
    buff = ""
    p = re.compile(r']#')
    result = ''
    res = ssh.recv(65535).decode('utf8')
    result += res
    device_id = session_id2device[session_id]
    if 'reboot' in cmd:
        if session_id in transport_dict.keys():
            transport_dict[session_id].close()
            del(transport_dict[session_id])
            print(str(device_id)+'已经被释放')
        if session_id in ssh_dict.keys():
            if ssh_dict[session_id] != {}:
                ssh_dict[session_id].close()
            del(ssh_dict[session_id])
    if result:
        sys.stdout.write(result.strip('\n'))
    # if res.endswith('# ') or res.endswith('$ '):
    #     break
    # while True:
    #     time.sleep(0.5)
    #     res = ssh.recv(65535).decode('utf8')
    #     result += res
    #     if result:
    #         sys.stdout.write(result.strip('\n'))
    #     if res.endswith('# ') or res.endswith('$ '):
    #         break
    consoleVO['res'] = result
    consoleVO['fail'] = 0
    return consoleVO
    # while True:
    # time.sleep(0.2)
    # ret = ssh.recv(65535)
    # try:
    #     ret = ret.decode('utf-8')
    #     buff += ret
    #     consoleVO['res'] = buff
    # except Exception as e:
    #     consoleVO['res'] = ''
    # print(ret)
    # consoleVO['fail'] = 0
    # return consoleVO

board_res = {}

def byte2str(input):
    res = ''
    for i in range(8):
        res = str(input%2)+res
        input = input//2
    return res

def runResultTick(device_id):
    ip = var.device2ip(device_id)
    res = {}
    if not ip in board_res.keys():
        res['fail'] = 1
        return res
    res['fail'] = 0
    effect = board_res[ip]
    new_effect = []
    for i in range(len(effect)):
        if i==0:
            new_effect.append(chr(effect[i]))
        elif i<8:
            new_effect[0] += chr(effect[i])
        else:
            new_effect.append(byte2str(effect[i]))
        # effect[i] = str(effect[i])
    res['effect'] = new_effect
    return res


def listen_board(board_ip):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    ip = var.serverIP()
    port =  var.ip2port(board_ip)
    s.bind((ip, port))
    while True:
        data=s.recv(1024)  #一次接收1024字节
        effect2 = []
        for i in range(len(data)):
            effect2.append(data[i])
        board_res[board_ip] = effect2
        # time.sleep(20)

session_life = {}

def clear_var():
    while True:
        now_time = datetime.now()
        clear_list = []
        for m in session_life:
            durn = (now_time-session_life[m]).seconds
            if durn >= 360:
                clear_list.append(m)
        for m in clear_list:
            if m in session_id2device.keys():
                device_id = session_id2device[m]
                del session_id2device[m]
                if device_dict[device_id] >= 1:
                    device_dict[device_id] -= 1
            if m in transport_dict.keys():
                transport_dict[m].close()
                del transport_dict[m]
                print(str(m)+'已经被释放')
            if m in session_life.keys():
                del session_life[m]
            if m in ssh_dict.keys():
                if ssh_dict[m] != {}:
                    ssh_dict[m].close()
                del ssh_dict[m]
        time.sleep(6)



if __name__ == '__main__':
    listen_board('1')

    