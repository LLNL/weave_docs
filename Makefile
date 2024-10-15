include vars.mk

define build_docs
	# arg1: repo_name
	$(PYTHON) $(BUILD_DOCS) $(SCRIPTS_OPT) $(BUILD_DOCS_DIR_OPT) --venv $(DEPLOY_PATH)/$(latest_symlink) --tool_json weave_ci/weave_tools/$1.json
endef


define patch_mds
	sed -i 's|https://maestrowf.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/maestrowf/html/index.html|g' docs/tools.md
	sed -i 's|https://merlin.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/merlin/html/index.html|g' docs/tools.md
	sed -i 's|https://kosh.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/kosh/html/index.html|g' docs/tools.md
	sed -i 's|https://pydv.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/pydv/html/index.html|g' docs/tools.md
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
	echo "### merge $1 to $2 ###"
	git status
	cat mkdocs.yml
	git config --global user.email "${GITLAB_USER_EMAIL}"
	git config --global user.name "${GITLAB_USER_NAME}"
	git fetch --all
	git checkout $2
	git pull origin $2
	git merge $1 -m "merge $1 into $2 develop [ci skip]" --no-ff --allow-unrelated-histories
	echo "#### after merging $1 to $2"
	cat mkdocs.yml
	git remote rm origin
	git remote add origin $(GITLAB_URL)/$(CI_PROJECT_PATH).git; \
	if [ "$3" == "push" ]; then \
		git push origin HEAD:$2; \
	fi
endef

define merge_for_push_to_zone_feature
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git rebase $(SOURCE_ZONE)_$(TARGET)
	git status
endef

define merge_for_push_to_zone
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
endef

define merge_for_push_to_target_feature
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git rebase $(TARGET)
	git status
endef


define merge_for_push_to_target_branch
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
endef

define patch_files_and_build_docs
	$(call copy_mds)
	$(call patch_mds)
	$(call patch_mkdocs_yml)
	git status
	cat mkdocs.yml
	source $(DEPLOY_PATH)/$(latest_symlink)/bin/activate && \
	mkdocs build && \
	mkdir -p $(BUILD_DOCS_DIR)/weave && \
	ls weave && cp -r weave $(BUILD_DOCS_DIR)/
endef

define patch_mkdocs_yml
	$(UPDATE_MKDOCS)
endef

pull_weave_docs_tutorials_PREV:
	$(call pull_weave_docs_tutorials)

setup:
	pwd
	git clone -b develop $(WEAVE_CI_URL)
	ls -l weave_ci

build_ibis_docs:
	$(call build_docs,ibis)

build_kosh_docs:
	$(call build_docs,kosh)

build_maestrowf_docs:
	$(call build_docs,maestrowf)

build_merlin_docs:
	$(call build_docs,merlin)

build_pydv_docs:
	$(call build_docs,pydv)

build_sina_docs:
	$(call build_docs,Sina)

build_trata_docs:
	$(call build_docs,trata)

build_weave_docs_PREV:
	$(call pull_weave_docs_tutorials)
	$(call copy_mds)
	$(call patch_mds)
	$(call patch_mkdocs_yml)
	cat mkdocs.yml
	source $(DEPLOY_PATH)/$(latest_symlink)/bin/activate && \
	mkdocs build && \
	mkdir -p $(BUILD_DOCS_DIR)/weave && \
	ls weave && cp -r weave $(BUILD_DOCS_DIR)/

build_weave_docs_for_push_to_zone_feature:
	$(call merge_for_push_to_zone_feature)
	$(call patch_files_and_build_docs)

build_weave_docs_for_push_to_zone:
	$(call merge_for_push_to_zone)
	$(call patch_files_and_build_docs)

build_weave_docs_for_push_to_target_feature:
	$(call merge_for_push_to_target_feature)
	$(call patch_files_and_build_docs)

build_weave_docs_for_push_to_target:
	$(call merge_for_push_to_target_branch)
	$(call patch_files_and_build_docs)

deploy_docs:
	cp -pr $(BUILD_DOCS_DIR)/Sina $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/maestrowf $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/pydv $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/kosh $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/merlin $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/trata $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/ibis $(DOCS_DIR)
	cp -pr $(BUILD_DOCS_DIR)/weave/* $(DOCS_DIR)
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)
