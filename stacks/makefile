VENV_NAME=stacks-venv
BUILD_DIR=build
STACK_NAME=Tweeter

all: clean-workspace json-template

clean-workspace:
	rm -rf ${VENV_NAME}
	rm -fr $(BUILD_DIR)

create-build-dir:
	mkdir -p $(BUILD_DIR)

json-template: pycodestyle create-build-dir
	. ${VENV_NAME}/Scripts/activate && python src/template.py > ${BUILD_DIR}/${STACK_NAME}.json

venv:
	python -m venv ${VENV_NAME}
	${VENV_NAME}/Scripts/pip install -r requirements.txt
	. ${VENV_NAME}/Scripts/activate
	echo "virtualenv prepared, please run 'source ${VENV_NAME}/bin/activate' if you wish to use it in your current shell"

pycodestyle:
	. ${VENV_NAME}/Scripts/activate && mypy --warn-unused-configs --disallow-any-generics --disallow-subclassing-any --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs --check-untyped-defs --disallow-untyped-decorators --no-implicit-optional --warn-redundant-casts --warn-unused-ignores --warn-return-any --no-implicit-reexport --strict-equality --ignore-missing-imports --pretty src/*.py && pycodestyle --first src/*.py