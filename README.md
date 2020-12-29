## 在AWS多个账号多个Region启用AWS GuardDuty以及AWS SecurityHub服务

本项目旨在以自动化的流程在AWS多个账号多个Region启用AWS GuardDuty以及AWS SecurityHub服务，在执行过程中将会自动完成SecurityHub中子账号与主账号的关联，统一通过主账号SecurityHub收集和展示子账号的安全状态和数据。


## 准备工作

* AWS GuardDuty以及AWS SecurityHub服务启动脚本正常运行需要在主账号以及子账号创建两个角色，本项目中将使用CloudFormation模板部署这两个角色，其中主账号以Stack的方式部署，子账号将以Stackset的方式部署在AWS Organization中的所有子账号中。具体角色模板请参考template文件夹中的GuardDutyRole.yml以及SecurityHubRole.yml文件，data文件夹中的GuardDutyRole.json以及SecurityHubRole.json文件为角色的CloudFormation模板所需要的参数，其中AdministratorAccountId为主账号ID，如果脚本在本地工作机运行则将CreateInstanceRole参数设置为No。

* 在data文件夹中的accounts.csv文件中配置需要关联到主账号的子账号列表，账号应每行以AccountId，EmailAddress的格式列出。 EmailAddress必须是与根帐户关联的电子邮件。 

* 步骤中所有脚本需要在主账号中以管理员身份执行。

## 步骤
### 1. 在主账号部署GuardDuty角色:
```
python create_update_stack.py \
    --name GuardDutyRole \
    --template template/GuardDutyRole.yml \
    --parameters data/GuardDutyRole.json

```
* 请注意以上命令中--name参数指定的是CloudFormation模板名称，角色名称在GuardDutyRole.yml中定义

### 2. 在所有需要关联的子账号中部署GuardDuty角色
```
python create_stackset_and_instances.py \
    --name GuardDutyRole \
    --template template/GuardDutyRole.yml \
    --parameters data/GuardDutyRole.json \
    --enabled_regions us-east-1 \
    --ou OU_ID

```
* 以上命令中--name参数指定的是CloudFormation模板名称，角色名称在GuardDutyRole.yml中定义
* 命令参数--enabled_regions指定启用角色的区域，由于AWS IAM为Global服务，只需指定us-east-1即可
* 命令参数--ou需要指定AWS Organization的ID，这个Organization中的全部子账号都会进行部署

### 3. 在主账号以及子账号中启用AWS GuardDuty服务
```
python enableguardduty.py \
    --master_account MASTER_ACCOUNT_ID \
    --assume_role ManageGuardDuty \
    --enabled_regions us-east-1,us-west-2,ap-southeast-1 \
    data/accounts.csv

```
* 命令参数--master_account参数指定AWS主账号ID
* 命令参数--assume_role填入之前步骤中创建的GuardDuty角色名称，默认为ManageGuardDuty
* 命令参数--enabled_regions指定启用服务的区域，多个区域使用逗号隔开
* 命令参数最后一行为子账号信息CSV文件的路径
* 如需在主账号以及子账号禁用AWS GuardDuty服务，请运行以下命令
```
python disableguardduty.py \
    --master_account MASTER_ACCOUNT_ID \
    --assume_role ManageGuardDuty \
    --enabled_regions us-east-1,us-west-2,ap-southeast-1 \
    data/accounts.csv

```

### 4. 在主账号部署SecurityHub角色:
```
python create_update_stack.py \
    --name SecurityHubRole \
    --template template/SecurityHubRole.yml \
    --parameters data/SecurityHubRole.json

```
* 请注意以上命令中--name参数指定的是CloudFormation模板名称，角色名称在SecurityHubRole.yml中定义

### 5. 在所有需要关联的子账号中部署SecurityHub角色
```
python create_stackset_and_instances.py \
    --name SecurityHubRole \
    --template template/SecurityHubRole.yml \
    --parameters data/SecurityHubRole.json \
    --enabled_regions us-east-1 \
    --ou OU_ID

```
* 以上命令中--name参数指定的是CloudFormation模板名称，角色名称在SecurityHubRole.yml中定义
* 命令参数--enabled_regions指定启用角色的区域，由于AWS IAM为Global服务，只需指定us-east-1即可
* 命令参数--ou需要指定AWS Organization的ID，这个Organization中的全部子账号都会进行部署

### 6. 在主账号以及子账号中启用AWS SecurityHub服务
```
python enablesecurityhub.py \
    --master_account MASTER_ACCOUNT_ID \
    --assume_role ManageSecurityHub \
    --enabled_regions us-east-1,us-west-2,ap-southeast-1 \
    --enable_standards standards/aws-foundational-security-best-practices/v/1.0.0,arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0 \
    data/accounts.csv

```
* 命令参数--master_account参数指定AWS主账号ID
* 命令参数--assume_role填入之前步骤中创建的SecurityHub角色名称，默认为ManageSecurityHub
* 命令参数--enabled_regions指定启用服务的区域，多个区域使用逗号隔开
* 命令参数--enable_standards指定启用的安全性标准ARN，多个标准使用逗号隔开，默认启用两个标准：standards/aws-foundational-security-best-practices/v/1.0.0, arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0
* 命令参数最后一行为子账号信息CSV文件的路径
* 如需在主账号以及子账号禁用AWS SecurityHub服务，请运行以下命令
```
python disablesecurityhub.py \
    --master_account MASTER_ACCOUNT_ID \
    --assume_role ManageSecurityHub \
    --enabled_regions us-east-1,us-west-2,ap-southeast-1 \
    --delete_master \
    data/accounts.csv

```
### 7. 在主账号中配置CloudWatch Event + SNS
```
python create_update_stack.py \
    --name SecurityHubNotification \
    --template template/Notification.json \
    --enabled_regions us-east-1,us-west-2,ap-southeast-1

```
* 命令参数--name参数指定CloudFormation模板名称
* 命令参数--enabled_regions指定启用服务的区域，多个区域使用逗号隔开
* CloudFormation模板文件中可以定义来自SecurityHub安全事件触发CloudWatch Event的规则，比如只有特定安全级别的发现才发送通知，可以在模板文件中的EventPattern模块中配置Label参数，本例中只对MEDIUM，HIGH，CRITICAL三个级别的安全发现发送通知：
```
"EventPattern": {
    "detail-type": [
        "Security Hub Findings - Imported"
    ],
    "source": [
        "aws.securityhub"
    ],
    "detail": {
        "findings": {
            "Severity": {
                "Label": [
                    "MEDIUM","HIGH","CRITICAL"
                ]
            }
        }
    }
}
```
* 其中LABEL参数用于定义需要处理时间的安全级别。详情请参考：https://docs.aws.amazon.com/zh_cn/securityhub/1.0/APIReference/API_Severity.html，https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/CloudWatchEventsandEventPatterns.html
```
0 - INFORMATIONAL
1–39 - LOW
40–69 - MEDIUM
70–89 - HIGH
90–100 - CRITICAL
```