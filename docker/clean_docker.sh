#!/bin/bash
echo "This script removes all your Docker stuff"
read -p "Are you sure? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    docker rm $(docker ps -a -q) 
    docker rmi $(docker images -q)
    docker system prune
    docker volume rm -f luckycat_db_data
    docker volume rm -f luckycat_backend_data
else
    echo "Aborting..."
fi
