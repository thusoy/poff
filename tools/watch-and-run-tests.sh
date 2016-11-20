#!/bin/sh

TEST_COMMAND="./test"

$TEST_COMMAND

./venv/bin/watchmedo shell-command \
    --patterns="*.py" \
    --wait \
    --drop \
    --recursive \
    --command "$TEST_COMMAND" \
    poff/
