# Werewolf
[![996.icu](https://img.shields.io/badge/link-996.icu-red.svg?label=Anti%20996)](https://996.icu)
[![Repo size](https://img.shields.io/github/repo-size/LucienZhang/werewolf?label=Repo%20Size)](https://github.com/LucienZhang/werewolf)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/lucienzhangzl/werewolf?label=Image%20Version)](https://hub.docker.com/r/lucienzhangzl/werewolf)
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/lucienzhangzl/werewolf?label=Image%20Size)](https://hub.docker.com/r/lucienzhangzl/werewolf)
[![MicroBadger Layers](https://img.shields.io/microbadger/layers/lucienzhangzl/werewolf?label=Image%20Layers)](https://hub.docker.com/r/lucienzhangzl/werewolf)

## Status

[![](https://github.com/LucienZhang/werewolf/workflows/Test/badge.svg)](https://github.com/LucienZhang/werewolf)
[![](https://github.com/LucienZhang/werewolf/workflows/Build/badge.svg)](https://hub.docker.com/r/lucienzhangzl/werewolf)

## Guideline

This is a repository for an online judge of game [*The Werewolves of Millers Hollow*](https://en.wikipedia.org/wiki/The_Werewolves_of_Millers_Hollow), to deploy this application on your server, follow the instructions:

1. Get Docker Engine for Ubuntu

   Visit [Documents](https://docs.docker.com/install/linux/docker-ce/ubuntu/) for more details.

   ```bash
   $ sudo apt-get remove docker docker-engine docker.io containerd runc
   $ sudo apt-get update
   $ sudo apt-get install \
       apt-transport-https \
       ca-certificates \
       curl \
       gnupg-agent \
       software-properties-common
   $ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   $ sudo apt-key fingerprint 0EBFCD88
       
   pub   rsa4096 2017-02-22 [SCEA]
         9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88
   uid           [ unknown] Docker Release (CE deb) <docker@docker.com>
   sub   rsa4096 2017-02-22 [S]
   
   $ sudo add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable"
   $ sudo apt-get update
   $ sudo apt-get install docker-ce docker-ce-cli containerd.io
   $ sudo docker run hello-world
   ```

2. Prepare Config Files

   ```bash
   $ mkdir -p /data/secrets/werewolf/instance
   $ ip addr show docker0 | grep -Po 'inet \K[\d.]+'
   172.17.0.1
   ```

   The IP address showed above is only for my machine, remember this address, we will use it in config files.

   ```bash
   $ vim /data/secrets/werewolf/instance/config.py
   
   DEBUG = False
   PORT = 8000
   SECRET_KEY = b'secret_key'
   SQLALCHEMY_DATABASE_URI = "mysql://username:password@172.17.0.1:3306/database?charset=utf8"
   # The IP address is what's shown in previous command, the port is which your mysql server on host machine is listening to, if you want to use sqlite, you can modify this attribute as below
   # SQLALCHEMY_DATABASE_URI = r'sqlite:////werewolf/instance/test.db'
   SQLALCHEMY_ECHO = False
   SQLALCHEMY_TRACK_MODIFICATIONS = False
   LOGIN_SECRET_KEY = 'another_secret_key'
   REDIS_URL = "redis://172.17.0.1"  # modify it to the IP address shown in previous command
   SCHEDULER_API_ENABLED = True
   GUNICORN = True
   ```

   ```bash
   $ vim /data/secrets/werewolf/instance/gunicorn.conf.py
   
   log_level = "warning"
   bind = "0.0.0.0:8000"
   ```

3. Install Redis

   ```bash
   $ sudo apt install redis-server
   $ sudo vim /etc/redis/redis.conf
   ```

   In the file `redis.conf`, set `supervised` from **`no`** to **`systemd`**, set `bind` to **`0.0.0.0`**, and set `dir` to **`/var/lib/redis`**

   ```bash
   ...
   supervised systemd
   ...
   bind 0.0.0.0
   ...
   dir /var/lib/redis
   ...
   ```

   ```bash
   $ sudo systemctl enable redis-server.service
   $ sudo systemctl restart redis
   $ redis-cli
   127.0.0.1:6379> ping
   PONG
   ```

4. Install and Config MySQL

   You don't need to install MySQL if you use SQLite

   ```bash
   $ sudo apt install mysql-server
   $ mysql --version
   $ sudo mysql -u root -p
   Enter password: [your password for root user in MySQL]
   ```

   ```mysql
   mysql> CREATE USER 'username'@'%' IDENTIFIED BY 'password';
   mysql> CREATE DATABASE `database` CHARACTER SET utf8 COLLATE utf8_general_ci;
   mysql> GRANT ALL PRIVILEGES ON database.* TO 'usernmae'@'%' IDENTIFIED BY 'password';
   mysql> FLUSH PRIVILEGES;
   ```

   Find MySQL config file and change the bind value, in my case, the config file is `/etc/mysql/mysql.conf.d/mysqld.cnf`

   ```bash
   vim /etc/mysql/mysql.conf.d/mysqld.cnf
   
   ...
   bind-address = 0.0.0.0
   ...
   
   sudo service mysql restart
   ```

5. Pull and Run Docker Image

   ```bash
   $ sudo docker pull lucienzhangzl/werewolf
   # You need to initialize the database if you run this for the first time
   $ sudo docker run -itd --name werewolf -p 8000:8000 -v /data/secrets/werewolf/instance:/data/project/werewolf/instance:ro lucienzhangzl/werewolf /bin/bash -c "DATABASE_URL=mysql://username:password@172.17.0.1:3306/database python scripts/init_db.py && gunicorn werewolf:create_app() -c ./werewolf/instance/gunicorn.conf.py"
   # Otherwise, just run below command
   $ sudo docker run -itd --name werewolf -p 8000:8000 -v /data/secrets/werewolf/instance:/data/project/werewolf/instance:ro lucienzhangzl/werewolf
   ```

6. Then you can access the website by URL `http://your-ip-address:8000/`