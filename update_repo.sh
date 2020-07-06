#!/bin/bash

# import run or fail helper script

# remove the current commit file
bash rm -rf .commit_id

# move to the target repository
pushd $1 1> /dev/null
# reset any changes made to the repository
git reset --hard HEAD
# get the most recent commit
COMMIT=$(git log -n1)
if [ $? != 0 ]; then
  echo "Could not call git log"
  exit 1
fi
# Extract the commit id
COMMIT_ID=$(echo $COMMIT | awk '{print $2}')
