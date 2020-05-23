class Miner:
    def __init__(self, *args, **kwargs):
        pass

    def get_this_season(self, rank):
        # this_season[1:11] = 50
        # this_season[11:101] = 10
        # this_season[101:201] = 5
        # this_season[201:501] = 3
        # this_season[501:2001] = 2
        # this_season[2001:4000] = 1
        # this_season[4000:8000:100] = 50
        # this_season[8100:15001:100] = 15
        if rank <= 11:
            return 50*rank-50
        elif rank <= 101:
            return 10*rank+390
            # return 10*(rank-11) + 50*10
        elif rank <= 201:
            return 5*rank+895
            # return 5*(rank-101) + 10*90 + 50*10
        elif rank <= 501:
            return 3*rank+1297
            # return 3*(rank-201) + 5*100 +10*90 + 50*10
        elif rank <= 2001:
            return 2*rank+1798
            # return 2*(rank-501) + 3*300 + 5*100 +10*90 + 50*10
        elif rank <= 4000:
            return rank+3799
            # return 1*(rank-2001) + 2*1500 + 3*300 + 5*100 +10*90 + 50*10
        elif rank <= 8000:
            return 50*(rank//100)+5799
            # return (rank-4000)//100*50 + 1*1999 + 2*1500 + 3*300 + 5*100 +10*90 + 50*10
        else:
            return 15*(rank//100)+8599
            # return (rank-8001)//100*15 + 40*50 + 1*1999 + 2*1500 + 3*300 + 5*100 +10*90 + 50*10

    def get_all_season(self, rank):
        # all_season[1:11] = 500
        # all_season[11:101] = 50
        # all_season[101:201] = 30
        # all_season[201:501] = 10
        # all_season[501:1001] = 5
        # all_season[1001:2001] = 3
        # all_season[2001:4001] = 2
        # all_season[4001:7999] = 1
        # all_season[8100:15001:100] = 30
        if rank <= 11:
            return 500*rank-500
        elif rank <= 101:
            return 50*rank+4450
            # return 50*(rank-11) + 500*10
        elif rank <= 201:
            return 30*rank+6470
            # return 30*(rank-101) + 50*90 + 500*10
        elif rank <= 501:
            return 10*rank+10490
            # return 10*(rank-201) + 30*100 +50*90 + 500*10
        elif rank <= 1001:
            return 5*rank+12995
            # return 5* (rank-501) + 10*300 + 30*100 +50*90 + 500*10
        elif rank <= 2001:
            return 3*rank+14997
            # return 3*(rank-1001) + 5*500 + 10*300 + 30*100 +50*90 + 500*10
        elif rank <= 4001:
            return 2*rank+16998
            # return 2*(rank-2001) + 3*1000 + 5*500 + 10*300 + 30*100 +50*90 + 500*10
        elif rank <= 7999:
            return rank+20999
            # return (rank-4001) + 2*2000 + 3*1000 + 5*500 + 10*300 + 30*100 +50*90 + 500*10
        else:
            return 30*(rank//100)+26598
            # return (rank-8001)//100*30 + 3998 + 2*2000 + 3*1000 + 5*500 + 10*300 + 30*100 +50*90 + 500*10

    def miner(self, cmd: str):
        cmd = cmd.lstrip()
        if cmd.isdigit() and 15001 >= int(cmd) >= 1:
            rank = int(cmd)
            reply = "当前排名为:{}\n最高排名奖励还剩 {} 钻\n历届最高排名还剩 {} 钻".format(
                rank, self.get_this_season(rank), self.get_all_season(rank))
            return reply
        else:
            reply = "请输入1～15001之间的整数"
            return reply

    async def execute_async(self, ctx):
        if ctx['raw_message'].startswith('挖矿计算'):
            return self.miner(ctx['raw_message'][4:])
