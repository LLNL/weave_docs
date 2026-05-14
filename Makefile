include vars.mk

define do_build_docs
	# arg1: repo_name
	$(PYTHON) $(BUILD_DOCS) $(SCRIPTS_OPT) $(BUILD_DOCS_DIR_OPT) --venv $(VENV) --tool_json $(WORKDIR)/weave_ci/weave_tools/$1.json
endef

#
# do_build_weave_docs
#   read the version tag from version.txt
#   fetch remove gh-pages
#   creates or updates (if exists) a local gh-pages branch from origin/gh-pages
#   in activated venv, do:
#      mike deploy _version_tag_ --push -> this publishes docs for the specified version
#      run utils/get_latest_mike_version.py -> determine the latest version
#      if latest version exists, updates latest alias with 'mike alias ...'
#
#   Add a git worktree for the gh-pages branch into a temporary directory.
#   Copy content of gh-pages using rsync into destination path
#     in the destination, finds top-level symlink and replaces directory symlinks
#     with real copied directories.
# 

define do_build_weave_docs
	# arg1: destination path for built docs
	@echo "destination path for weave docs: $(1)"
	mkdir -p "$(1)"
	tag=$$(tr -d '\r\n' < ./version.txt); \
	echo "Using tag: $$tag"; \
	git fetch origin gh-pages || true; \
	if git show-ref --verify --quiet refs/remotes/origin/gh-pages; then \
		git branch -f gh-pages origin/gh-pages || true; \
	fi; \
	. "$(VENV)/bin/activate"; \
	echo "Deploying version $$tag"; \
	mike deploy "$$tag" --push; \
	latest_tag=$$(python3 utils/get_latest_mike_version.py); \
	if [ -n "$$latest_tag" ]; then \
		echo "Setting latest -> $$latest_tag"; \
		mike alias --update-aliases --push "$$latest_tag" latest; \
	else \
		echo "No valid version found for latest alias"; \
	fi; \
	deactivate; \
	TMPDIR=$$(mktemp -d); \
	trap 'git worktree remove --force "$$TMPDIR" 2>/dev/null || true; rm -rf "$$TMPDIR"' EXIT; \
	echo "Using temp dir: $$TMPDIR"; \
	git worktree add --force "$$TMPDIR" gh-pages; \
	rsync -a --delete --exclude '.git' "$$TMPDIR"/ "$(1)"/; \
	( cd "$(1)" && \
	  find . -maxdepth 1 -type l -print0 | \
	  while IFS= read -r -d '' L; do \
	    NAME=$${L#./}; \
	    TGT=$$(readlink "$$NAME" || true); \
	    case "$$TGT" in \
	      /*|*..* ) echo "WARN...skipping unsafe symlink $$NAME -> $$TGT"; continue ;; \
	    esac; \
	    if [ -d "$$TGT" ]; then \
	      echo "INFO...dereferencing alias $$NAME -> $$TGT for static hosting"; \
	      rm -f "$$NAME"; \
	      cp -a "$$TGT" "$$NAME"; \
	    fi; \
	  done \
	); \
	git worktree remove --force "$$TMPDIR"; \
	rm -rf "$$TMPDIR"
endef

define patch_mds
	sed -i 's|https://maestrowf.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/maestrowf/html/index.html|g' docs/tools.md
	sed -i 's|https://merlin.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/merlin/html/index.html|g' docs/tools.md
	sed -i 's|https://kosh.readthedocs.io/en/latest|https://lc.llnl.gov/weave/kosh/html/index.html|g' docs/tools.md
	sed -i 's|https://pydv.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/pydv/html/index.html|g' docs/tools.md
	sed -i 's|https://llnl-ibis.readthedocs.io/en/latest|https://lc.llnl.gov/weave/ibis/html/index.html|g' docs/tools.md
	sed -i 's|https://llnl-trata.readthedocs.io/en/latest|https://lc.llnl.gov/weave/trata/html/index.html|g' docs/tools.md
	sed -i 's;<!-- SINA DOCUMENTATION HERE -->;| [Documentation](https://lc.llnl.gov/weave/Sina/html/index.html);g' docs/tools.md
	sed -i 's;<!-- PYDV GETTING STARTED HERE -->;| [Quick Start Guide](https://pydv.readthedocs.io/en/latest/getting_started.html);g' docs/tools.md
	if [ $(SOURCE_ZONE) == RZ ]; then \
		cd docs; \
		find . -type f -name '*.md' | xargs  sed -i 's|https://lc.llnl.gov|https://rzlc.llnl.gov|g'; \
		cd ..; \
	fi
endef

#
# copy the WEAVE venv's pip list output that were populated by weave/weave_ci's CI
#
define copy_mds
	mkdir -p docs/llnl
	cp -r $(VENVS_VERSIONS_ROOT_PATH) docs/llnl/
endef

define merge_branch_1_to_branch_2
	echo "### merge $1 to $2 ###"; \
	git status; \
	cat mkdocs.yml; \
	git config --global user.email "${GITLAB_USER_EMAIL}"; \
	git config --global user.name "${GITLAB_USER_NAME}"; \
	git fetch --all; \
	git checkout $2; \
	git pull origin $2; \
	git merge $1 -m "merge $1 into $2 develop [ci skip]" --no-ff --allow-unrelated-histories; \
	echo "#### after merging $1 to $2"; \
	cat mkdocs.yml; \
	git remote rm origin; \
	git remote add origin $(GITLAB_URL)/$(CI_PROJECT_PATH).git; \
	if [ "$3" == "push" ]; then \
		git push origin HEAD:$2; \
	fi
endef

define patch_files_and_build_docs
	$(call copy_mds)
	$(call patch_mds)
	$(call patch_mkdocs_yml)
	git status
	cat mkdocs.yml
endef

define patch_mkdocs_yml
	$(UPDATE_MKDOCS)
endef

define deploy_docs_for
	# arg1: tool name
	# Mike may have previously published alias dirs (e.g. latest/) as symlinks, which many
	# static hosts won't serve and which `cp -r` can't overwrite with a real directory.
	mkdir -p $(DOCS_DIR)/$(1)
	if [ -e $(DOCS_DIR)/$(1)/latest ] && [ ! -d $(DOCS_DIR)/$(1)/latest ]; then rm -f $(DOCS_DIR)/$(1)/latest; fi
	rsync -a --delete build_docs_dir/$(1)/ $(DOCS_DIR)/$(1)/
	if [ "$(1)" == "weave" ]; then \
		cp index.html $(DOCS_DIR)/index.html; \
	fi
endef

print_env:
	echo "WORKSPACE: $(WORKSPACE)"
	echo "WORKDIR: $(WORKDIR)"
	echo "VENV: $(VENV)"

.PHONY: setup
.ONESHELL:
setup: print_env
	mkdir -p build_docs_dir
	mkdir -p $(WORKDIR)
	cd $(WORKDIR)
	rm -rf weave_ci
	git clone -b develop $(WEAVE_CI_URL)
	rm -rf $(VENV)
	$(CREATE_VENV_SCRIPT) -v latest-develop -e $(VENV)
	source $(VENV)/bin/activate && pip install $(PKGS) && pip list && deactivate

build_ibis_docs:
	$(call do_build_docs,ibis)

build_kosh_docs:
	$(call do_build_docs,kosh)

build_maestrowf_docs:
	$(call do_build_docs,maestrowf)

build_merlin_docs:
	$(call do_build_docs,merlin)

build_pydv_docs:
	$(call do_build_docs,pydv)

build_sina_docs:
	$(call do_build_docs,Sina)

build_trata_docs:
	$(call do_build_docs,trata)

build_studyweaver_docs:
	$(call do_build_docs,StudyWeaver)

build_docs:
	$(call patch_files_and_build_docs)
	$(call do_build_weave_docs,$(CURDIR)/build_docs_dir/weave)

merge_for_push_to_CZ_develop_feature:
	$(call merge_branch_1_to_branch_2,origin/develop,CZ_develop,push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	echo "### git pull origin CZ_develop ###"
	git pull origin CZ_develop
	git status

merge_for_push_to_CZ_develop:
	$(call merge_branch_1_to_branch_2,origin/develop,CZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,develop,no_push)

merge_for_push_to_develop_feature_cz:
	$(call merge_branch_1_to_branch_2,origin/develop,CZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,develop,no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin CZ_develop
	git status

merge_for_push_to_develop_cz:
	$(call merge_branch_1_to_branch_2,origin/develop,CZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,develop,no_push)

#
# RZ
#
merge_for_push_to_RZ_develop_feature:
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,RZ_develop,push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin RZ_develop
	git status

merge_for_push_to_RZ_develop:
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,develop,no_push)

merge_for_push_to_develop_feature_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,develop,no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin RZ_develop
	git status

merge_for_push_to_develop_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,RZ_develop,push)
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,develop,no_push)

#
# SCF
#
merge_for_push_to_SCF_develop_feature:
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,SCF_develop,push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin SCF_develop
	git status

merge_for_push_to_SCF_develop:
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/SCF_develop,develop,no_push)

merge_for_push_to_develop_feature_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/SCF_develop,develop,no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin SCF_develop
	git status

merge_for_push_to_develop_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/develop,SCF_develop,push)
	$(call merge_branch_1_to_branch_2,origin/SCF_develop,develop,no_push)


deploy_docs:
	mkdir -p $(DOCS_DIR)
	cp -pr build_docs_dir/maestrowf $(DOCS_DIR)
	cp -pr build_docs_dir/pydv $(DOCS_DIR)
	cp -pr build_docs_dir/Sina $(DOCS_DIR)
	cp -pr build_docs_dir/kosh $(DOCS_DIR)
	cp -pr build_docs_dir/trata $(DOCS_DIR)
	cp -pr build_docs_dir/ibis $(DOCS_DIR)
	cp -pr build_docs_dir/merlin $(DOCS_DIR)
	$(call deploy_docs_for,StudyWeaver)
	$(call deploy_docs_for,weave)
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)
#	rm -rf build_docs_dir
