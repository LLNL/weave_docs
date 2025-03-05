import os
import shutil
import json
import re

from command_utils import SUCCESS, run_cmd, run_cmd_capture_output

def get_json_info(tool_json):
    """
    Reads in a json file into a dictionary
    Parameters:
      tool_json: full path to a json file
    Return value:
      tool_dict: dictionary containing entries from the json file
    """
    
    with open(tool_json, 'r') as f:
        tool_dict = json.load(f)
        for k in tool_dict:
            print("{}: {}".format(k, tool_dict[k]))
            
    return tool_dict

def substitute_vars(cmds_list, vars_dict):
    '''
    cmds_list: list of commands to look for vars in, and replace
               them with values.
    vars_dict: dict for variables
    '''
    i = 0
    new_cmds_list = []
    for s in cmds_list:
        m = re.findall(r'\$\((\S+)\)', s)
        if m:
            print("FOUND: ", m)
            for pattern in m:
                s = s.replace("$({})".format(pattern), vars_dict[pattern])
                print("the new line: {}".format(s))
        new_cmds_list.append(s)
        i = i + 1
        
    return new_cmds_list


def do_clone_repo(tool_dict, workdir, url, branch, tag=None):
    """
    clones the project specified in tool_dict into workdir.
    Parameters:
      workdir  : directory where project will be cloned to.
      tool_dict: dictionary containing info about a project.
      branch   : git branch to clone
      tag      : tag to checkout
    """

    repo_dir = os.path.join(workdir, tool_dict['repo_project'])
    if os.path.exists(repo_dir):
        print("INFO...removing {} directory".format(repo_dir))
        shutil.rmtree(repo_dir)

    cmd = "git clone -b {} {}".format(branch, url)
    ret = run_cmd(cmd, cwd=workdir)
    if ret != SUCCESS:
        return(ret)

    if tag:
        cmd = "git checkout tags/{} -b {}".format(tag, branch)
        ret = run_cmd(cmd, cwd=workdir)
        if ret != SUCCESS:
            return(ret)   
        
    cmd = "git status"
    ret, cmd_output = run_cmd_capture_output(cmd, cwd=repo_dir)

    return ret, repo_dir

def get_platform():
    sys_type_str = os.environ['SYS_TYPE']
    m = re.match(r'^([a-zA-z]+)_(\d+)_\S+', sys_type_str)
    if m:
        platform = "{}_{}".format(m.group(1), m.group(2))
        print("DEBUG DEBUG...platform: {}".format(platform))
    else:
        print("Error...platform is none")
        platform = None
    return platform

#
# REVISIT -- does latest tag always come from 'main' or 'master'?
#

def get_latest_tag(tag, repo_dir):

    if tag == 'latest':
        
        cmd = "git describe --abbrev=0 --tags"
        ret, cmd_output = run_cmd_capture_output(cmd, cwd=repo_dir)

        if ret != SUCCESS:
            return FAILURE
        install_tag = cmd_output[0]
    else:
        install_tag = tag
        
    cmd = "git checkout {}".format(install_tag)
    ret = run_cmd(cmd, cwd=repo_dir)
    if ret != SUCCESS:
        return ret

    cmd = "git pull origin {}".format(install_tag)
    ret = run_cmd(cmd, cwd=repo_dir)

    return ret
    
    

    
