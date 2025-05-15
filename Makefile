include vars.mk

define do_build_docs
	# arg1: repo_name
	$(PYTHON) $(BUILD_DOCS) $(SCRIPTS_OPT) $(BUILD_DOCS_DIR_OPT) --venv $(VENV) --tool_json weave_ci/weave_tools/$1.json
endef


define patch_mds
	sed -i 's|https://maestrowf.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/maestrowf/html/index.html|g' docs/tools.md
	sed -i 's|https://merlin.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/merlin/html/index.html|g' docs/tools.md
	sed -i 's|https://kosh.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/kosh/html/index.html|g' docs/tools.md
	sed -i 's|https://pydv.readthedocs.io/en/latest/|https://lc.llnl.gov/weave/pydv/html/index.html|g' docs/tools.md
	sed -i 's|https://llnl-ibis.readthedocs.io/en/latest|https://lc.llnl.gov/weave/ibis/html/index.html|g' docs/tools.md
	sed -i 's|https://llnl-trata.readthedocs.io/en/latest|https://lc.llnl.gov/weave/trata/html/index.html|g' docs/tools.md
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

define sync_zone_branch
	if [ $(SOURCE_ZONE) == RZ ]; then \
		$(call merge_branch_1_to_branch_2,origin/CZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push); \
	fi
	if [ $(SOURCE_ZONE) == SCF ]; then \
		$(call merge_branch_1_to_branch_2,origin/RZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push); \
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
	rm -rf weave_ci
	git clone -b develop $(WEAVE_CI_URL)
	ls -l weave_ci
	rm -rf $(VENV)
	$(CREATE_VENV_SCRIPT) -v latest-develop -e $(VENV) -p cpu
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

merge_for_push_to_zone_feature:
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	echo "### git pull origin $(SOURCE_ZONE)_$(TARGET) ###"
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_zone:
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)

merge_for_push_to_target_feature:
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_target_branch:
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)


#
# RZ
#
merge_for_push_to_zone_feature_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_zone_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)

merge_for_push_to_target_feature_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_target_branch_rz:
	$(call merge_branch_1_to_branch_2,origin/CZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)

#
# SCF
#
merge_for_push_to_zone_feature_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_zone_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)

merge_for_push_to_target_feature_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)
	git status
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(TARGET)
	git status

merge_for_push_to_target_branch_scf:
	$(call merge_branch_1_to_branch_2,origin/RZ_$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(TARGET),$(SOURCE_ZONE)_$(TARGET),push)
	$(call merge_branch_1_to_branch_2,origin/$(SOURCE_ZONE)_$(TARGET),$(TARGET),no_push)

deploy_docs_PREV:
	mkdir -p $(DOCS_DIR)
	cp -pr build_docs_dir/Sina $(DOCS_DIR)
	cp -pr build_docs_dir/maestrowf $(DOCS_DIR)
	cp -pr build_docs_dir/pydv $(DOCS_DIR)
	cp -pr build_docs_dir/kosh $(DOCS_DIR)
	cp -pr build_docs_dir/trata $(DOCS_DIR)
	cp -pr build_docs_dir/ibis $(DOCS_DIR)
	cp -pr build_docs_dir/StudyWeaver $(DOCS_DIR)
	cp -pr build_docs_dir/merlin $(DOCS_DIR)
	cp -pr build_docs_dir/weave/* $(DOCS_DIR)
	rm -rf build_docs_dir
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)

deploy_docs:
	mkdir -p $(DOCS_DIR)
	cp -pr build_docs_dir/Sina $(DOCS_DIR)
	cp -pr build_docs_dir/maestrowf $(DOCS_DIR)
	cp -pr build_docs_dir/pydv $(DOCS_DIR)
	cp -pr build_docs_dir/kosh $(DOCS_DIR)
	cp -pr build_docs_dir/trata $(DOCS_DIR)
	cp -pr build_docs_dir/ibis $(DOCS_DIR)
	cp -pr build_docs_dir/weave/* $(DOCS_DIR)
	cp -pr build_docs_dir/StudyWeaver $(DOCS_DIR)
	cp -pr build_docs_dir/weave/* $(DOCS_DIR)
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)
	cp -pr build_docs_dir/merlin $(DOCS_DIR)
	rm -rf build_docs_dir
	chgrp -R $(DOCS_GROUP) $(DOCS_DIR)
