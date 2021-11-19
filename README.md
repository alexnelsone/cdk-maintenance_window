this project creates patchbaselines for ec2 instances, a maintenance window and maintenance window task.

Figure out:
1. check root volume on ec2 and if low, increase size or do not patch.
2. run patching
3. reboot
4. Use AWS-RunPatchBaselineWithHooks


##Configure CloudWatch Agent to send disk utilization to CloudWatch
###install the cloudwatch agent:   
1. wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
2. sudo rpm -U amazon-cloudwatch-agent.rpm

3. edit /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json and add:
```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "append_dimensions": {
        "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      }
    }
  }
}
```
4. sudo systemctl restart amazon-cloudwatch-agent
5. verify by tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log

NOTE: make sure instance role has cloudwatch:PutMetricData


# Assumptions
1. that a vpc already exist.


# SSM Documents for patching:
https://docs.aws.amazon.com/systems-manager/latest/userguide/patch-manager-ssm-documents.html