<template >
  <div >
    <van-nav-bar
      title="操作"
      left-arrow
      fixed placeholder
      right-text="添加操作"
      @click-left="onClickLeft"
      @click-right="onClickRight"
    >
    </van-nav-bar>
    <van-cell-group >
      <van-cell v-for="action in allActions"  :key="action.id"  is-link  @click="onDetailClick(action.id)" >
        <template #title>
          <span  class="custom-title">{{action.hname}}</span>
        </template>
        <template #label>
          <van-tag :type="action.style">{{action.handleText}}</van-tag>
          <van-tag v-show="action.exempt" style="margin-left: 10px" color="gray" plain  type="action.style">{{action.value}}</van-tag>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<script>
export default {
  name: "Action.vue",
  data() {
    return {
      allActions:[],
    };
  },
  mounted() {
    this.getAllAction();
  },
  methods: {
    onClickLeft() {
      this.$router.go(-1);
    },
    onDetailClick(id){
      this.$router.push({path:"/action/add",query:{action:id}})
    },
    onClickRight() {
      this.$router.push({path:"/action/add"})
    },
    getAllAction() {
      this.$http({
        url: "/action/getAction",
        method: "get",
      }).then((response) => {
        this.allActions = response.data.data;
        this.allActions.forEach((action)=>{
          action.value = action.exempt?"不计入总金额":""
          action.handleText = action.handle===0?"账户金额增加":action.handle===1?"账户金额减少":"账户金额不变"
          action.style =  action.handle===0?"success":action.handle===1?"danger":"primary"
        })
        console.log(this.allActions );
      }).catch((error) => {
        console.log(error);
      });
    },
  },
};
</script>

<style scoped></style>
