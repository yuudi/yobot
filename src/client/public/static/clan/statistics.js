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
});
