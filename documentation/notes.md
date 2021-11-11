

This:
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


replaced this:
 
               amazon_linux2_product_patch_filter = ssm.CfnPatchBaseline.PatchFilterProperty(key='PRODUCT',
                                                                                              values=['AmazonLinux2',
                                                                                                      'AmazonLinux2.0'])

                amazon_linux2_classification_patch_filter = ssm.CfnPatchBaseline.PatchFilterProperty(key='CLASSIFICATION',
                                                                                                     values=['Security',
                                                                                                             'Bugfix',
                                                                                                             'Enhancement',
                                                                                                             'Recommended'])

                amazon_linux2_severity_patch_filter = ssm.CfnPatchBaseline.PatchFilterProperty(key='SEVERITY',
                                                                                               values=['Critical',
                                                                                                       'Important',
                                                                                                       'Medium',
                                                                                                       'Low'])