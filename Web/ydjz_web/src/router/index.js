import {createRouter, createWebHistory} from "vue-router";
import SettingLayout from "@/layouts/SettingLayout";
import HomeLayout from "@/layouts/HomeLayout";
import NotFound from "../views/404";
import NProgress from "nprogress";
import "nprogress/nprogress.css";
import Dashbord from "@/views/board/Dashbord";


const routes = [
  {
    path: "/:pathMatch(.*)*",
    component: NotFound,
  },
  {
    path: "/",
    redirect: "/board" // 访问 / 时，自动重定向到 /board
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
      {
        path: "/analysisV2",
        component: () =>
            import(/* webpackChunkName: "flow" */ "../views/analysis/AnalysisV2.vue"),
      },
/*      {
        path: "/screen",
        component: () =>
            import(/!* webpackChunkName: "flow" *!/ "../views/screen/Screen.vue"),
      },*/
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
    path: '/auth',
    name: 'Auth',
    component: () => import(/* webpackChunkName: "auth" */ "../views/login/LoginRegister.vue"),
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
        import(/* webpackChunkName: "analysis" */ "../views/analysis/Analysis.vue"),
  },
  {
    path: "/analysisV2",
    name: "AnalysisV2",
    component: () =>
        import(/* webpackChunkName: "analysis" */ "../views/analysis/AnalysisV2.vue"),
  },
  {
    path: "/analysis/type",
    name: "AnalysisType",
    component: () =>
        import(/* webpackChunkName: "analysis" */ "../views/analysis/type/AnalysisType.vue"),
  },
  {
    path: "/verify",
    name: "Verify",
    component: () =>
        import(/* webpackChunkName: "verify" */ "../views/Verify.vue"),
  },
  {
    path: "/screen",
    name: "Screen",
    component: () =>
        import(/* webpackChunkName: "screen" */ "../views/screen/Screen.vue"),
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
      },
      {
        path: "/setting/config",
        name: "Config",
        component: () =>
          import(
            /* webpackChunkName: "setting" */ "../views/setting/Config.vue"
          ),
      }
    ],
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
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
