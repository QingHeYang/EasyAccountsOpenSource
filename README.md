# 记账软件 开源文档说明  
## 项目简介
这是这个项目是[EasyAccounts](https://github.com/QingHeYang/EasyAccounts)的源码  
如果你有一定开发能力，可以根据这个源码进行二次开发，或者自己编译打包成docker文件  
如果你只是想使用记账软件，可以直接下载[EasyAccounts](https://github.com/QingHeYang/EasyAccounts)  

## 贡献指南  
[贡献指南](./CONTRIBUTING.md)

## 版本
v2.4.0   
更新时间：2025.02.19  
项目说明：https://qingheyang.github.io/EasyAccounts/#/function/README

## 项目结构
```Shell
(base) root@mercy-server:~/EasyAccountsProjects/EasyAccountsSource# tree -L 3
.
├── README.md
├── Server
│   ├── Dockerfile
│   ├── excel_template
│   │   ├── auto_excel.xls
│   │   └── screen_excel.xls
│   ├── make_jar.sh
│   └── YD_JZ
│       ├── pom.xml
│       ├── src
│       ├── target
│       └── YD_JZ.iml
├── Web
│   ├── Dockerfile
│   ├── make_nginx.sh
│   ├── nginx
│   │   └── default.conf
│   └── ydjz_web
│       ├── babel.config.js
│       ├── dist
│       ├── jest.config.js
│       ├── node_modules
│       ├── nohup.out
│       ├── package.json
│       ├── package-lock.json
│       ├── public
│       ├── README.md
│       ├── src
│       ├── tests
│       └── vue.config.js
└── WebHook
    ├── Dockerfile
    ├── make_webhook.sh
    ├── requirements.txt
    └── webhook.py
```

## 项目说明
### Server
excel_template 文件夹下存放了两个excel模板文件，用于导出excel文件
- auto_excel.xls: 月度记账模板
- screen_excel.xls: 筛选记账模板  

不推荐修改这两个文件  
YD_JZ 文件夹下是后端代码，使用的是SpringBoot框架，数据库使用的是mysql
- pom.xml: 项目依赖
- src: 项目源码
- target: 项目编译后的文件

java版本是11，如果你的java版本不是11，可能会出现编译错误，使用下面的命令安装openjdk11  
```Shell
apt-get install openjdk-11-jdk
```  
编译该项目还需要安装maven，如果没有安装maven，可以使用以下命令安装  
```Shell
apt-get install maven
```
编译制作镜像的脚本是make_jar.sh，执行这个脚本会自动编译项目，并制作镜像  
  
### Web
nginx 文件夹下存放了nginx的配置文件  
ydjz_web 文件夹下是前端代码，使用的是vue框架  
node.js版本为v16，如果你的node.js版本不是这个，可能会出现编译错误  
安装完node你需要下载依赖包，使用以下命令下载依赖包  
```Shell
npm install
```
然后执行编译  
```Shell
npm run build
```
编译制作镜像的脚本是make_nginx.sh，执行这个脚本会自动编译项目，并制作镜像  

### WebHook  
webhook.py 是一个简单的webhook服务，用于接收服务端生成sql、excel的文件  
方便你拓展功能，比如你可以在这个文件中加入发送邮件的功能  
需要注意的是，这个服务的requirements.txt文件中依赖比较少，如果你需要添加额外的功能，记得在 /WebHook/requestments.txt 中添加依赖  
执行make_webhook.sh脚本会自动编译项目，并制作镜像  

## 项目部署
如果你修改了某个端，重启Docker容器即可生效，也可以down掉compose，重新up  
```Shell
cd EasyAccounts
docker-compose down; docker-compose up -d
```  
前提是你没修改docker容器的tag，如果修改了tag，需要修改docker-compose.yml文件中的tag  

## 项目维护  
我会不定期更新这个项目，如果你有什么问题，欢迎提Issues，我会尽快回复  
如果帮助到你了，欢迎给我一个star，谢谢！  

## 安全声明  
这个项目是开源项目，你可以自由使用，但是请不要将这个项目用于商业用途，否则后果自负  
本项目没有上传任何使用者的数据，如果你发现有上传数据的行为，请及时联系我  
欢迎审查代码  

## 最后再说点别的事情  
这个项目是我业余时间开发的，可能会有很多不完善的地方  
我本职是一个Android开发工程师，对于前端、后端、数据库等方面的知识了解不多  
所以代码并不是很规范  
如果你想根据后台接口重新写一个前端界面，项目运行起来是有Swagger的，可以查看接口文档  
或者你根据接口文档，套用自己的别的服务也是可以的，例如你可以调用screen筛选接口，查询出来一段时间的收支情况
