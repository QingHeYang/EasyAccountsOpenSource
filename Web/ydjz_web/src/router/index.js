import Vue from "vue";
import VueRouter from "vue-router";
import SettingLayout from "@/layouts/SettingLayout";
import HomeLayout from "@/layouts/HomeLayout";
import NotFound from "../views/404";
import NProgress from "nprogress";
import "nprogress/nprogress.css";
import Dashbord from "@/views/board/Dashbord";

Vue.use(VueRouter);

const routes = [
  {
    path: "*",
    component: NotFound,
  },
  {
    path: "/",
    name: "Home",
    component: HomeLayout,
    children: [
      {
        path: "/setting",
        component: () =>
          import(/* webpackChunkName: "home" */ "../views/setting/Setting.vue"),
      },
      {
        path: "/flow",
        component: () =>
          import(/* webpackChunkName: "home" */ "../views/flow/Flow.vue"),
      },
      /*{
        path: "/analysis",
        component: () =>
            import(/!* webpackChunkName: "flow" *!/ "../views/analysis/Analysis.vue"),
      },*/
      {
        path: "/screen",
        component: () =>
            import(/* webpackChunkName: "flow" */ "../views/screen/Screen.vue"),
      },
      {
        path: "/board",
       component: Dashbord,
      },
    ],
  },
  {
    path: "/account/add",
    name: "AccountAdd",
    component: () =>
      import(
        /* webpackChunkName: "account" */ "../views/setting/AccountAdd.vue"
      ),
  },
  {
    path: "/type/add",
    name: "TypeAdd",
    component: () =>
      import(/* webpackChunkName: "type" */ "../views/setting/TypeAdd.vue"),
  },
  {
    path: "/type/archive",
    name: "TypeArchive",
    component: () =>
        import(/* webpackChunkName: "type" */ "../views/setting/TypeArchive.vue"),
  },
  {
    path: "/action/add",
    name: "ActionAdd",
    component: () =>
      import(/* webpackChunkName: "action" */ "../views/setting/ActionAdd.vue"),
  },
  {
    path: "/login",
    name: "Login",
    component: () =>
      import(/* webpackChunkName: "login" */ "../views/login/Login.vue"),
  },
  {
    path: "/flow",
    name: "Flow",
    component: () =>
      import(/* webpackChunkName: "flow" */ "../views/flow/Flow.vue"),
  },
  {
    path: "/analysis",
    name: "Analysis",
    component: () =>
        import(/* webpackChunkName: "flow" */ "../views/analysis/Analysis.vue"),
  },
  {
    path: "/screen",
    name: "Screen",
    component: () =>
        import(/* webpackChunkName: "flow" */ "../views/screen/Screen.vue"),
  },
  {
    path: "/flow/add",
    name: "FlowAdd",
    component: () =>
      import(/* webpackChunkName: "flow" */ "../views/flow/FlowAdd.vue"),
  },
  {
    path: "/template/add",
    name: "TemplateAdd",
    component: () =>
      import(
        /* webpackChunkName: "template" */ "../views/setting/template/TemplateAdd.vue"
      ),
  },
  {
    path: "/template/tag",
    name: "TemplateTag",
    component: () =>
      import(
        /* webpackChunkName: "template" */ "../views/setting/template/TemplateTag.vue"
      ),
  },
  {
    path: "/setting",
    component: SettingLayout,
    children: [
      {
        path: "/setting/account",
        name: "Account",
        component: () =>
          import(
            /* webpackChunkName: "setting" */ "../views/setting/Account.vue"
          ),
      },
      {
        path: "/setting/type",
        name: "Type",
        component: () =>
          import(/* webpackChunkName: "setting" */ "../views/setting/Type.vue"),
      },
      {
        path: "/setting/action",
        name: "Action",
        component: () =>
          import(
            /* webpackChunkName: "setting" */ "../views/setting/Action.vue"
          ),
      },
      {
        path: "/setting/template",
        name: "Template",
        component: () =>
          import(
            /* webpackChunkName: "setting" */ "../views/setting/template/Template.vue"
          ),
      }
    ],
  },
];

const router = new VueRouter({
  mode: "hash",
  base: process.env.BASE_URL,
  routes,
});

router.beforeEach((to, from, next) => {
  NProgress.start();
  next();
});

router.afterEach(() => {
  NProgress.done();
});
export default router;
