#!/usr/bin/env bash


cwd=$(pwd)

workspace_dir=$(cd `dirname $0`; pwd)
cd $workspace_dir
main_fuc='/app.py'
D:\\Games\\Anaconda\\python.exe ${workspace_dir}${main_fuc} $1

cd ${cwd}

read
