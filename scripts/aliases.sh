#!/usr/bin/env bash


read -r project ec2 ec2f dns dnsf lb lbf cf cff <<< $(echo $1 $2 $3 $4 $5 $6 $7 $8 $9)
shift 9
read -r s3 s3f lambdas lambdasf params paramsf get_param  <<< $(echo $1 $2 $3 $4 $5 $6 $7)

store="$HOME/.$project"
project_path="$store/$project"
alias_file="$store/.aliases"

import_project="import sys;sys.path.append('$project_path');from services import aws, common, driver"

echo """
$ec2() {
    grep -i \"\$1\" \"$store/$ec2f.txt\"
}

$dns() {
    grep -i \"\$1\" \"$store/$dnsf.txt\"
}

$lb() {
    grep -i \"\$1\" \"$store/$lbf.txt\"
}

$cf() {
    grep -i \"\$1\" \"$store/$cff.txt\"
}

$s3() {
    grep -i \"\$1\" \"$store/$s3f.txt\"
}

$lambdas() {
    grep -i \"\$1\" \"$store/$lambdasf.txt\"
}

$params() {
    grep -i \"\$1\" \"$store/$paramsf.txt\"
}

$get_param() {
    if [ ! -z \"\$1\" ]
    then
         python -c \"$import_project; aws.get_ssm_parameter_value('\$1')\"
    fi
}


awss() {
case \"\$1\" in
	"configure")
		python -c \"$import_project;common.configure_project_commands();common.create_alias_functions()\"
		source "$alias_file"
		;;
	"update-data")
		$project_path/scripts/cron.sh
		;;
	"update-project")
		git clone --quiet https://github.com/sunil-saini/"$project".git "$store/temp" >/dev/null
		cp -r "$store/temp"/{resources/*.json,scripts,services,requirements.txt,awss.py} $project_path
		rm -rf "$store/temp"
		python -m pip install --ignore-installed -q -r "$project_path"/requirements.txt --user
		python -c \"$import_project;common.create_alias_functions()\"
		source "$alias_file"
		awss update-data
		awss
		;;
	*)
		python -c \"$import_project;common.read_project_current_commands()\"
		;;
esac
}""" > "$alias_file"