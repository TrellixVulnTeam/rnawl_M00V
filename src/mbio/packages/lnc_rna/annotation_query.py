# -*- coding: utf-8 -*-
# __author__ = 'zengjing'

import regex
import re
from biocluster.config import Config
import sys
from mbio.packages.rna.annot_config import AnnotConfig

class Transcript(object):
    def __init__(self):
        self.name = ''
        self.tran_id = ''
        self.is_gene = 'no'
        self.gene_id = ''
        self.gene_name = ''
        self.enterz = ''
        self.length = ''
        self.nr = ''
        self.swissprot = ''
        self.cog = ''
        self.nog = ''
        self.cog_ids = ''
        self.nog_ids = ''
        self.subloc = ''
        self.go = ''
        self.ko_id = ''
        self.ko_name = ''
        self.pathway = ''
        self.des = ''
        self.symbol = ''
        self.pfam = []

class AllAnnoStat(object):
    def __init__(self, kegg_version=None):
        self.stat_info = {}
        self.gene_names = {}
        self.gene2trans = {}
        # self.cog_string = Config().biodb_mongo_client.sanger_biodb.COG
        # self.kegg_ko = Config().biodb_mongo_client.sanger_biodb.kegg_ko_v1
        # self.go = Config().biodb_mongo_client.sanger_biodb.GO
        self.kegg_version = kegg_version
        self.client = Config().get_mongo_client(mtype="ref_rna", ref=True)
        self.ref_db = self.client[Config().get_mongo_dbname("ref_rna", ref=True)]  # 20171101 by zengjing 数据库连接方式修改
        self.cog_string = self.ref_db.COG
        self.kegg_ko = self.ref_db.kegg_ko_v1
        self.go = self.ref_db.GO
        self.gloabl = ["map01100", "map01110", "map01120", "map01130", "map01200", "map01210", "map01212", "map01230", "map01220"]

    def get_anno_stat(self, gene2trans, tran_outpath, gene_outpath, new_gtf_path, ref_gtf_path, length_path, gene_file, cog_list=None, kegg_table=None, gos_list=None, blast_nr_table=None, blast_swissprot_table=None, pfam_domain=None, des=None, subloc=None, enterz=None, des_type="type3"):
        """
        传入各个数据库的部分注释结果文件，统计功能注释信息表（即应注释查询模块的功能注释信息表）
        tran_outpath：输出结果路径：转录本功能注释信息表的文件路径；gene_outpath：基因功能注释信息表的文件路径
        new_gtf_path：新转录本的gtf文件，提取转录本对应的基因ID
        ref_gtf_path: 参考基因的gtf文件，提取基因ID对应的基因名称
        cog_list：string2cog注释tool统计得到的cog_list.xls,提取cog/nog及对应的功能分类信息
        kegg_table：kegg_annotation注释tool统计得到的kegg_table.xls
        gos_list：go_annotation注释tool统计得到的query_gos.list
        blast_nr_table：blast比对nr库得到的结果文件(blast输出文件格式为6：table)
        blast_swissprot_table: blast比对swissprot库得到的结果文件（blast输出文件格式为6：table）
        pfam_domain: orf预测的结果pfam_domain
        length_path:注释转录本序列长度
        """
        self.get_unigene(gene2trans)

        if des != None and des != "None":
            self.get_des(des=des, des_type=des_type)
        if blast_nr_table != None and blast_nr_table != "None":
            self.get_nr(blast_nr_table=blast_nr_table)
        if blast_swissprot_table != None and blast_swissprot_table != "None":
            self.get_swissprot(blast_swissprot_table=blast_swissprot_table)
        if pfam_domain != None and pfam_domain != "None":
            self.get_pfam(pfam_domain=pfam_domain)
        if gos_list != None and gos_list != "None":
            self.get_go(gos_list=gos_list)
        if kegg_table != None and kegg_table != "None":
            self.get_kegg(kegg_table=kegg_table)
        if cog_list != None and cog_list != "None":
            self.get_cog(cog_list=cog_list)
        if subloc != None and subloc != "None":
            self.get_subloc(subloc=subloc)
        if enterz != None and enterz != "None":
            self.get_enterz(enterz=enterz)

        with open(tran_outpath, 'wb') as w:
            head = 'gene_id\ttranscript_id\tis_gene\tgene_name\tlength\tdescription\tcog\tcog_description\tKO_id\tKO_name\tpaths\tpfam\tgo\tnr\tswissprot\tentrez\n'
            w.write(head)
            for name in self.stat_info:
                try:
                    gene_name = self.gene_names[self.stat_info[name].gene_id]
                except:
                    gene_name = ''
                if gene2trans:
                    w.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                        # name,
                        self.stat_info[name].gene_id,
                        self.stat_info[name].tran_id,
                        self.stat_info[name].is_gene,
                        self.stat_info[name].gene_name,
                        self.stat_info[name].length,
                        self.stat_info[name].des,
                        self.stat_info[name].cog,
                        self.stat_info[name].cog_ids,
                        self.stat_info[name].ko_id,
                        self.stat_info[name].ko_name,
                        self.stat_info[name].pathway,
                        '; '.join(self.stat_info[name].pfam),
                        self.stat_info[name].go,
                        self.stat_info[name].nr,
                        self.stat_info[name].swissprot,
                        self.stat_info[name].enterz
                    ))
        #gene_list = self.gene_names.keys()

    def get_unigene(self, gene2trans):
        """denovo组装 找到转录本ID对应的基因ID"""
        # gene_ids = []
        with open (gene2trans, 'r') as f:
            lines = f.readlines()

            for line in lines:
                line = line.strip().split('\t')
                if self.gene2trans.has_key(line[1]):
                    self.gene2trans[line[1]].append(line[0])
                else:
                    self.gene2trans[line[1]] = [line[0]]

                self.stat_info[line[0]] = Transcript()
                self.stat_info[line[0]].length = line[3]
                self.stat_info[line[0]].name = line[0]
                self.stat_info[line[0]].gene_id = line[1]
                self.stat_info[line[0]].is_gene = line[2]
                self.stat_info[line[0]].tran_id = line[0]
                if line[2] == "yes":
                    self.gene_names[line[0]] = line[1]

    def get_subloc(self, subloc):
        """denovo组装 找到转录本ID对应的基因ID"""
        # gene_ids = []
        with open (subloc, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().split('\t')
                location = line[1].split(':')[0]
                self.stat_info[line[0]].subloc = location

    def get_enterz(self, enterz):
        """获取enterz_id"""
        # gene_ids = []
        with open (enterz, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().split('\t')
                if len(line) > 2 and line[2] != "":
                    if self.stat_info.has_key(line[1]):
                        self.stat_info[line[1]].enterz = line[2]


    def get_gene(self, new_gtf_path, ref_gtf_path):
        """找到转录本ID对应的基因ID及基因名称"""
        gene_ids = []
        if new_gtf_path:
            gtf_path = new_gtf_path
        else:
            gtf_path = ref_gtf_path
        for line in open(gtf_path):
            content_m = regex.match(
                r'^([^#]\S*?)\t+((\S+)\t+){7}(.*;)*((transcript_id|gene_id)\s+?\"(\S+?)\");.*((transcript_id|gene_id)\s+?\"(\S+?)\");(.*;)*$',
                line.strip())
            if content_m:
                if 'transcript_id' in content_m.captures(6):
                    query_name = content_m.captures(7)[0]
                    gene_id = content_m.captures(10)[0]
                else:
                    query_name = content_m.captures(10)[0]
                    gene_id = content_m.captures(7)[0]
                if query_name not in self.stat_info:
                    query = Transcript()
                    query.name = query_name
                    query.gene_id = gene_id
                    self.stat_info[query_name] = query
                    gene_ids.append(gene_id)
        gene_ids = list(set(gene_ids))
        if ref_gtf_path:
            gtf_path = ref_gtf_path
        else:
            gtf_path = new_gtf_path
        for line in open(gtf_path):
            m = re.match(r".+gene_id \"(.+?)\"; .*gene_name \"(.+?)\";.*$", line)
            if m:
                gene_id = m.group(1)
                gene_name = m.group(2)
                if gene_id in gene_ids:
                    self.gene_names[gene_id] = gene_name

    def get_kegg(self, kegg_table):
        "找到转录本ID对应的KO、KO_name、Pathway、Pathway_definition"
        map2class = AnnotConfig().get_kegg_map2class(version=self.kegg_version)
        ko2des = AnnotConfig().get_kegg_ko2des(version=self.kegg_version)

        with open(kegg_table, 'rb') as r:
            r.readline()
            for line in r:
                line = line.strip('\n').split('\t')
                query_name = line[0]
                ko_id = line[1]
                ko_name = line[2]
                ko_des = ";".join([ko2des[ko] if ko in ko2des else "" for ko in ko_id.split(";")])
                pathways = line[4].split(";")
                pathway = []
                pathway_ids = []
                for map_id in pathways:
                    try:
                        map_num = re.sub(r'[a-z]*', '', map_id)
                        if map_num not in self.gloabl:
                            pid = "map" + map_num
                            definition = map2class[pid][2]
                            item = map_id + "(" + definition + ")"
                            pathway.append(item)
                    except:
                        pass
                pathway = "; ".join(pathway)
                if query_name in self.stat_info:
                    self.stat_info[query_name].ko_id = ko_id
                    self.stat_info[query_name].ko_name = ko_name
                    self.stat_info[query_name].pathway = pathway

        with open(kegg_table, 'rb') as r:
            r.readline()
            for line in r:
                line = line.strip('\n').split('\t')
                query_name = line[0]
                ko_id = line[1]
                ko_name = line[2]
                pathways = line[4].split(";")
                pathway = []
                for map_id in pathways:
                    try:
                        map_num = re.sub(r'[a-z]*', '', map_id)
                        if map_num not in self.gloabl:
                            pid = "ko" + map_num
                            result = self.kegg_ko.find_one({"pathway_id": {"$in": [pid]}})
                            pids = result["pathway_id"]
                            for index, i in enumerate(pids):
                                if i == pid:
                                    category = result["pathway_category"][index]
                                    definition = category[2]
                                    item = map_id + "(" + definition + ")"
                                    pathway.append(item)
                    except:
                        pass
                        # print "{}在该物种中没有pathway".format(query_name)
                pathway = "; ".join(pathway)
                if query_name in self.stat_info:
                    self.stat_info[query_name].ko_id = ko_id
                    self.stat_info[query_name].ko_name = ko_name
                    self.stat_info[query_name].pathway = pathway

    def get_go(self, gos_list):
        """找到转录本ID对应的goID及term、term_type"""
        with open(gos_list, 'rb') as r:
            for line in r:
                line = line.strip('\n').split('\t')
                query_name = line[0]
                go = line[1].split(";")
                gos = []
                for i in go:
                    result = self.go.find_one({"go_id": i})
                    if result:
                        item = i + "(" + result["ontology"] + ":" + result["name"] + ")"
                        gos.append(item)
                    else:
                        # 增加数据库中删除的GO
                        item = i + "(" + "deleted" + ":" + "old GO" + ")"
                        gos.append(item)
                gos = "; ".join(gos)
                if query_name in self.stat_info:
                    self.stat_info[query_name].go = gos

    def get_cog(self, cog_list):
        """找到转录本ID对应的cogID、nogID、kogID及功能分类和描述"""
        with open(cog_list, 'rb') as r:
            r.readline()
            for line in r:
                line = line.strip('\n').split('\t')
                query_name = line[0]
                cog = line[1]
                cog_class_abr = line[3].split(";")
                cog_class = line[4].split(";")
                cog_des = line[2]
                # nog = line[2]
                for i,j in enumerate(cog_class_abr):
                    if query_name in self.stat_info:
                        if self.stat_info[query_name].cog:
                            self.stat_info[query_name].cog += "; " + cog + "({}:{})".format(cog_class_abr[i], cog_class[i].strip())
                            self.stat_info[query_name].cog_ids += "; " + cog + "({})".format(cog_des)
                        else:
                            self.stat_info[query_name].cog = cog + "({}:{})".format(cog_class_abr[i], cog_class[i].strip())
                            self.stat_info[query_name].cog_ids = cog + "({})".format(cog_des)
                    # self.stat_info[query_name].cog = self.get_cog_group_categories(cog)[0]
                    # self.stat_info[query_name].nog = self.get_cog_group_categories(nog)[0]
                    # self.stat_info[query_name].cog_ids = self.get_cog_group_categories(cog)[1]
                    # self.stat_info[query_name].nog_ids = self.get_cog_group_categories(nog)[1]

    def get_cog_group_categories(self, group):
        """找到cog/nog/kogID对应的功能分类及功能分类描述、cog描述"""
        group = group.split(";")
        funs, ids = [], []
        for item in group:
            if item:
                result = self.cog_string.find({'cog_id': item, 'version': 10.0})
                for result_one in result:
                    group = result_one["cog_categories"]
                    group_des = result_one["categories_description"]
                    cog_des = result_one["cog_description"]
                    cog_fun = item + "(" + group + ":" + group_des + ")"
                    cog_id = item + "(" + cog_des + ")"
                    funs.append(cog_fun)
                    ids.append(cog_id)
        funs = "; ".join(funs)
        ids = "; ".join(ids)
        return funs, ids

    def get_nr(self, blast_nr_table):
        """找到转录本ID对应NR库的最佳hit_name和描述"""
        with open(blast_nr_table, 'rb') as f:
            f.readline()
            flag = None
            for line in f:
                line = line.strip('\n').split('\t')
                query_name = line[5]
                if flag == query_name:
                    pass
                else:
                    nr_hit_name = line[10]
                    nr_description = line[-1]
                    nr = nr_hit_name + "(" + nr_description + ")"
                    flag = query_name
                    if query_name in self.stat_info:
                        self.stat_info[query_name].nr = nr
                        self.stat_info[query_name].length = line[6]

    def get_swissprot(self, blast_swissprot_table):
        """找到转录本ID对应swissprot库的最佳hit_name及描述"""
        with open(blast_swissprot_table, 'rb') as f:
            f.readline()
            flag = None
            for line in f:
                line = line.strip('\n').split('\t')
                query_name = line[5]
                if flag == query_name:
                    pass
                else:
                    swissprot_hit_name = line[10]
                    swissprot_description = line[-1]
                    swissprot = swissprot_hit_name + "(" + swissprot_description + ")"
                    flag = query_name
                    if query_name in self.stat_info:
                        self.stat_info[query_name].swissprot = swissprot
                        self.stat_info[query_name].length = line[6]

    def get_pfam(self, pfam_domain):
        """找到转录本ID对应的最佳pfamID及domain、domain_description"""
        with open(pfam_domain, "rb") as f:
            f.readline()
            for line in f:
                line = line.strip().split('\t')
                query_name = line[0]
                pfam_id = line[2]
                domain = line[3]
                domain_description = line[4]
                pfam = pfam_id + "(" + domain + ":" + domain_description + ")"
                if query_name in self.stat_info:
                    if pfam not in self.stat_info[query_name].pfam:
                        pfams = self.stat_info[query_name].pfam
                        pfams.append(pfam)
                        self.stat_info[query_name].pfam = pfams

    def get_des(self, des, des_type):
        """
        获取蛋白名或描述信息
        """
        with open(des, "rb") as f:
            # f.readline()
            for line in f.readlines():
                line = line.strip().split('\t')
                gene_id = line[0]
                tran_id = line[1]
                if des_type == "type3":
                    symbol = ""
                    des = line[3]
                elif des_type == "type2":
                    symbol = line[2]
                    des = line[5]
                elif des_type == "type1":
                    symbol = line[2]
                    des = line[7]
                else:
                    pass
                # tran_id = line[3]
                # description = line[4] if len(line) >= 2 else ''
                # symbol = line[2] if len(line) >=3 else ''
                # symbol = ''
                # self.stat_info[tran_id] = Transcript()
                if self.stat_info.has_key(tran_id):
                    self.stat_info[tran_id].des = des
                    self.stat_info[tran_id].gene_name = symbol
                    self.stat_info[tran_id].symbol = symbol
                else:
                    # print gene_id
                    # 对应已知基因的基因 name和描述
                    if self.gene2trans.has_key(gene_id):
                        # print "has key gene".format(gene_id)
                        for tran in self.gene2trans[gene_id]:
                            if self.stat_info.has_key(tran):
                                # print "add gene symbol {}".format(tran)
                                self.stat_info[tran].des = des
                                self.stat_info[tran].gene_name = symbol
                                self.stat_info[tran].symbol = symbol
                            else:
                                pass



    def get_length(self, length_path):
        """每个转录本id对应的序列长度"""
        for line in open(length_path, "rb"):
            line = line.strip().split(" ")
            tran_id = line[1]
            length = line[0]
            if tran_id in self.stat_info:
                self.stat_info[tran_id].length = length


if __name__ == '__main__':
    Transcript()
    if sys.argv[3] == 'None':
        sys.argv[3] = None
    if sys.argv[7] == 'None':
        sys.argv[7] = None
    if sys.argv[8] == 'None':
        sys.argv[8] = None
    if sys.argv[9] == 'None':
        sys.argv[9] = None
    if sys.argv[10] == 'None':
        sys.argv[10] = None
    if sys.argv[11] == 'None':
        sys.argv[11] = None
    if sys.argv[12] == 'None':
        sys.argv[12] = None
    if sys.argv[13] == 'None':
        sys.argv[13] == None
    if sys.argv[14] == 'None':
        sys.argv[14] == None
    if sys.argv[15] == 'None':
        sys.argv[15] == None
    if sys.argv[16] == 'None':
        sys.argv[16] == None
    if sys.argv[16] == 'None':
        sys.argv[16] == None

    if len(sys.argv) > 18:
        inst = AllAnnoStat(kegg_version=sys.argv[18])
    else:
        inst = AllAnnoStat()
    inst.get_anno_stat(gene2trans=sys.argv[1],
                                tran_outpath=sys.argv[2],
                                gene_outpath=sys.argv[3],
                                new_gtf_path=sys.argv[4],
                                ref_gtf_path=sys.argv[5],
                                length_path=sys.argv[6],
                                gene_file=sys.argv[7],
                                cog_list=sys.argv[8],
                                kegg_table=sys.argv[9],
                                gos_list=sys.argv[10],
                                blast_nr_table=sys.argv[11],
                                blast_swissprot_table=sys.argv[12],
                                pfam_domain=sys.argv[13],
                                des=sys.argv[14],
                                subloc=sys.argv[15],
                                enterz=sys.argv[16],
                                des_type=sys.argv[17]
                                )