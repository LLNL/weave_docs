SHELL := /bin/bash

#
# for command line testing, set the following:
# ZONE, SOURCE_ZONE, CI_COMMIT_BRANCH
## TEMPORARY
#ZONE = CZ
#SOURCE_ZONE = CZ
#CI_COMMIT_BRANCH = develop

#GITLAB_USER_EMAIL = muryanto1@llnl.gov
#GITLAB_USER_NAME = weaveci
#CI_COMMIT_BRANCH = develop
#CI_PROJECT_PATH = weave/new_weave_docs

UMASK = umask 027
ZONE := $(shell nodeattr -v center)
DOCS_GROUP = llnl_emp

CZ_GITLAB = ssh://git@czgitlab.llnl.gov:7999
RZ_GITLAB = ssh://git@rzgitlab.llnl.gov:7999
SCF_GITLAB = ssh://git@scfgitlab.llnl.gov:7999

ifeq ($(ZONE),scf)
	GITLAB_URL = $(SCF_GITLAB)
else ifeq ($(ZONE),rz)
	GITLAB_URL = $(RZ_GITLAB)
else
	GITLAB_URL = $(CZ_GITLAB)
endif

WEAVE_CI_URL = $(GITLAB_URL)/weave/weave_ci.git

ifdef CI_COMMIT_TAG
	tools_dir = $(CI_COMMIT_TAG)
else
	tools_dir = $(CI_COMMIT_BRANCH)
endif
tools_dir = develop

WORKSPACE = /usr/workspace/weaveci/weave
WORKDIR = $(WORKSPACE)/workdir
SPACK_VERSION = 0.22.1
SPACK_CORE_ENV_DIR = $(WORKSPACE)/repos/spack_core_environment/$(SPACK_VERSION)/spack_core_environment
MACHINE = $(LCSCHEDCLUSTER)
PYTHON = python3

SPACK_CORE_MACHINE_DIR = $(SPACK_CORE_ENV_DIR)/$(SPACK_VERSION)/$(MACHINE)
REPOS_DIR = $(SPACK_CORE_MACHINE_DIR)/weave_tools/$(tools_dir)

TARGET = develop
#BUILD_DOCS_DIR = /usr/workspace/weave/gitlab/weave_docs

WEAVE_WWW_DIR = /usr/global/web-pages/lc/www/weave

ifeq ($(CI_COMMIT_BRANCH),$(filter $(CI_COMMIT_BRANCH),develop CZ_develop RZ_develop SCF_develop))
	DOCS_DIR = $(WEAVE_WWW_DIR)
else
	DOCS_DIR = $(WEAVE_WWW_DIR)/dev/$(CI_COMMIT_BRANCH)
endif

#
# for creating venv
#
CREATE_VENV_SCRIPT = /usr/apps/weave/tools/create_venv.sh
VENV = $(WORKDIR)/weave_docs_venv
PKGS = sphinx_immaterial termynal

BUILD_DOCS = utils/build_docs.py
VARS_JSON = --vars_json weave_ci/weave_tools/vars.json

PLATFORM := $(shell echo $(SYS_TYPE) | cut -b 1-6)
PLATFORM_OPT = --platform $(PLATFORM)
ZONE_OPT = --zone $(ZONE)
WORKDIR_OPT = --workdir $(REPOS_DIR)

BUILD_DOCS_DIR_OPT = --build_docs_dir `pwd`/build_docs_dir
SCRIPTS_OPT = $(VARS_JSON) $(WORKDIR_OPT) $(ZONE_OPT) $(PLATFORM_OPT)

LLNL_DOCS_MDS= tools.md environment.md badging.md

VENVS_VERSIONS_ROOT_PATH = $(WORKSPACE)/for_docs/venvs_versions

UPDATE_MKDOCS = ./utils/update_mkdocs_yml.sh -f mkdocs.yml

