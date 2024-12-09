import re
import os
import subprocess
import shlex

SUCCESS = 0
FAILURE = 1

def get_python_version(venv):

    cmd = "python --version"
    ret, cmd_output = run_cmd_in_venv(cmd, venv)

    m = re.match(r'Python\s+(\d+.\d+).\d+$', cmd_output[0])
    if m:
        python_version = "python{}".format(m.group(1))

    else:
        python_version = None

    return python_version

def run_command(cmd, join_stderr=True, shell_cmd=False, verbose=True, cwd=None, env=None):

    print("CMD: {c}".format(c=cmd))
    save_cwd  = None
    if isinstance(cmd, str) and not shell_cmd:
        cmd = shlex.split(cmd)

    if join_stderr:
        stderr_setting = subprocess.STDOUT
    else:
        stderr_setting = subprocess.PIPE

    if cwd is None:
        current_wd = os.getcwd()
    else:
        save_wd = os.getcwd()
        current_wd = cwd
        # print("INFO...chdir to {}".format(current_wd))
        os.chdir(current_wd)

    new_env = os.environ.copy()

    if env is not None:
        new_env.update(env)

    P = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr_setting,
                         cwd=current_wd, shell=shell_cmd)

    output =  P.communicate()[0]
    #print("STDOUT: {}".format(output))

    decoded_str = output.decode('utf-8')

    out = []
    if decoded_str:
        for l in decoded_str.split('\n'):
            out.append(l.rstrip())
        
    ret_code = P.returncode
    if verbose:
        for l in out:
            print(l)
    if cwd:
        # print("INFO....chdir to {}".format(save_wd))
        os.chdir(save_wd)

    return(ret_code, out)

def run_cmd(cmd, join_stderr=True, shell_cmd=False, verbose=True, cwd=None, env=None):

    ret_code, output = run_command(cmd, join_stderr, shell_cmd, verbose, cwd, env)
    return(ret_code)


def run_cmds(cmds, join_stderr=True, shell_cmd=False, verbose=True, cwd=None, env=None):

    for cmd in cmds:
        ret_code, output = run_command(cmd, join_stderr, shell_cmd, verbose, cwd, env)
        if ret_code != SUCCESS:
            return ret_code
    return ret_code


def run_cmd_capture_output(cmd, join_stderr=True, shell_cmd=False, verbose=True, cwd=None, env=None):

    ret_code, output = run_command(cmd, join_stderr, shell_cmd, verbose, cwd, env)
    return(ret_code, output)


def run_cmd_in_venv(cmd, venv, cwd=None):
    """
    run cmd under cwd directory in the specified venv.
    Parameters:
      cmd : command to be executed
      cwd : working directory
      venv: virtual environment

    Return value:
      ret: 0 for SUCCESS, 1 for FAILURE
      cmd_output: a list of command output lines.
    """
    
    activate_cmd = "source {}/bin/activate".format(venv)
    if cwd:
        the_cmd = "{} && cd {} && {} && deactivate".format(activate_cmd,
                                                           cwd,
                                                           cmd)
    else:
        the_cmd = "{} && {} && deactivate".format(activate_cmd,
                                                  cmd)
    ret, cmd_output = run_cmd_capture_output(the_cmd, shell_cmd=True,
                                             verbose=True, cwd=cwd) 
    return ret, cmd_output


def run_cmds_for_badged_tools(repo_dir, local_install_dir, commands,
                              venv, add_path=True):
    """
    run commands listed in <commands> list in the specified virtual environment
      to install badged tool, or to run the badged tool tests.
 
    Parameters:
      commands: a list of commands to run.
                Some commands may be 'cd some_dir && do_something'
                'some_dir' will be run relative to the passed in repo_dir.
      repo_dir: project repository top directory
      local_install_dir: if specified, then the 'pip install' command will be
                         run with '--prefix <local_install_dir>' argument.
    """

    python_version = get_python_version(venv)
    if not python_version:
        return FAILURE
    
    add_path_str = add_python_path_str = ""
    if local_install_dir and add_path:
        add_path_str = "export PATH={}/bin:$PATH".format(local_install_dir)
        add_python_path_str = "export PYTHONPATH={}/lib/{}/site-packages:$PYTHONPATH".format(local_install_dir,
                                                                                             python_version)
        print("INFO...add_path_str: {}".format(add_path_str))
        print("INFO...add_python_path_str: {}".format(add_python_path_str))
    else:
        print("INFO INFO INFO...local_install_dir is None")
    
    for c in commands:
        cwd = None
        # print("c: {}".format(c))
    
        m = re.match(r'^cd\s+(\S+)\s+&&\s+(.+)$', c)
        if m:
            the_cmd = m.group(2)
            cwd = os.path.join(repo_dir, m.group(1))
        else:
            the_cmd = c
            cwd = repo_dir

        m = re.match(r'^pip\s+install\s+', the_cmd)
        if m:
            if local_install_dir and add_path:
                prefix = "--prefix {}".format(local_install_dir)
                cmd = "{} && {} && umask 027 && {} {}".format(add_path_str,
                                                              add_python_path_str,
                                                              the_cmd,
                                                              prefix)
            else:
                cmd = "{}".format(the_cmd)
                
        else:
            if local_install_dir and add_path:
                cmd = "{} && {} && umask 027 && {}".format(add_path_str,
                                                           add_python_path_str,
                                                           the_cmd)
            else:
                cmd = "{}".format(the_cmd)
 
        ret, cmd_output = run_cmd_in_venv(cmd, venv, cwd=cwd)
        if ret != SUCCESS:
            break

    return ret

def do_run_cmds_in_venv(repo_dir, commands, venv):

    for cmd in commands:
        cwd = None

        m = re.match(r'^cd\s+(\S+)\s+&&\s+(.+)$', cmd)
        if m:
            the_cmd = m.group(2)
            cwd = os.path.join(repo_dir, m.group(1))
        else:
            the_cmd = cmd
            cwd = repo_dir

        ret, cmd_output = run_cmd_in_venv(the_cmd, venv, cwd=cwd)
        if ret != SUCCESS:
            break

    return ret

