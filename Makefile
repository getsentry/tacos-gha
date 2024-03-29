# all recipes live in scripts at ./lib/make/
makelib ?= ./lib/make

# a nicer-looking xtrace: (one intentional trailing space)
export PS4 ?= + \033[31;1m$$\033[m 

# listing of all python-relevant inputs
python_files := $(shell git ls-files '*.py' 'requirements*.in' 'requirements*.txt')

.PHONY: all
all: venv .git/hooks/pre-commit TODO.grep.md


### commands: these will always run, even if nothing changed
commands := test lint format
test: $(makelib)/test venv
lint: $(makelib)/lint format
format: $(makelib)/format venv


### dependencies: it's important that these properly report "already done"
venv: $(makelib)/venv .python-version requirements-dev.txt .done/pyenv
requirements-dev.txt: $(makelib)/pip-compile requirements-dev.in
.done/pyenv: $(makelib)/pyenv .python-version .done/brew
.done/brew: $(makelib)/brew Brewfile
.git/hooks/pre-commit: $(makelib)/pre-commit venv
TODO.grep.md: ${makelib}/todo-grep always

### test coverage
# coverage commands
commands += coverage-report coverage-server
coverage-report: $(makelib)/coverage-report .coverage
coverage-server: $(makelib)/coverage-server coverage-html

# coverage deps
coverage-html: $(makelib)/coverage-html .coverage
.coverage: $(makelib)/coverage venv $(python_files)


### one recipe for all: run the target's first dependency, with zero args
$(commands) %:
	@set -x; "$<"


### incidental complexity: you might stop reading here :)
# useful to represent files that should always rebuild
.PHONY: always
always:

# commands: ignore any coincidental files with the same name:
.PHONY: $(commands)
# help debug (make -d) output be readable:
.SUFFIXES:
MAKEFLAGS:=--no-builtin-rules --no-builtin-variables
