# 部署
## 准备工作
* 获取 mongo 镜像
  ```
  docker pull mongo
  ```
* 获取Ubuntu镜像
  ```
  docker pull ubuntu
  ```
## 安装部署
* 制作镜像
  ```
  docker-compose build
  ```
* 启动服务
  ```
  docker-compose up -d chain_midware
  ```
* 停止服务
  ```
  docker-compose down
  ```

## 参考
* https://hub.docker.com/_/mongo/
* https://hub.docker.com/_/ubuntu/