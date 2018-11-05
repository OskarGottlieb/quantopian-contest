# Quantopian Contest Visualization
This repo contains a dash app that analyzes strategies deployed in the Quantopian contest. 

## Deployement
You can deploy the app simply by 
1. Copying this repo with `git clone https://github.com/OskarGottlieb/quantopian-contest`
2. Bulding the docker image `docker build . -t dashapp`
3. And then running the image with `docker run -p 80:8050 -d dashapp`

I will add Volume blocks later on, so far the Docker implementation is rather naive - with every build, all the data needs to be   downloaded from the scratch - the build therefore takes a while.

The app is currently running at [http://178.128.225.136/](http://178.128.225.136/) if you want to check it out.

## TBD
1. Improve the DockerFile
2. Add more statistics - histogram of winnings, average time in contest, shortest time in contest until 1st place etc..
3. Add automatic daily downloads of the *.csv* files - probably via Celery tasks
4. Add support of Nginx as well as Docker-compose.
