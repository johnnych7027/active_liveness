#!/bin/bash

black 2>/dev/null || echo "you do not have black. should install: pip3 install black"

# run formater
git diff --diff-filter=d --cached --name-only | egrep '\.py$' | xargs black 2>/dev/null

# apply changes after formater
git diff --diff-filter=d --cached --name-only | egrep '\.py$' | xargs git add 2>/dev/null
