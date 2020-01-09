# coding=utf-8

# 祖传代码，写得稀烂，不想改了

import csv
import json
import os
import pickle
import smtplib
import sys
import time
import zipfile
from email.encoders import encode_base64
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


class Report():
    """
    这个类用于发送出刀报告
    """

    cy_eff = [1.0, 1.0, 1.3, 1.3, 1.5,
              1.4, 1.4, 1.8, 1.8, 2.0,
              2.0, 2.0, 2.5, 2.5, 3.0]
    cy_eff_2 = [1.2, 1.2, 1.3, 1.4, 1.5,
                1.6, 1.6, 1.8, 1.9, 2.0,
                2.0, 2.0, 2.4, 2.4, 2.6]
    txt_list = []

    def __init__(self,  groupid):
        self.__groupid = groupid
        self.__path = os.path.dirname(sys.argv[0])
        self.yobot_eff = [0]*15
        self.tailing_eff = 0.0
        self.rpt_name = self.__groupid + \
            time.strftime("_%Y%m%d_%H%M%S", time.localtime())
        self.__rpt = {}
        self.txt_list = []
        if not os.path.exists(os.path.join(self.__path, "report")):
            os.mkdir(os.path.join(self.__path, "report"))
        if not os.path.exists(os.path.join(self.__path, "report", "daily")):
            os.mkdir(os.path.join(self.__path, "report", "daily"))

    def __del__(self):
        pass

    def _filt(self, data):
        mdata = {}
        bdata = [[] for _ in range(15)]
        for opt in data[0]:
            if opt[0]:
                lv = -1 if opt[3] <= 3 else 4 if opt[3] <= 10 else 9
                lv += opt[4]
                if opt[2] in mdata.keys():
                    mdata[opt[2]].append(
                        (opt[1], lv, opt[5], opt[6]))
                else:
                    mdata[opt[2]] = [(opt[1], lv, opt[5], opt[6])]
                bdata[lv].append((opt[1], opt[2], opt[5], opt[6]))
        # self.__rpt["period"] = (data[0][0][1],
        #                         data[0][-1][1])
        return mdata, bdata

    def _get_nick(self, data):
        nicks = []
        for m in self.__rpt["mem_list"]:
            if data[1][m][0] == m and m.isdigit():
                # 使用老李api
                res = requests.get("http://laoliapi.cn/king/qq.php?qq=" + m)
                if res.status_code == 200:
                    nicks.append(json.loads(res.text).get("name", m))
                else:
                    nicks.append(data[1][m][0])
            else:
                nicks.append(data[1][m][0])
        return nicks

    def _bmean(self, bdata):
        assert len(bdata) == 15
        means = []
        for boss in bdata:
            count = 0
            total = 0
            for dmg in boss:
                if(dmg[3] == 0):
                    total += dmg[2]
                    count += 1
            if count > 0:
                means.append(total/count)
            else:
                means.append(None)
        return means

    def _first_num(self, inlist):
        for t in inlist:
            if isinstance(t, int) or isinstance(t, float):
                return t
        return None

    def _eff(self, bmean, bbase):
        eff = [(1.0 if x == None else x/bbase)for x in bmean]
        return eff

    def _tail_eff(self, bdata):
        total_full = 0
        count_full = 0
        total_tail = 0
        count_tail = 0
        for blist, yeff in zip(bdata, self.yobot_eff):
            for dmg in blist:
                if dmg[3] == 0:
                    total_full += dmg[2]*yeff
                    count_full += 1
                else:
                    total_tail += dmg[2]*yeff
                    if dmg[3] == 1:
                        count_tail += 1
        if total_tail == 0:
            return None
        else:
            return (total_full * count_tail) / (total_tail * count_full)

    def _score(self, mdata, eff, taileff=False):
        score = []
        for mem in self.__rpt["mem_list"]:
            s = 0
            for dmg in mdata[mem]:
                s += int(dmg[2] * eff[dmg[1]] * (
                    1. if (dmg[3] == 0 or taileff == False)
                    else self.tailing_eff))
            score.append(s)
        return score

    def _proportion(self, list1, list2):
        return [("{:.2%}".format(k1/k2) if k2 else "0")
                for k1, k2 in zip(list1, list2)]

    def _count(self, mdata):
        t = []
        for mem in self.__rpt["mem_list"]:
            c = [0, 0, 0, 0, 0]
            for dmg in mdata[mem]:
                c[dmg[3]] += 1
            c[4] = c[0]+c[2]+c[3]
            t.append(c)
        return t

    def _gen_table(self, mdata):
        with open(os.path.join(self.__path, "conf.json"), "r", encoding="utf-8") as f:
            conf = json.load(f)
        time_offset = 14400 if conf[self.__groupid]["area"] == "jp" \
            else 10800  # GMT偏移：日服+4小时，台服+3小时
        date_set = set()
        for m in self.__rpt["mem_list"]:
            for d in mdata[m]:
                date_set.add(time.strftime(
                    "%m/%d",
                    time.gmtime(d[0]+time_offset)))
        date_list = list(date_set)
        date_list.sort()
        row, col = len(self.__rpt["mem_list"]), len(date_list)
        table_dict_list = []
        table_mem_height = []
        table_mem_count = []
        for m in self.__rpt["mem_list"]:
            m_dmg_dict = dict(zip(date_list, [[] for _ in range(col)]))
            m_height_dict = dict(zip(date_list, [0 for _ in range(col)]))
            m_count_dict = dict(zip(date_list, [0 for _ in range(col)]))
            for d in mdata[m]:
                dmg_date = time.strftime(
                    "%m/%d",
                    time.gmtime(d[0]+time_offset))  # pcr日
                dmg_time = time.strftime(
                    "(%d)%H:%M:%S",
                    time.gmtime(d[0]+28800))  # 北京时间
                dmg_boss = "{}{}".format(["A", "B", "C"][d[1]//5], d[1] % 5+1)
                dmg_type = ["完整刀", "尾刀", "余刀", "余尾刀"][d[3]]
                dmg_score = int(d[2]*self.yobot_eff[d[1]] *
                                (1. if d[3] == 0 else self.tailing_eff))
                m_dmg_dict[dmg_date].append(
                    [dmg_time, dmg_boss, d[2], dmg_type, dmg_score])
                m_height_dict[dmg_date] += 1
                if d[3] != 1:
                    m_count_dict[dmg_date] += 1
            table_dict_list.append(m_dmg_dict)
            table_mem_height.append(max(m_height_dict.values()))
            table_mem_count.append(m_count_dict)
        table = []
        table.append([None, None] +
                     [(d if i == 0 else None)for d in date_list for i in range(5)])
        table.append(["QQ号", "群名片"] +
                     ["时间", "boss", "伤害", "类型", "yobot积分"] * col)
        itr = zip(self.__rpt["mem_list"],
                  self.__rpt["nicknames"],
                  table_dict_list,
                  table_mem_height)
        for qq, nickname, dmglist, height in itr:
            for in_row in range(height):
                line = [qq, nickname] if in_row == 0 else [None, None]
                for d in date_list:
                    line.extend(dmglist[d][in_row]
                                if len(dmglist[d]) > in_row else [None]*5)
                table.append(line)
        table_count = []
        table_count.append(["QQ号", "群名片"] + date_list)
        itr = zip(self.__rpt["mem_list"],
                  self.__rpt["nicknames"],
                  table_mem_count)
        for qq, nickname, table_mem_count in itr:
            line = [qq, nickname]
            for d in date_list:
                line.append(table_mem_count[d])
            table_count.append(line)
        return table, table_count

    def _gen_report(self, table, count):
        rpt_path = os.path.join(self.__path, "report", self.rpt_name)
        if not os.path.exists(rpt_path):
            os.mkdir(rpt_path)
        overview = [self.__rpt["mem_list"],
                    self.__rpt["nicknames"],
                    self.__rpt["yb_sorce"],
                    self.__rpt["cy_sorce"],
                    self.__rpt["proportion"]
                    ]+list(map(list, zip(*self.__rpt["count"])))
        overview_header = ["QQ号", "群名片", "yobot公式得分", "cy公式得分",
                           "yobot/cy比例", "完整刀数", "尾刀数", "余刀数", "尾余刀数", "总刀数"]
        with open(os.path.join(rpt_path, "stat.csv"), "w", newline="", encoding="utf-8-sig") as f:
            wt = csv.writer(f)
            wt.writerow(overview_header)
            wt.writerows(zip(*overview))
        with open(os.path.join(rpt_path, "table.csv"), "w", newline="", encoding="utf-8-sig") as f:
            wt = csv.writer(f)
            wt.writerows(table)
        with open(os.path.join(rpt_path, "count.csv"), "w", newline="", encoding="utf-8-sig") as f:
            wt = csv.writer(f)
            wt.writerows(count)

    def _zip_report(self):
        with zipfile.ZipFile(os.path.join(self.__path,
                                          "report",
                                          self.rpt_name,
                                          self.rpt_name+".zip"),
                             compression=zipfile.ZIP_DEFLATED,
                             mode="w",
                             compresslevel=9) as z:
            z.write(os.path.join(self.__path, "data", self.__groupid+".log"),
                    arcname="日志.log")
            z.write(os.path.join(self.__path, "report", self.rpt_name, "stat.csv"),
                    arcname="数据统计.csv")
            z.write(os.path.join(self.__path, "report", self.rpt_name, "table.csv"),
                    arcname="出刀表.csv")
            z.write(os.path.join(self.__path, "report", self.rpt_name, "count.csv"),
                    arcname="每日出刀数.csv")

    def _sendmail(self):
        mailconfig = None
        with open(os.path.join(self.__path, "mailconf.json"), "r", encoding="utf-8") as f:
            mailconfig = json.load(f)
        if not mailconfig["subscriber"][self.__groupid]:
            self.txt_list.append("没有订阅者")
            return
        mail_host = mailconfig["sender"]["host"]
        mail_user = mailconfig["sender"]["user"]
        mail_pass = mailconfig["sender"]["pswd"]
        if mail_user == "unknown" or mail_pass == "unknown":
            self.txt_list.append("没有设置发件人，请在{}里填写发件人信息".format(
                os.path.join(self.__path, "mailconf.json")))
            return
        sender = mailconfig["sender"]["sender"]
        receivers = mailconfig["subscriber"][self.__groupid]
        receivers.append(self.mailaddr)
        message = MIMEMultipart()
        mail_text = MIMEText("公会战的统计报告已生成，详见附件", "plain", "utf-8")
        message.attach(mail_text)
        with open(os.path.join(self.__path, "report", self.rpt_name, self.rpt_name+".zip"), "rb") as attach:
            mail_attach = MIMEBase("application", "octet-stream")
            mail_attach.set_payload(attach.read())
        encode_base64(mail_attach)
        mail_attach.add_header("Content-Disposition",
                               "attachment",
                               filename=self.__groupid+"_battle_report.zip")
        message.attach(mail_attach)
        message["From"] = mailconfig["sender"]["sender"]
        message["To"] = "客户"
        subject = "公会战统计报告"
        message["Subject"] = Header(subject, "utf-8")
        smtp_obj = smtplib.SMTP()
        try:
            smtp_obj.connect(mail_host, 25)
            smtp_obj.login(mail_user, mail_pass)
            smtp_obj.sendmail(sender, receivers, message.as_string())
        except smtplib.SMTPServerDisconnected:
            self.txt_list.append("SMTP连接失败，请检查您与" +
                                 mailconfig["sender"]["host"] + "的连接")
            return
        except smtplib.SMTPAuthenticationError:
            self.txt_list.append(
                r"发件邮箱密码错误，请发送“设置邮箱”输入正确密码")
            return
        except smtplib.SMTPSenderRefused:
            self.txt_list.append(
                r"发件邮箱已被服务商禁用，请发送“设置邮箱”输入新的邮箱")
            return
        except Exception as other:
            self.txt_list.append("未知错误：")
            self.txt_list.append(str(other))
            return
        smtp_obj.quit()
        self.txt_list.append("报告已发送至：")
        for addr in receivers[:-1]:  # 不显示最后一个
            self.txt_list.append(addr)

    def _uploadfile(self):
        url = 'http://api.yobot.xyz/v2/reports/'
        f = open(os.path.join(self.__path, "report",
                              self.rpt_name, self.rpt_name+".zip"), 'rb')
        files = {'file': f}
        response = requests.post(url, files=files)
        f.close()
        p = response.text
        self.txt_list.append("公会战报告已上传，" + p)

    def _gen_daily(self, mdata, date=None):
        with open(os.path.join(self.__path, "conf.json"), "r", encoding="utf-8") as f:
            conf = json.load(f)
        time_offset = 14400 if conf[self.__groupid]["area"] == "jp" \
            else 10800  # GMT偏移：日服+4小时，台服+3小时
        if date == None or date == "today":
            date = time.strftime(
                "%m/%d",
                time.gmtime(time.time()+time_offset))  # pcr日
        elif date == "yesterday":
            date = time.strftime(
                "%m/%d",
                time.gmtime(time.time()+time_offset-86400))  # pcr日
        daily = []
        daily_all = 0
        for qq, nik in zip(self.__rpt["mem_list"], self.__rpt["nicknames"]):
            mem_daily = [qq, nik, 0]
            for d in mdata[qq]:
                d_date = time.strftime(
                    "%m/%d",
                    time.gmtime(d[0]+time_offset))
                if date == d_date:
                    dmg_time = time.strftime(
                        "%d/%H:%M",
                        time.gmtime(d[0]+28800))
                    dmg_boss = "{}{}".format(
                        ["A", "B", "C"][d[1]//5], d[1] % 5+1)
                    dmg_type = ["完整刀", "尾刀", "余刀", "余尾刀"][d[3]]
                    mem_daily.append("{}({}{}){:,}".format(
                        dmg_time, dmg_boss, dmg_type, d[2]))
                    if d[3] != 1:
                        mem_daily[2] += 1
            daily.append(mem_daily)
            daily_all += mem_daily[2]
        daily.sort()  # 按QQ号升序排序
        daily_header = ["QQ号", "群名片", "出刀数", "出刀详情"]
        filename = os.path.join(
            self.__path, "report", "daily", self.rpt_name+".csv")
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            wt = csv.writer(f)
            wt.writerow(daily_header)
            wt.writerows(daily)
            wt.writerow(["共{}人".format(len(self.__rpt["mem_list"])),
                         None,
                         "共{}刀".format(daily_all)])

    def _upload_daily(self):
        url = 'http://api.yobot.xyz/v2/reports/'
        f = open(os.path.join(
            self.__path, "report", "daily", self.rpt_name+".csv"), 'rb')
        files = {'file': f}
        response = requests.post(url, files=files)
        f.close()
        p = response.text
        self.txt_list.append("每日报告已生成，" + p)

    def report(self, mathod, date=None):
        """
        生成报告然后发送邮件/上传文件
        """
        with open(os.path.join(self.__path, "data", self.__groupid+".dat"), "rb") as f:
            raw_data = pickle.load(f)
        mem_data, boss_data = self._filt(raw_data)  # 取出成员伤害表与boss伤害表
        self.__rpt["mem_list"] = list(mem_data)
        self.__rpt["nicknames"] = self._get_nick(raw_data)
        if mathod == "uploaddaily":
            self._gen_daily(mem_data, date)
            self._upload_daily()
            return
        boss_mean = self._bmean(boss_data)  # 每个boss完整刀的平均伤害
        base_dmg = self._first_num(boss_mean)  # 伤害基本量
        if base_dmg == None:
            self.txt_list.append("100没有完整刀")
            return 100
        self.yobot_eff = self._eff(boss_mean, base_dmg)  # 得分系数
        self.tailing_eff = self._tail_eff(boss_data)  # 尾刀加成
        if self.tailing_eff == None:
            self.txt_list.append("101没有尾刀")
            return 101
        self.__rpt["yb_sorce"] = self._score(mem_data, self.yobot_eff, True)
        self.__rpt["cy_sorce"] = self._score(mem_data, self.cy_eff_2, False)
        self.__rpt["proportion"] = self._proportion(
            self.__rpt["yb_sorce"], self.__rpt["cy_sorce"])
        self.__rpt["count"] = self._count(mem_data)
        self.mailaddr = "yu@yobot.xyz"
        table, count = self._gen_table(mem_data)
        self._gen_report(table=table, count=count)
        self._zip_report()
        if mathod == "sendmail":
            self._sendmail()
        elif mathod == "uploadfile":
            self._uploadfile()

    def text(self):
        return "\n".join(self.txt_list)
