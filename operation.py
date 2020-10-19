import os
from shutil import copyfile
import var
from pexpect import *


def makeGeneralProject(toolChainPath, basicPath, proPath, projectname, exp_type):
    if os.path.exists(proPath):
        return True
    #make basic dir
    os.makedirs(proPath)
    os.makedirs(os.path.join(proPath, 'src'))
    os.makedirs(os.path.join(proPath, 'include'))
    os.makedirs(os.path.join(proPath, 'env'))
    #build_env_app
    try:
        #复制第一层makefile
        source_makefile = os.path.join(basicPath, 'var/begin/Makefile')
        target_makefile = os.path.join(proPath, 'env/Makefile')
        copyfile(source_makefile, target_makefile)
        #复制第二层makefile
        if exp_type=='1':
            source_makfile2 = os.path.join(basicPath, 'var/Makefile')
        elif exp_type=='2':
            source_makfile2 = os.path.join(basicPath, 'var/Makefile_kernel')
            # source_makfile2 = '/home/chu-jiao/test/zlg72902/Makefile'
        else:
            return False
        target_makefile2 = os.path.join(proPath,'src/Makefile')
        copyfile(source_makfile2, target_makefile2)
        #写入configmk
        f = open(os.path.join(proPath, 'env/config.mk'), 'w')
        f.write("TOOL_CHAIN_PATH")
        f.write("=")
        f.write(toolChainPath)
        f.write("\n")
        f.write("Projectname")
        f.write("=")
        f.write(projectname)
        f.write("\n")
        f.write("KERNELDIR=/home/fzk/linux-3.14.52")
        f.close()
    except IOError as e:
        print("make generalproject failed: %s" % e)
        return False
    #make_shell_compile
    if os.path.exists(os.path.join(proPath, 'env/shell_compile.bat')):
        print('shell_compile已经存在')
        return True
    try:
        f = open(os.path.join(proPath, 'env/shell_compile.bat'),'w')
        # f.write("source /home/fzk/my-imx6/03_tools/gcc-linaro-arm-linux-gnueabihf-492-env\n")
        f.write("cd "+os.path.join(proPath, 'env')+"\n")
        f.write("make 2>&1\n")
        f.close()
        return True
    except IOError as e:
        print("make generalproject failed: %s" % e)
        return False
    
def upload_program(user_id, exp_id, exp_type, device_id):
    basicPath = var.basicPath()
    if exp_type == '1':
        programPath = os.path.join(basicPath, 'workdir', user_id, exp_id, 'src', user_id+'_'+exp_id)
        uploadPath = os.path.join('/home', 'experiment', user_id)
    elif exp_type == '2':
        # programPath = os.path.join(basicPath, 'workdir', user_id, exp_id, 'src', user_id+'_'+exp_id+'.ko')
        programPath = os.path.join(basicPath, 'workdir', user_id, exp_id, 'src', 'myzr_zlg7290.ko')
        uploadPath = os.path.join('/home', 'experiment', user_id)
    ip = var.device2ip(device_id)
    cmd = "scp " + programPath + " root@" + ip + ":"+uploadPath
    # os.system(cmd)
    # os.system("root\r")
    child = spawn(cmd)
    child.expect ("password")
    child.sendline ("root")
    child.read()
    return True
    # try:
    #     copyfile(programPath, uploadPath)
    #     return True
    # except IOError as e:
    #     print("make generalproject failed: %s" % e)
    #     return False

def run_program(user_id, exp_id):
    basicPath = var.basicPath
    programPath = os.path.join(basicPath, 'board', user_id+'_'+exp_id)
    res_run = os.popen('./ '+programPath)
    run_result = ''
    for m in res_run.readlines():
        run_result += m
    return run_result
    
