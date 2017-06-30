chain_common_api

# setup
## mongo
* get mongo image
  ```
  docker pull mongo
  ```
* run mongo container
  ```
  docker run --name chaindb -p 27017:27017 -d mongo
  ```
* reference
  https://hub.docker.com/_/mongo/

## app
* get ubuntu base image
  ```
  docker pull ubuntu
  docker build -f Dockerfile.base -t chain_master/python_web:1.0 .
  ```
* build app image
  ```
  docker build -t chain_master/midware:1.0 .
  ```
* run app container
  ```
  docker run -d --name chain_midware -p 80:80 chain_master/midware:1.0
  ```
* reference
  https://hub.docker.com/_/ubuntu/