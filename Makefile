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


define pull_weave_docs_tutorials
	pwd
	echo "...CI in $(SOURCE_ZONE)...${GITLAB_USER_EMAIL} ... ${USER}"
	git config --global user.email "${GITLAB_USER_EMAIL}"
	git config --global user.name "${GITLAB_USER_NAME}"
	# Merge $(CI_COMMIT_BRANCH) into RZ_$(CI_COMMIT_BRANCH) or SCF_$(CI_COMMIT_BRANCH)
	# and push it to RZ_$(CI_COMMIT_BRANCH) or SCF_$(CI_COMMIT_BRANCH)
	git fetch --all
	git checkout $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH)
	git merge origin/$(CI_COMMIT_BRANCH) -m "merge $(CI_COMMIT_BRANCH) into $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH) [ci skip]" --no-ff --allow-unrelated-histories
	git remote rm origin
	if [ "$(SOURCE_ZONE)" == "CZ" ]; then \
		echo "DEBUG...git remote add origin $(CZ_GITLAB)/$(CI_PROJECT_PATH).git;"; \
		git remote add origin $(CZ_GITLAB)/$(CI_PROJECT_PATH).git; \
	else \
		echo "else...1"; \
		if [ "$(SOURCE_ZONE)" == RZ ]; then \
			git remote add origin $(CZ_GITLAB)/$(CI_PROJECT_PATH).git; \
			git remote add origin $(RZ_GITLAB)/$(CI_PROJECT_PATH).git; \
		else \
			git remote add origin $(CZ_GITLAB)/$(CI_PROJECT_PATH).git; \
			git remote add origin $(RZ_GITLAB)/$(CI_PROJECT_PATH).git; \
			git remote add origin $(SCF_GITLAB)/$(CI_PROJECT_PATH).git; \
		fi \
	fi
	git push origin HEAD:$(SOURCE_ZONE)_$(CI_COMMIT_BRANCH)
	# Merge CZ_$(CI_COMMIT_BRANCH) or RZ_$(CI_COMMIT_BRANCH)/SCF_$(CI_COMMIT_BRANCH) into $(CI_COMMIT_BRANCH)
	# but DO NOT commit and push... merge only for building the docs.
	git fetch --all
	git checkout $(CI_COMMIT_BRANCH)
	if [ $(SOURCE_ZONE) == CZ ]; then \
		git merge $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH) -m "merge $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH) into $(CI_COMMIT_BRANCH) [ci skip]" --no-ff --allow-unrelated-histories; \
	else \
		if [ $(SOURCE_ZONE) == RZ ]; then \
			git merge RZ_$(CI_COMMIT_BRANCH) -m "merge RZ_$(CI_COMMIT_BRANCH) into $(CI_COMMIT_BRANCH) [ci skip]" --no-ff --allow-unrelated-histories; \
		else \
			git merge SCF_$(CI_COMMIT_BRANCH) -m "merge SCF_$(CI_COMMIT_BRANCH) into $(CI_COMMIT_BRANCH) [ci skip]" --no-ff --allow-unrelated-histories; \
		fi \
	fi
	git pull origin $(CI_COMMIT_BRANCH)
	git pull origin $(SOURCE_ZONE)_$(CI_COMMIT_BRANCH)
	# git remote rm origin
	ls docs
	ls docs/tutorials/
	cat mkdocs.yml
endef

define patch_mkdocs_yml
	$(UPDATE_MKDOCS)
endef

pull_weave_docs_tutorials:
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

build_weave_docs:
	$(call pull_weave_docs_tutorials)
	$(call copy_mds)
	$(call patch_mds)
	$(call patch_mkdocs_yml)
	cat mkdocs.yml
	source $(DEPLOY_PATH)/$(latest_symlink)/bin/activate && \
	mkdocs build && \
	mkdir -p $(BUILD_DOCS_DIR)/weave && \
	ls weave && cp -r weave $(BUILD_DOCS_DIR)/

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
