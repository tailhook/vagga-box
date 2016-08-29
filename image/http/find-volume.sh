#!/bin/sh
name=${VAGGA_PROJECT_NAME}
base=/vagga

if [ ! -e $base/$name ]; then
    mkdir $base/$name
    echo $name
    exit 0
fi
for i in $(seq 100); do
    dir=$base/$name-$i
    if [ ! -e $dir ]; then
        mkdir $dir
        echo $name-$i
        exit 0
    fi
done
echo Too many directories named '"'"$name"'"' >> /dev/stderr
exit 1
