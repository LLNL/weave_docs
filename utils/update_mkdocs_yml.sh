#!/bin/bash

Help()
{
    echo ""
    echo "Update mkdocs.yml with entries for building LLNL WEAVE docs"
    echo ""
    echo "Usage: "
    echo "  -f <mkdocs_yml_file> : full path to mkdocs yml file to be updated"
    echo ""
}

get_options()
{
    local OPTIND OPTARG option
    while getopts "f:h" option; do
	case $option in
	    h) # display Help
		Help
		exit;;
	    f) # mkdocs.yml file full path
		mkdocs_yml=$OPTARG
		;;
	    \?) # Invalid option
		echo "Error: Invalid option"
		exit;;
	esac
    done
    shift "$((OPTIND-1))"
}

insert_line() {
    line_before=$1
    line_to_insert=$2
    file_to_edit=$3
    sed -i "s/$line_before/$line_before\n$line_to_insert/" $file_to_edit
}

update_mkdocs_yml_for_releases() {
    file_to_edit=$1
    releases=`ls -r docs/llnl/venvs_versions/releases`
    echo "releases: $releases"
    first_release=1
    releases_path=`echo "llnl/venvs_versions/releases" | sed 's/\//\\\\\//g'`

    for r in $releases; do
	    release_mds=`ls docs/llnl/venvs_versions/releases/$r`
	    if [ $first_release == 1 ]; then
	        insert_line '      - Versions:' "        - $r:" $file_to_edit
	        first_release=0
	    else
	        insert_line "$prev_insert" "        - $r:" $file_to_edit         
	    fi
	    this_release_insert="        - $r:"
	    first_md=1
	    for release_md in $release_mds; do
	        md=`echo $release_md | awk -F"." '{ print $1 }'`
	        if [ $first_md == 1 ]; then
		        insert_line "$this_release_insert" "          - $md: $releases_path\/$r\/$release_md" $file_to_edit
		        first_md=0
	        else 
		        insert_line "$prev_insert" "          - $md: $releases_path\/$r\/$release_md" $file_to_edit
	        fi
	        prev_insert="          - $md: $releases_path\/$r\/$release_md"
	    done
    done
}

update_mkdocs_yml_for_develop() {
    file_to_edit=$1

    develops=`ls -r docs/llnl/venvs_versions/develop`
    echo "develops: $develops"
    first_dev=1
    develops_path=`echo "llnl/venvs_versions/develop" | sed 's/\//\\\\\//g'`    

    insert_line '      - Versions:' '        - Develop:' $file_to_edit

    for dev_md in $develops; do
	dev=`echo $dev_md | awk -F. '{ print $1 }'`

	if [ $first_dev == 1 ]; then
	    insert_line '        - Develop:' "          - $dev: $develops_path\/$dev_md" $file_to_edit
   	    prev_insert="          - $dev: $develops_path\/$dev_md"
	    first_dev=0
	else
	    insert_line "$prev_insert" "          - $dev: $develops_path\/$dev_md" $file_to_edit
	fi
    done
}

#
# Main
#

get_options "$@"

if [ -z "$mkdocs_yml" ]; then
    Help
    exit
fi

echo "mkdocs_yml: $mkdocs_yml"
update_mkdocs_yml_for_develop $mkdocs_yml
update_mkdocs_yml_for_releases $mkdocs_yml

head -30 $mkdocs_yml

# ./update_mkdocs_yml.sh -f mkdocs.yml

