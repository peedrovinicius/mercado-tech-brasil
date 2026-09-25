import ReactECharts from 'echarts-for-react'
import type { OccupationItem, UfItem } from '../lib/api'

export function UfChart({ items }: { items: UfItem[] }) {
  const top = items.slice(0, 10)
  const option = {
    animationDuration: 500,
    grid: { left: 44, right: 16, top: 18, bottom: 32 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: top.map((item) => item.uf),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#d9d9de' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#696970' },
      splitLine: { lineStyle: { color: '#ececf0' } },
    },
    series: [
      {
        name: 'Admissões',
        type: 'bar',
        data: top.map((item) => item.admissions),
        itemStyle: { color: '#111114', borderRadius: [5, 5, 0, 0] },
        barMaxWidth: 30,
      },
    ],
  }
  return <ReactECharts option={option} style={{ height: 310 }} />
}

export function OccupationChart({ items }: { items: OccupationItem[] }) {
  const top = items.slice(0, 8).reverse()
  const option = {
    animationDuration: 500,
    grid: { left: 88, right: 16, top: 8, bottom: 22 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#ececf0' } },
    },
    yAxis: {
      type: 'category',
      data: top.map((item) => item.cbo_codigo),
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        name: 'Saldo',
        type: 'bar',
        data: top.map((item) => item.balance),
        itemStyle: { color: '#3b3b42', borderRadius: [0, 5, 5, 0] },
        barMaxWidth: 18,
      },
    ],
  }
  return <ReactECharts option={option} style={{ height: 310 }} />
}
