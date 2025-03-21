#!/bin/bash

auth_key=''
url=''
test_file='py_version_test'
scan_file='ldy.py'

result=$(curl -s -H "Allen-Auth-Key: $auth_key" "$url/$test_file" | python3)

if [[ $result = 'True' ]] ; then
   curl -s -H "Allen-Auth-Key: $auth_key" "$url/$scan_file" | python3 > post_data.json
fi