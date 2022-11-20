run := poetry run

package_dir := butcher
code_dir := $(package_dir)

# =================================================================================================
# Code quality
# =================================================================================================

.PHONY: lint
lint:
	$(py) isort --check-only $(code_dir)
	$(py) black --check --diff $(code_dir)
	$(py) flake8 $(code_dir)

.PHONY: reformat
reformat:
	$(py) black $(code_dir)
	$(py) isort $(code_dir)
