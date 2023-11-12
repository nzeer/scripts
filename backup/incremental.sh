#!/bin/bash
TarFile=transfer-me.tar.gz
TheScript=$0
saveIFS="$IFS"
IFS=$'\n'
files=($(find . -maxdepth 1 -newer $TheScript -print))
unset files[0]; #remove "."
tmpfile=$(mktemp temp.XXXXXX)
IFS="$saveIFS"
elements=${#files[@]}
if [ "$elements" -gt "0" ]; then
    tar cvfz $TarFile --exclude ".svn" --exclude ".swp" --exclude "Icon?" --exclude ".DS_Store" --exclude "$TarFile" "${files[@]}" && touch -r $tmpfile $TheScript
fi
rm $tmpfile;
