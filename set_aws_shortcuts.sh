#!/usr/bin/env bash

project="aws_shortcuts"

store="$HOME/.$project"
project_path="$store/$project"
alias_file="$store/.aliases"

printf "\nDetected OS type - $OSTYPE"
if ! [[ "$OSTYPE" == darwin* || "$OSTYPE" == "linux-gnu" ]]; then
    echo "Unsupported OS, exiting"
    exit 1
fi

printf "\nStarted setting the project $project..."

if ! [[ -z "$project" ]]; then
    rm -rf "$store"
fi

mkdir -p "$store"/{"$project",logs,temp}

git clone --quiet https://github.com/sunil-saini/"$project".git "$store/temp" >/dev/null
cp -r "$store/temp"/{*.py,*.json,*.properties,*.txt,*.sh} "$project_path"

rm -rf "$store/temp"

cron="$project_path/cron.sh"

chmod +x "$cron"

printf "\nInstalling pip dependencies..."
python -m pip install --ignore-installed -q -r "$project_path"/requirements.txt --user

printf "\nStarted collecting data from AWS, it may take few minutes...\n"

if python -c "import sys;sys.path.append('$project_path');from driver import main; main()"; then
    crontab -l > current_cron
    cron_line="0 */2 * * * /bin/bash $cron"
    if grep -Fxq "$cron_line" current_cron; then
        echo "Cron already set, skipping"
    else
        echo "0 */2 * * * /bin/bash $cron" >> current_cron
        crontab current_cron
        rm current_cron
        echo "Cron set successfully to keep updating data from AWS periodically"
    fi

    source "$alias_file"
    echo "Project set successfully, Open new terminal tab and enjoy the shortcut commands"
else
    echo "Error(s) in setting the project, please fix above mentioned error and run again"
fi
