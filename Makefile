include vars.mk

define do_build_docs
	# arg1: repo_name
	$(PYTHON) $(BUILD_DOCS) $(SCRIPTS_OPT) $(BUILD_DOCS_DIR_OPT) --venv $(VENV) --tool_json weave_ci/weave_tools/$1.json
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
		cd ../..; \
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
	source $(VENV)/bin/activate && \
	mkdocs build && \
	mkdir -p build_docs_dir/weave && \
	ls weave && cp -r weave build_docs_dir/
endef

define patch_mkdocs_yml
	$(UPDATE_MKDOCS)
endef

print_env:
	echo "WORKSPACE: $(WORKSPACE)"
	echo "WORKDIR: $(WORKDIR)"
	echo "VENV: $(VENV)"

setup: print_env
	mkdir -p build_docs_dir
	mkdir -p $(WORKDIR)
	cd $(WORKDIR)
	rm -rf weave_ci
	git clone -b develop $(WEAVE_CI_URL)
	ls -l weave_ci
	rm -rf $(VENV)
	$(CREATE_VENV_SCRIPT) -v latest-stable -e $(VENV)
	source $(VENV)/bin/activate && pip install $(PKGS) && cd plugins/mkdocs_version_diff && pip install . && pip list && deactivate

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
	mkdir -p $(DOCS_DIR)/StudyWeaver
	# Mike may have previously published alias dirs (e.g. latest/) as symlinks, which many
	# static hosts won't serve and which `cp -r` can't overwrite with a real directory.
	if [ -e $(DOCS_DIR)/StudyWeaver/latest ] && [ ! -d $(DOCS_DIR)/StudyWeaver/latest ]; then rm -f $(DOCS_DIR)/StudyWeaver/latest; fi
	rsync -a --delete build_docs_dir/StudyWeaver/ $(DOCS_DIR)/StudyWeaver/
	cp -pr build_docs_dir/merlin $(DOCS_DIR)
	cp -pr build_docs_dir/weave/* $(DOCS_DIR)
	rm -rf build_docs_dir
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)

deploy_docs_cz:
	mkdir -p $(DOCS_DIR)
	cp -pr build_docs_dir/maestrowf $(DOCS_DIR)
	cp -pr build_docs_dir/pydv $(DOCS_DIR)
	cp -pr build_docs_dir/Sina $(DOCS_DIR)
	cp -pr build_docs_dir/kosh $(DOCS_DIR)
	cp -pr build_docs_dir/trata $(DOCS_DIR)
	cp -pr build_docs_dir/ibis $(DOCS_DIR)
	cp -pr build_docs_dir/merlin $(DOCS_DIR)
	cp -pr build_docs_dir/weave/* $(DOCS_DIR)
	rm -rf build_docs_dir
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)
