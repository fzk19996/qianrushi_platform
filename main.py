from flask import Flask
from flask import jsonify
from flask import request
import json
import boardServiceImpl
import var
import _thread

app = Flask(__name__)

@app.route('/EnvironmentRequest', methods=['post'])
def environmentRequest():
    data = request.form
    user_id = data['user_id']
    exp_id = data['exp_id']
    exp_type = data['exp_type']
    return boardServiceImpl.environmentRequest(user_id, exp_id, exp_type)

@app.route('/CodeSubmit', methods=['post'])
def codeSubmit():
    data = request.form
    session_id = data['session_id']
    code = data['code']
    code_name = data['code_name']
    return boardServiceImpl.codeSubmit(session_id, code, code_name)

@app.route('/compile', methods=['post'])
def compile():
    data = request.form
    session_id = data['session_id']
    return boardServiceImpl.compile(session_id)

@app.route('/DeviceRequest', methods=['post'])
def deviceRequest():
    data = request.form
    session_id = data['session_id']
    device_type = data['device_type']
    device_id = data['device_id']
    return boardServiceImpl.deviceRequest(session_id, device_type, device_id)

@app.route('/ProgramUpload', methods=['post'])
def programUpload():
    data = request.form
    session_id = data['session_id']
    device_id = data['device_id']
    exp_type = data['exp_type']
    return boardServiceImpl.programUpload(session_id, device_id, exp_type)

@app.route('/ConsoleSend', methods=['post'])
def consoleSend(): 
    data = request.form
    ssh_uuid = data['session_id']
    cmd = data['cmd']
    return boardServiceImpl.consoleSend(ssh_uuid, cmd)

@app.route('/runResultTick', methods=['post'])
def runResultTick():
    data = request.form
    device_id = data['device_id']
    return boardServiceImpl.runResultTick(device_id)


def init_server():
    ip_list = var.ip_list()
    _thread.start_new_thread(boardServiceImpl.clear_var, ())
    for ip in ip_list:
        _thread.start_new_thread(boardServiceImpl.listen_board, (ip,))


if __name__ == '__main__':
    init_server()
    app.run(host='0.0.0.0', port= 8001)

