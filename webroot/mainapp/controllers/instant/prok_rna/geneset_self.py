# -*- coding: utf-8 -*-
import web
import json
import datetime
from mainapp.controllers.project.prok_rna_controller import ProkRNAController
from mbio.api.to_file.prok_rna import *
from mainapp.libs.signature import check_sig
import unittest
import os
import re
import codecs
from bson.objectid import ObjectId

class GenesetSelfAction(ProkRNAController):
    def __init__(self):
        super(GenesetSelfAction, self).__init__(instant=True)

    @check_sig
    def POST(self):
        input_data = web.input()
        basic_args = ["task_id", "trait_path"]
        # check arg
        for arg in basic_args:
            if not hasattr(input_data, arg):
                info = {'success': False, 'info': "Lack argument: {}".format(arg)}
                return json.dumps(info)
            if arg.lower() == "null":
                info = {'success': False, 'info': "{} : is null or NULL".format(arg)}
                return json.dumps(info)

        exp_info = self.prok_rna.get_task_info(task_id=input_data.task_id)
        project_sn = exp_info["project_sn"]
        task_id = input_data.task_id
        # create main table record
        params = dict(
            task_id=task_id,
            submit_location=input_data.submit_location,
            task_type=int(input_data.task_type),
            project_sn=project_sn
        )
        # if input_data.file_id:
        #     params['file_id'] = input_data.file_id
        params = json.dumps(params, sort_keys=True, separators=(',', ':'))
        time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        desc = "the_geneset_upload_at_%s_by_the_customer" % time
        if input_data.name:
            name = input_data.name
        else:
            name = desc

        if type(params) == dict:
            params = json.dumps(params, sort_keys=True, separators=(',', ':'))

        # get the upload file path
        # target_dir = 'sanger' if input_data.client == 'client01' else 'tsanger-data'
        # base_path = "/mnt/ilustre/{}".format(target_dir)
        # trait_path = base_path + input_data.trait_path
        trait_path = input_data.trait_path
        print trait_path
        if os.path.exists(trait_path):
            pass
        elif re.match(r'^\w+://\S+/.+$', input_data.trait_path):
            inter_dir = self.create_tmp_dir(input_data.task_id, "trait_path/")
            trait_path = self.download_from_s3(input_data.trait_path, inter_dir=inter_dir)
            if not os.path.exists(trait_path):
                info = {'success': False, 'info': "无法找到文件，请联系售后", "code": "C2901804"}
                return json.dumps(info)
        else:
            print trait_path
            raise "文件传递格式错误 {}".format(input_data.trait_path)
        content = open(trait_path).read()
        if content[:3] == codecs.BOM_UTF8:
            content = codecs.open(trait_path, 'r', 'utf-8').read()
        elif content[:2] in [codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE]:
            content = codecs.open(trait_path, 'r', 'utf-16').read()
        elif content[:4] in [codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]:
            content = codecs.open(trait_path, 'r', 'utf-32').read()
        open(trait_path, 'w').write(content)

        # prepare main table info
        main_info = dict(
            name=name,
            task_id=task_id,
            gene_length=0,
            project_sn=project_sn,
            group_id="",
            # type=input_data.gene_type,
            desc=desc,
            status="start",
            params = params,
        )
        main_id = self.prok_rna.insert_main_table('sg_geneset', main_info)

        # prepare option for workflow
        options = {
            "genes": task_id,
            "trait_path":trait_path,
            "name": input_data.name,
            # "g_or_t": g_or_t,
            "geneset_id": str(main_id),
            "update_info": json.dumps({str(main_id): "sg_geneset"})  # to update sg_status
        }
        # prepare to file
        to_files = ["prok_rna.export_geneset_from_query(genes)"]

        # 把参数交给workflow运行相应的tool， 其中to_file用于准备tool的输入文件
        task_name = 'prok_rna.report.geneset_self'
        self.set_sheet_data(name=task_name,
                            options=options,
                            main_table_name=name,  # 设置交互分析结果目录名
                            module_type="workflow",
                            to_file=to_files,
                            project_sn=project_sn,
                            task_id=input_data.task_id)

        # 运行workflow 并传回参数
        task_info = super(GenesetSelfAction, self).POST()
        task_info['content'] = {
            'ids': {
                'id': str(main_id),
                'name': name
                }
        }
        # task_info['group_dict'] = group_dict
        return json.dumps(task_info)

class TestFunction(unittest.TestCase):
    """
    This is test for the tool. Just run this script to do test.
    """
    def test_this(self):
        cmd = 'python /mnt/ilustre/users/sanger-dev/biocluster/bin/webapitest.py '
        cmd += 'post '
        cmd += "-fr no "
        cmd += '-c {} '.format("client03")
        cmd += "i/prok_rna/geneset_self "
        cmd += "-b http://bcl.tsg.com "
        args = dict(
            task_id="tsg_35470",
            task_type="1",
            submit_location="geneset_upload",
            name="prok_rna_ff",
            # gene_type="G",
            trait_path='/mnt/ilustre/users/sanger-dev/sg-users/zoujiaxun/geneset_test.txt',
            # file_id='123454'
        )
        arg_names, arg_values = args.keys(), args.values()
        cmd += '-n "{}" -d "{}" '.format(";".join(arg_names), ";".join(arg_values))
        print(cmd)
        os.system(cmd)


if __name__ == '__main__':
    unittest.main()