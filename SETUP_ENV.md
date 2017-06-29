chain_common_api

# setup
## mongo
* get docker image
  ```
  docker pull mongo
  ```
* run docker container
  ```
  docker run --name chaindb -p 27017:27017 -d mongo
  ```
* reference
  https://hub.docker.com/_/mongo/

## app
* get ubuntu base image
  ```
  docker pull ubuntu
  ```
* build app image

* reference
  https://hub.docker.com/_/ubuntu/