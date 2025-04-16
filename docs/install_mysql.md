# MySQL 8.0.41 安装文档

---

## 一、环境准备

### 更新软件源并安装依赖

```bash
sudo apt-get update
sudo apt-get install -y libaio1 libnuma-dev
```

---

## 二、解压安装包

### 进入安装包目录

```bash
cd /sxs/yyy
```

### 解压MySQL安装包（确保文件名正确）

```bash
xz -d mysql-8.0.41-linux-glibc2.28-x86_64.tar.xz
tar -xvf mysql-8.0.41-linux-glibc2.28-x86_64.tar
```

###  移动文件到/opt目录

```bash
sudo mv mysql-8.0.41-linux-glibc2.28-x86_64 /opt/mysql
```

---

#  三、创建用户和权限配置

### 创建mysql用户组和用户

```bash
sudo groupadd mysql
sudo useradd -r -g mysql -s /bin/false mysql
```

### 设置目录权限

```bash
sudo chown -R mysql:mysql /opt/mysql
sudo chmod -R 750 /opt/mysql
```

### 创建数据、日志、运行目录

```bash
sudo mkdir -p /opt/mysql/{data,logs,run}
sudo chown -R mysql:mysql /opt/mysql
```

---

#  四、初始化MySQL

### 进入MySQL目录

```bash
cd /opt/mysql
```

### 初始化数据库（无密码模式）

```bash
sudo bin/mysqld --initialize-insecure --user=mysql \
--basedir=/opt/mysql \
--datadir=/opt/mysql/data
```

---
# 五、配置环境变量

### 编辑全局配置文件

```bash
echo 'export PATH=/opt/mysql/bin:$PATH' | sudo tee -a /etc/profile
source /etc/profile
```

---

#  六、启动MySQL服务

### 手动启动服务（调试用）

```bash
sudo -u mysql /opt/mysql/bin/mysqld_safe \
--defaults-file=/opt/mysql/my.cnf \
--datadir=/opt/mysql/data \
--socket=/opt/mysql/run/mysql.sock \
--log-error=/opt/mysql/logs/mysql-error.log &
```

### 验证进程

```bash
ps aux | grep mysqld
```

---

# 七、设置开机自启

### 创建启动/停止脚本

```bash
echo 'sudo -u mysql /opt/mysql/bin/mysqld_safe --defaults-file=/opt/mysql/my.cnf &' > ~/start_mysql.sh
echo 'sudo /opt/mysql/bin/mysqladmin -u root -p --socket=/opt/mysql/run/mysqld.sock shutdown' > ~/stop_mysql.sh
chmod +x ~/*_mysql.sh
```
### 添加rc.local自启动

```bash
sudo tee -a /etc/rc.local <<EOF

# MySQL Autostart

/root/start_mysql.sh

EOF

sudo chmod +x /etc/rc.local
```

---

# 八、安全配置

### 连接MySQL（使用socket）

```bash
mysql -u root -p --socket=/opt/mysql/run/mysqld.sock
```

### 设置root密码

```bash
ALTER USER 'root'@'localhost' IDENTIFIED BY 'gdty@123';
```

### 创建审计用户

```bash
CREATE USER 'auditUser'@'%' IDENTIFIED BY 'AuditUserPassword';

GRANT ALL PRIVILEGES ON *.* TO 'auditUser'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
```

### 创建审计数据库

```bash
CREATE DATABASE audit_results;
```

---

#  九、Socket路径优化

# 创建软链接解决默认socket路径问题

```bash
sudo rm -f /tmp/mysql.sock
sudo ln -s /opt/mysql/run/mysqld.sock /tmp/mysql.sock
```

---

# 十、验证安装

### 查看数据库列表

```bash
SHOW DATABASES;
```

---

# 常见问题处理

1. **权限错误**  

确保所有MySQL相关目录属主为mysql用户：

```bash
sudo chown -R mysql:mysql /opt/mysql
```

2. **Socket连接失败**  

检查软链接有效性：

```bash
ls -l /tmp/mysql.sock
```

3. **依赖缺失**  

安装必需库：

```bash
sudo apt-get install libaio1 libnuma-dev~
```

