#!/bin/bash

pidkill() {
  echo '[*] Found PID occupying port :'$1' - pid '$2
  echo '[*] Attempting to kill pid '$2
  sudo kill $2
  if [[ $? -eq '0' ]]; then
    echo '[+] Success!'
  else
    echo '[!] Failed to free process: '$2
    echo '[!] Aborting Lucky CAT startup'
    exit 1
  fi
}

for port in '5000' '5672'; do
  pid=$(sudo lsof -i :$port | grep LISTEN | grep '[0-9]*' | cut -d' ' -f2)
  if [[ $pid -ne '0' ]]; then
    pidkill $port $pid
  fi
done

for port in '27017'; do
  pid=$(sudo lsof -i :$port | grep LISTEN | grep '[0-9]*' | cut -d' ' -f3)
  if [[ $pid -ne '0' ]]; then
    pidkill $port $pid
  fi
done

echo "Starting Lucky CAT..."
docker-compose build && docker-compose up
