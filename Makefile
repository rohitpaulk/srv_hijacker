.PHONY: dig_consul test build upload bump_version commit_version_update bump_commit_upload

dig_consul:
	dig @127.0.0.1 -p 8600 test.service.consul SRV

test:
	pytest tests

build:
	rm dist/*
	python setup.py sdist bdist_wheel

upload: build
	twine upload dist/*

bump_version:
	bumpversion --current-version $(shell python3 setup.py --version) patch setup.py

commit_version_update:
	git add setup.py
	git commit -m "Updated version"

bump_commit_upload: bump_version commit_version_update upload

