import os
import sys
import argparse
import shutil
import re

this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(this_dir, '..', 'lib'))

from command_utils import SUCCESS, FAILURE
from command_utils import run_cmds, do_run_cmds_in_venv
from utils import get_json_info, do_clone_repo
from utils import substitute_vars

parser = argparse.ArgumentParser(
    description="Run tests for the tool specified in the json file in the virtual environment",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--tool_json',
                    help="full path name of json file that contains" +
                    " info about the tool to install")
parser.add_argument('--vars_json',
                    help="full path name of json file that contains" +
                    " variables that may be used in tool_json ")
parser.add_argument('--venv',
                    default="/usr/apps/weave/weave-develop-cpu",
                    help="Virtual environment to install the tool into")
parser.add_argument('--workdir',
                    help="working directory where the tool repo was cloned to.")
parser.add_argument('--zone', choices=['cz', 'rz', 'scf'], default='cz',
                    help="Zone to install the tool on.")
parser.add_argument('--build_docs_dir',
                    help="Directory to put the generated html directory")


args = parser.parse_args(sys.argv[1:])
tool_json = args.tool_json
vars_json = args.vars_json
venv = args.venv
workdir = args.workdir
zone = args.zone
build_docs_dir = args.build_docs_dir

def add_cp_html_cmd(repo_project, build_docs_dir, cmds_list):

    add_cmd = "mkdir -p {}/{}".format(build_docs_dir, repo_project)
    cmds_list.insert(0, add_cmd)

    for i in range(1,len(cmds_list)):
        cmd = cmds_list[i]
        if 'make html' in cmd:
            if repo_project == 'pydv':
                add_cmd = " && cp -r _build/html {}/{}".format(build_docs_dir,
                                                              repo_project)
            else:
                add_cmd = " && cp -r build/html {}/{}".format(build_docs_dir,
                                                              repo_project)
 
            cmds_list[i] = cmds_list[i] + add_cmd
            break
        elif 'mkdocs build' in cmd:
            orig_cmd = cmd
            orig_str = "mkdocs build"
            new_str = "mkdocs build -d {}/{}".format(build_docs_dir, repo_project)
            new_cmd = orig_cmd.replace(orig_str, new_str)
            cmds_list[i] = new_cmd
            break
        elif 'make docs' in cmd:
            add_cmd = " && cp -r docs/build/html {}/{}".format(build_docs_dir,
                                                               repo_project)
            cmds_list[i] = cmds_list[i] + add_cmd
            break
        elif 'mike deploy' in cmd:
            version_cmd = r"grep '^version *= *\"' pyproject.toml | sed -E 's/^[^\"]*\"([^\"]*)\".*/\1/'"
            # Preserve any additional mike deploy flags (e.g. --branch, --rebase),
            # but always supply the version/aliases and --push ourselves.
            mike_cmd = cmd.strip()
            m = re.match(r'^cd\\s+\\S+\\s+&&\\s+(.+)$', mike_cmd)
            if m:
                mike_cmd = m.group(1).strip()
            mike_opts = ""
            if mike_cmd.startswith("mike deploy"):
                mike_opts = mike_cmd[len("mike deploy"):].strip()
            push_flag = "" if "--push" in mike_opts.split() else " --push"

            export_cmd = (
                "REPO_ROOT=$(git rev-parse --show-toplevel)"
                " && cd \"${REPO_ROOT}\""
                " && (python -c \"import pkgutil; import markdown; raise SystemExit(0 if pkgutil.find_loader('markdown.extensions.toc') else 1)\""
                "     || python -m pip install -U Markdown)"
                " && git fetch origin gh-pages || true"
                " && (git show-ref --verify --quiet refs/remotes/origin/gh-pages"
                "     && git branch -f gh-pages origin/gh-pages || true)"
                f" && VERSION=$({version_cmd})"
                ' && echo "INFO...mike deploy version=${VERSION}"'
                f' && mike deploy {mike_opts}{push_flag} "${{VERSION}}" latest --update-aliases'
                " && TMPDIR=$(mktemp -d)"
                ' && git worktree add --force "${TMPDIR}" gh-pages'
                f" && rsync -a --delete --exclude '.git' \"${{TMPDIR}}\"/ {build_docs_dir}/{repo_project}/"
                f" && (cd {build_docs_dir}/{repo_project}"
                "     && find . -maxdepth 1 -type l -print0"
                "     | while IFS= read -r -d '' L; do"
                "         NAME=${L#./};"
                "         TGT=$(readlink \"$NAME\" || true);"
                "         case \"$TGT\" in"
                "           /*|*..* ) echo \"WARN...skipping unsafe symlink $NAME -> $TGT\"; continue ;;"
                "         esac;"
                "         if [ -d \"$TGT\" ]; then"
                "           echo \"INFO...dereferencing alias $NAME -> $TGT for static hosting\";"
                "           rm -f \"$NAME\";"
                "           cp -a \"$TGT\" \"$NAME\";"
                "         fi;"
                "       done)"
                f" && if [ ! -d {build_docs_dir}/{repo_project}/latest ] && [ -d {build_docs_dir}/{repo_project}/\"${{VERSION}}\" ]; then "
                f"echo \"WARN...{repo_project} missing latest/, copying ${{VERSION}} -> latest/ for static hosting\"; "
                f"cp -a {build_docs_dir}/{repo_project}/\"${{VERSION}}\" {build_docs_dir}/{repo_project}/latest; "
                "fi"
                ' && git worktree remove --force "${TMPDIR}"'
                ' && rm -rf "${TMPDIR}"'
            )
            cmds_list[i] = export_cmd
            break
        
    print("cmds_list: ", cmds_list)
    
    return SUCCESS

#
# main
#

tool_dict = get_json_info(tool_json)
vars_dict = get_json_info(vars_json)

repo_project = tool_dict['repo_project']
repo_dir = os.path.join(workdir, repo_project)

if not os.path.isdir(repo_dir):
    url = tool_dict["{}_clone".format(zone)]
    the_url = substitute_vars([url], vars_dict)[0]

    # REVISIT if we are running a tagged version of the tool.
    status, repo_dir = do_clone_repo(tool_dict, workdir,
                                     the_url,
                                     tool_dict['branch'])


the_key = "{}_build_docs_cmds".format(zone)
if the_key not in tool_dict:
    the_key = 'build_docs_cmds'

if the_key in tool_dict:
    cmds_list = substitute_vars(tool_dict[the_key], vars_dict)
    print("cmds_list (after substitute): {}".format(cmds_list))
else:
    print("ERROR...No build docs commands for {}".format(repo_project))
    sys.exit(1)

status = add_cp_html_cmd(repo_project, build_docs_dir, cmds_list)
if status != SUCCESS:
    sys.exit(status)
    
print("after returned from add_cp_html_cmd() ")
print("cmds_list: ", cmds_list)

if repo_project == "Sina":
    status = run_cmds(cmds_list, shell_cmd=True, cwd="{}/python".format(repo_dir))
else:
    status = do_run_cmds_in_venv(repo_dir, cmds_list, venv)

sys.exit(status)

# example:
# python3 ./utils/build_docs.py  --vars_json weave_tools/vars.json --venv $VENV --workdir `pwd`/workdir --build_docs_dir=`pwd`/build_docs_dir --tool_json weave_tools/merlin.json
