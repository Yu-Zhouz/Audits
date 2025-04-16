#!/bin/bash

# 目标服务器的 IP 地址
TARGET_IP="172.16.15.10"
# SSH 用户名
SSH_USER="root"
# SSH 密码（如果使用密钥认证，可以忽略）
SSH_PASSWORD="gdty@123"

# MySQL 安装包路径（替换为实际路径）
INSTALL_PKG_DIR="/sxs/yyy"
INSTALL_PKG_NAME="mysql-8.0.41-linux-glibc2.28-x86_64.tar.xz"

# 通过 SSH 执行命令的函数
ssh_execute() {
    local cmd="$1"
    echo "Executing: $cmd"
    sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SSH_USER@$TARGET_IP" "$cmd"
}

# 1. 环境准备
ssh_execute "sudo apt-get update"
ssh_execute "sudo apt-get install -y libaio1 libnuma-dev"

# 2. 解压安装包
ssh_execute "cd $INSTALL_PKG_DIR"
ssh_execute "xz -d $INSTALL_PKG_NAME"
ssh_execute "tar -xvf ${INSTALL_PKG_NAME%.xz}"
ssh_execute "sudo mv mysql-8.0.41-linux-glibc2.28-x86_64 /opt/mysql"

# 3. 创建用户和权限配置
ssh_execute "sudo groupadd mysql"
ssh_execute "sudo useradd -r -g mysql -s /bin/false mysql"
ssh_execute "sudo chown -R mysql:mysql /opt/mysql"
ssh_execute "sudo chmod -R 750 /opt/mysql"
ssh_execute "sudo mkdir -p /opt/mysql/{data,logs,run}"
ssh_execute "sudo chown -R mysql:mysql /opt/mysql"

# 4. 初始化 MySQL
ssh_execute "cd /opt/mysql"
ssh_execute "sudo -u mysql bin/mysqld --initialize-insecure --user=mysql --basedir=/opt/mysql --datadir=/opt/mysql/data"

# 5. 配置环境变量
ssh_execute "echo 'export PATH=/opt/mysql/bin:\$PATH' | sudo tee -a /etc/profile"
ssh_execute "source /etc/profile"

# 6. 启动 MySQL 服务
ssh_execute "sudo -u mysql /opt/mysql/bin/mysqld_safe --datadir=/opt/mysql/data --socket=/opt/mysql/run/mysql.sock --log-error=/opt/mysql/logs/mysql-error.log &"
ssh_execute "ps aux | grep mysqld"

# 7. 设置开机自启
ssh_execute "echo 'sudo -u mysql /opt/mysql/bin/mysqld_safe --defaults-file=/opt/mysql/my.cnf &' > ~/start_mysql.sh"
ssh_execute "echo 'sudo /opt/mysql/bin/mysqladmin -u root -p --socket=/opt/mysql/run/mysqld.sock shutdown' > ~/stop_mysql.sh"
ssh_execute "chmod +x ~/*_mysql.sh"
ssh_execute "sudo tee -a /etc/rc.local <<EOF
# MySQL Autostart
/root/start_mysql.sh
EOF"
ssh_execute "sudo chmod +x /etc/rc.local"

# 8. 安全配置
ssh_execute "mysql -u root --socket=/opt/mysql/run/mysqld.sock -e \"ALTER USER 'root'@'localhost' IDENTIFIED BY 'gdty@123';\""
ssh_execute "mysql -u root -pgdty@123 --socket=/opt/mysql/run/mysqld.sock -e \"CREATE USER 'auditUser'@'%' IDENTIFIED BY 'AuditUserPassword';\""
ssh_execute "mysql -u root -pgdty@123 --socket=/opt/mysql/run/mysqld.sock -e \"GRANT ALL PRIVILEGES ON *.* TO 'auditUser'@'%' WITH GRANT OPTION; FLUSH PRIVILEGES;\""
ssh_execute "mysql -u root -pgdty@123 --socket=/opt/mysql/run/mysqld.sock -e \"CREATE DATABASE audit_results;\""

# 9. Socket 路径优化
ssh_execute "sudo rm -f /tmp/mysql.sock"
ssh_execute "sudo ln -s /opt/mysql/run/mysqld.sock /tmp/mysql.sock"

# 10. 验证安装
ssh_execute "mysql -u root -pgdty@123 --socket=/opt/mysql/run/mysqld.sock -e \"SHOW DATABASES;\""