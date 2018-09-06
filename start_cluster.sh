#!/bin/bash

for port in '5000' '5672'; do
    pid=$(sudo lsof -i :$port | grep LISTEN | grep  '[0-9]*' | cut -d' ' -f2)
    if [[ $pid -ne '0' ]]; then
        echo '[*] Found PID occupying port :'$port' - pid '$pid
        echo '[*] Attempting to kill pid '$pid
        sudo kill $pid
        if [[ $? -eq '0' ]]; then
            echo '[+] Success!'
        else
            echo '[!] Failed to free process: '$pid
            echo '[!] Aborting Lucky CAT startup'
            exit 1
        fi
    fi
done

echo "Starting Lucky CAT..."
docker-compose build && docker-compose up
