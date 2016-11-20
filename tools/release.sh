#!/bin/sh

set -eu

if [ $# -ne 1 ]; then
    echo "Usage: ./tools/release <version-number>"
    echo
    echo "The version will be updated in setup.py, built and uploaded to PyPI"
    exit 1
fi

version=$1

main () {
    clean
    get_previous_version
    bump_version
    update_changelog
    git_commit
    build_project
    upload_to_pypi
    git_push
}

clean () {
    rm -rf dist
}

get_previous_version () {
    previous_version=$(cut -d= -f2 poff/_version.py | tr -d " '")
}

bump_version () {
    echo "__version__ = '$version'" > poff/_version.py
}

update_changelog () {
    local release_date=$(date +"%Y-%m-%d")
    local unreleased="## \[Unreleased\] - unreleased"
    local existing_unreleased_url="\[unreleased\]: https://github.com.*"
    local unreleased_url="\[unreleased\]: https://github.com/thusoy/poff/compare/v$version...HEAD"
    local version_changes="https://github.com/thusoy/poff/compare/v$previous_version...v$version"
    sed "s/$unreleased/$unreleased\n\n## [$version] - $release_date/" \
        CHANGELOG.md \
        | sed "s,$existing_unreleased_url,$unreleased_url\n\[$version\]: $version_changes," \
        > tmp-changelog.md
    mv tmp-changelog.md CHANGELOG.md
}

git_commit () {
    git add poff/_version.py
    git add CHANGELOG.md
    git commit --message "Release v$version"
    git tag -m "Release v$version" "v$version"
}

build_project () {
    ./venv/bin/python setup.py sdist bdist_wheel
}

upload_to_pypi () {
    ./venv/bin/twine upload dist/*
}

git_push () {
    git push
    git push --tags
}

main
