if (!Object.defineProperty) {
  alert("浏览器版本过低");
}
var vm = new Vue({
  el: "#app",
  data() {
    return {
      activeIndex: "4",
      userData: {},
      dialogTableVisible: false,
      activeId: null,
    };
  },
  computed: {
    statisticsData() {
      return Object.entries(this.userData).map(([qqid, data]) => ({
        ...data,
        qqid,
      }));
    },
    gridData() {
      if (!this.dialogTableVisible) return [];
      return this.userData[this.activeId].damageDetail;
    },
  },
  mounted() {
    axios
      .all([
        axios.get("./api/"),
        axios.post("../api/", {
          action: "get_member_list",
          csrf_token: csrf_token,
        }),
      ])
      .then(
        axios.spread(function (resData, resUser) {
          if (resData.data.code != 0) {
            thisvue.$alert(res.data.message, "获取记录失败");
            return;
          }
          if (resUser.data.code != 0) {
            thisvue.$alert(memres.data.message, "获取成员失败");
            return;
          }
          const data = {};
          resUser.data.members.forEach((item) => {
            data[item.qqid] = {
              nickname: item.nickname,
              damage: 0,
              damageDetail: [],
            };
          });
          resData.data.challenges
            .sort((a, b) => (a.challenge_time > b.challenge_time ? 1 : -1))
            .forEach((item) => {
              const { qqid, damage } = item;
              data[qqid].damage += damage;
              data[qqid].damageDetail.push(item);
            });
          this.userData = data;
        })
      );
  },
  methods: {
    csummary: function (cha) {
      if (cha == undefined) {
        return "";
      }
      return `(${cha.cycle}-${cha.boss_num}${
        cha.is_continue ? "剩余刀" : ""
      }) <a class="digit${cha.damage.toString().length}">${cha.damage}</a>`;
    },
    cdetail: function (cha) {
      if (cha == undefined) {
        return "";
      }
      var nd = new Date();
      nd.setTime(cha.challenge_time * 1000);
      var detailstr = nd.toLocaleString("chinese", { hour12: false }) + "\n";
      detailstr += cha.cycle + "周目" + cha.boss_num + "号boss\n";
      detailstr +=
        (cha.health_ramain + cha.damage).toLocaleString() +
        "→" +
        cha.health_ramain.toLocaleString();
      if (cha.message) {
        detailstr += "\n留言：" + cha.message;
      }
      return detailstr;
    },
    handleClick(row) {
      this.activeId = row.qqid;
      this.dialogTableVisible = true;
    },
    handleTitleSelect(key, keyPath) {
      switch (key) {
        case "1":
          window.location = "../";
          break;
        case "2":
          window.location = "../subscribers/";
          break;
        case "3":
          window.location = "../progress/";
          break;
        case "4":
          window.location = "../statistics/";
          break;
        case "5":
          window.location = `../my/`;
          break;
        default:
          break;
      }
    },
  },
  template: `
    <div id="app">
    <el-page-header @back="location='..'" content></el-page-header>
    <el-menu
      :default-active="activeIndex"
      class="el-menu-demo"
      mode="horizontal"
      @select="handleTitleSelect"
    >
      <el-menu-item index="1">面板</el-menu-item>
      <el-menu-item index="2">预约</el-menu-item>
      <el-menu-item index="3">查刀</el-menu-item>
      <el-menu-item index="4">统计</el-menu-item>
      <el-menu-item index="5">我的</el-menu-item>
    </el-menu>
    <h1 style="text-align:center">伤害统计</h1>
    <span>伤害颜色：</span>
    <a class="digit6">十万</a> |
    <a class="digit7">百万</a> |
    <a class="digit8">千万</a> |
    <a class="digit9">亿</a>
    <el-table :data="statisticsData" :default-sort="{prop: 'damage', order: 'descending'}">>
      <el-table-column prop="qqid" label="QQ号" sortable></el-table-column>
      <el-table-column prop="nickname" label="昵称" sortable></el-table-column>
      <el-table-column prop="damage" label="总伤害" sortable>
        <template v-if="scope.row" slot-scope="scope">
          <a :class="'digit'+scope.row.damage.toString().length">{{scope.row.damage}}</a>
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="操作">
        <template slot-scope="scope">
          <el-button @click="handleClick(scope.row)" type="text" size="small">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="伤害详情" :visible.sync="dialogTableVisible">
      <el-table :data="gridData">
        <el-table-column prop="qqid" label="QQ号"></el-table-column>
        <el-table-column label="刀数据">
          <template v-if="scope.row" slot-scope="scope">
            <span v-html="csummary(scope.row)"></span>
            <el-popover placement="top" effect="light" trigger="hover">
              {{ cdetail(scope.row) }}
              <i class="el-icon-info" slot="reference"></i>
            </el-popover>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    </div>
  `,
});
