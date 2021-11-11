from aws_cdk import (
    core as cdk,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_ec2 as ec2,
)

import boto3


class CdkEc2PatchingStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        namespace = config['namespace']
        vpc_name = config['vpc_name']

        # this policy is used if your VPC has an S3 endpoint to allow it access to AWS Managed buckets
        # https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html
        rSsmInstanceProfileS3Policy = iam.ManagedPolicy(self, 'rSsmInstanceProfileS3Policy',
                                                        path='/',
                                                        managed_policy_name=f'{namespace}_ssm_instance_profile_policy',
                                                        statements=[
                                                            iam.PolicyStatement(
                                                                actions=['s3:GetObject'],
                                                                resources=[
                                                                    f'arn:aws:s3:::aws-ssm-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::aws-windows-downloads-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::amazon-ssm-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::amazon-ssm-packages-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::{cdk.Aws.REGION}-birdwatcher-prod/*',
                                                                    f'arn:aws:s3:::aws-ssm-distributor-file-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::aws-ssm-document-attachments-{cdk.Aws.REGION}/*',
                                                                    f'arn:aws:s3:::patch-baseline-snapshot-{cdk.Aws.REGION}/*'
                                                                ],
                                                                effect=iam.Effect.ALLOW
                                                            )
                                                        ])

        rSsmInstanceRole = iam.Role(self, 'rCfExecutionRole',
                                    role_name=f'{namespace}_custom_ssm_instance_role',
                                    assumed_by=iam.CompositePrincipal(
                                        iam.ServicePrincipal('ec2.amazonaws.com')
                                    ))

        rSsmInstanceRole.add_managed_policy(rSsmInstanceProfileS3Policy)
        rSsmInstanceRole.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchAgentServerPolicy'))
        rSsmInstanceRole.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'))
        rSsmInstanceRole.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMDirectoryServiceAccess'))

        rInstanceProfile = iam.CfnInstanceProfile(self, 'rInstanceProfile',
                                                  roles=[rSsmInstanceRole.role_name],
                                                  instance_profile_name=f'{namespace}-SsmCustomInstanceProfile',
                                                  path='/'
                                                  )

        ######################### Create VPC encpoint for SSM

        rVpc = ec2.Vpc.from_lookup(self, 'rVpc', vpc_name=f'{vpc_name}')

        rSsmVpcEndpoint = ec2.InterfaceVpcEndpoint(self, 'rSsmVpcEndpoint',
                                                   vpc=rVpc,
                                                   service=ec2.InterfaceVpcEndpointAwsService.SSM,
                                                   )
        # example endpoint policy
        # rSsmVpcEndpoint.add_to_policy(iam.PolicyStatement(
        #     actions=['s3:GetObject'],
        #     principals=[iam.StarPrincipal()],
        #     resources=[
        #         'ssm:ListCommands',
        #         'ssm:ListCommandInvocations',
        #         'ssm:GetCommandInvocation'
        #     ],
        #     effect=iam.Effect.ALLOW,
        #
        # ))

        #### Create Patch Baseline
        if 'ssm' in config.keys():
            if 'patch_baseline' in config['ssm'].keys():
                for patch_baseline in config['ssm']['patch_baseline']:
                    patch_baseline_name = patch_baseline
                    patch_baseline = config['ssm']['patch_baseline']
                    print(patch_baseline)

                    if 'patch_filter_properties' in patch_baseline[f'{patch_baseline_name}'].keys():
                        # The PatchFilter property type defines a patch filter for an AWS Systems Manager patch baseline.

                        patch_filters = []
                        for property in patch_baseline[f'{patch_baseline_name}']['patch_filter_properties']:
                            patch_filters.append(ssm.CfnPatchBaseline.PatchFilterProperty(key=f'{property}',
                                                                                          values=patch_baseline[f'{patch_baseline_name}']['patch_filter_properties'][f'{property}']['values']))

                        rPatchBaselinePatchFilterGroup = ssm.CfnPatchBaseline.PatchFilterGroupProperty(
                            patch_filters=patch_filters
                        )

                    rPatchBaselineRules = ssm.CfnPatchBaseline.RuleProperty(approve_after_days=patch_baseline[f'{patch_baseline_name}']['approve_after_days'],
                                                                            compliance_level=patch_baseline[f'{patch_baseline_name}']['compliance_level'],
                                                                            enable_non_security=patch_baseline[f'{patch_baseline_name}']['enable_non_security'],
                                                                            patch_filter_group=rPatchBaselinePatchFilterGroup,
                                                                            )

                    rPatchBaselineRuleGroup = ssm.CfnPatchBaseline.RuleGroupProperty(patch_rules=[rPatchBaselineRules])

                    rPatchBaseline = ssm.CfnPatchBaseline(self, 'rPatchBaseline',
                                                          name=f'{namespace}_{patch_baseline_name}',
                                                          description=patch_baseline[f'{patch_baseline_name}']['description'],
                                                          operating_system=patch_baseline[f'{patch_baseline_name}']['operating_system'],
                                                          approved_patches_enable_non_security=patch_baseline[f'{patch_baseline_name}']['approved_patches_enable_non_security'],
                                                          patch_groups=patch_baseline[f'{patch_baseline_name}']['patch_groups'],
                                                          approval_rules=rPatchBaselineRuleGroup,
                                                          )

        # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        rMaintenanceWindow = ssm.CfnMaintenanceWindow(self, 'rMaintenanceWindow',
                                                      name=f'{namespace}_custom_maintenance_window',
                                                      description='maintenance window for nlalex',
                                                      allow_unassociated_targets=True,
                                                      schedule='cron(0 4 ? * SUN *)',
                                                      duration=4,
                                                      cutoff=1,
                                                      schedule_timezone='America/Denver'
                                                      )

        rMaintenanceWindowTarget = ssm.CfnMaintenanceWindowTarget(self, 'rMaintenanceWindowTarget',
                                                                  description='nlalex maint window target',
                                                                  resource_type='INSTANCE',
                                                                  window_id=rMaintenanceWindow.ref,
                                                                  name=f'{namespace}_development_instances_targets',
                                                                  targets=[
                                                                      ssm.CfnMaintenanceWindowTarget.TargetsProperty(
                                                                          key='tag:environment',
                                                                          values=['development'])

                                                                  ])

        rMaintenanceWindowRunCommandParameters = ssm.CfnMaintenanceWindowTask.MaintenanceWindowRunCommandParametersProperty(
            parameters={
                "Operation": ["Install"]
            }
        )

        rSsmMaintWindowTask = ssm.CfnMaintenanceWindowTask(
            self, 'rSsmMaintWindowTask',
            max_concurrency='5',
            max_errors='5',
            priority=1,
            targets=[{'key': 'WindowTargetIds', 'values': [rMaintenanceWindowTarget.ref]}],
            task_arn='AWS-RunPatchBaseline',
            task_type='RUN_COMMAND',
            window_id=rMaintenanceWindow.ref,
            name=f'{namespace}_maintenance_window_task',
            task_invocation_parameters=ssm.CfnMaintenanceWindowTask.TaskInvocationParametersProperty(
                maintenance_window_run_command_parameters=rMaintenanceWindowRunCommandParameters)
        )
