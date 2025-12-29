/**
 * ECharts 按需引入配置
 *
 * 支持图表类型：
 * - 饼图 (Pie)
 * - 柱状图 (Bar)
 * - 折线图 (Line)
 * - 面积图 (Line + areaStyle)
 * - 复合图 (Bar + Line)
 * - 雷达图 (Radar)
 */

import { use } from 'echarts/core'

// 渲染器
import { CanvasRenderer } from 'echarts/renderers'

// 图表类型
import { PieChart, BarChart, LineChart, RadarChart } from 'echarts/charts'

// 组件
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent,
  DatasetComponent,
  GraphicComponent,
} from 'echarts/components'

// 注册组件
use([
  // 渲染器
  CanvasRenderer,
  // 图表
  PieChart,
  BarChart,
  LineChart,
  RadarChart,
  // 组件
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent,
  DatasetComponent,
  GraphicComponent,
])

// 导出 echarts 核心，供直接使用
export * from 'echarts/core'

// 导出类型
export type { EChartsOption } from 'echarts'
