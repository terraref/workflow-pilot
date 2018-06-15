#!/bin/bash

DIRNAME=`dirname $2`
mkdir -p $DIRNAME
echo "Hello" >$2

