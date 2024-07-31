WEAVE idesign environment
=========================

You can access WEAVE idesign environment on any LC CZ and RZ machines by activating the latest WEAVE idesign environment::

    $ source /usr/gapps/weave/develop/weave_idesign_env/bin/activate
    
At this point, you are ready to use the supported WEAVE tools in the environment.
You can snapshot the WEAVE idesign env to your local directory so that you can install any additional modules that you may need into the enviroment::

    $ /usr/workspace/weave/gitlab/weave_ci/idesign/bin/idsnapshot my_weave_idesign_env
    $ source ./my_weave_idesign_env/bin/activate
