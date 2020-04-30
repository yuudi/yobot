installDocker() {
    curl -fsSL "https://get.docker.com" | /bin/bash
    sudo usermod -aG docker $(whoami)
}

changeDockerSource() {
    sudo cat>/etc/docker/daemon.json<<EOF
{
  "registry-mirrors" : [
    "https://registry.docker-cn.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "debug" : true
}
EOF
}

installDockerCompose() {
  sudo curl -L "https://github.com/docker/compose/releases/download/1.25.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
}

installDocker
changeDockerSource
installDockerCompose

echo "Install Success!"
