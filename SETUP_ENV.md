# 部署
部署时用到mongo和ubuntu镜像，docker会自动下载镜像，因此无需主动pull
## 完全重新部署
  ```
  ./docker_op.sh
  ```
## 过程解释
* 制作镜像
  ```
  docker-compose build
  ```
  会生成以下4个镜像：
    - yqr/midware
    - yqr/btc_wallet
    - yqr/eth_wallet
    - yqr/python_web
* 启动数据库服务
  ```
  docker-compose up -d chaindb
  ```
* 添加认证信息
  ```
  docker cp mgmt/init_db.js chaincommonapi_chaindb_1:/
  sleep 5
  docker exec -it chaincommonapi_chaindb_1 mongo init_db.js
  ```
* 停止服务(删除容器)
  ```
  docker-compose down
  ```

## 参考
* https://hub.docker.com/_/mongo/
* https://hub.docker.com/_/ubuntu/