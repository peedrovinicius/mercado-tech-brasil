import { BarChart, LineChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import ReactEChartsCore from 'echarts-for-react/lib/core'

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])
import type {
  MunicipalityItem,
  OccupationItem,
  TrendItem,
  UfItem,
} from '../lib/api'
import { formatCompetence, formatNumber } from '../lib/format'

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
  return <ReactEChartsCore echarts={echarts} option={option} style={{ height: 310 }} />
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
  return <ReactEChartsCore echarts={echarts} option={option} style={{ height: 310 }} />
}

export function MunicipalityChart({ items }: { items: MunicipalityItem[] }) {
  const top = items.slice(0, 12).reverse()
  const labels = top.map((item) => {
    const name = item.municipio_nome ?? item.municipio_codigo_caged
    return item.uf ? `${name} / ${item.uf}` : name
  })
  const option = {
    animationDuration: 500,
    grid: { left: 142, right: 20, top: 12, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => formatNumber(value),
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#ececf0' } },
      axisLabel: { color: '#74747c' },
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: '#4d4d54',
        width: 128,
        overflow: 'truncate',
      },
    },
    series: [
      {
        name: 'Admissões',
        type: 'bar',
        data: top.map((item) => item.admissions),
        itemStyle: { color: '#242428', borderRadius: [0, 5, 5, 0] },
        barMaxWidth: 18,
      },
    ],
  }
  return <ReactEChartsCore echarts={echarts} option={option} style={{ height: 340 }} />
}

export function TrendChart({ items }: { items: TrendItem[] }) {
  const ordered = [...items].sort((a, b) =>
    a.competence.localeCompare(b.competence),
  )
  const option = {
    animationDuration: 600,
    grid: { left: 50, right: 22, top: 28, bottom: 42 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => formatNumber(value),
    },
    legend: {
      top: 0,
      data: ['Admissões', 'Desligamentos', 'Saldo'],
      textStyle: { color: '#67676f' },
    },
    xAxis: {
      type: 'category',
      data: ordered.map((item) => formatCompetence(item.competence)),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#d9d9de' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#74747c' },
      splitLine: { lineStyle: { color: '#ececf0' } },
    },
    series: [
      {
        name: 'Admissões',
        type: 'line',
        smooth: true,
        showSymbol: ordered.length < 18,
        data: ordered.map((item) => item.admissions),
        lineStyle: { width: 2 },
      },
      {
        name: 'Desligamentos',
        type: 'line',
        smooth: true,
        showSymbol: ordered.length < 18,
        data: ordered.map((item) => item.dismissals),
        lineStyle: { width: 2 },
      },
      {
        name: 'Saldo',
        type: 'bar',
        data: ordered.map((item) => item.balance),
        barMaxWidth: 18,
      },
    ],
  }

  return <ReactEChartsCore echarts={echarts} option={option} style={{ height: 340 }} />
}

type RegionItem = {
  region: string
  admissions: number
  dismissals: number
  balance: number
}

export function ReferenceRegionChart({ items }: { items: RegionItem[] }) {
  const ordered = [...items].sort((a, b) => b.balance - a.balance)
  const option = {
    animationDuration: 600,
    grid: { left: 94, right: 20, top: 18, bottom: 20 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => new Intl.NumberFormat('pt-BR').format(value),
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#ececf0' } },
      axisLabel: { color: '#74747c' },
    },
    yAxis: {
      type: 'category',
      data: ordered.map((item) => item.region),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: '#4d4d54' },
    },
    series: [
      {
        name: 'Saldo',
        type: 'bar',
        data: ordered.map((item) => ({
          value: item.balance,
          itemStyle: {
            color: item.balance >= 0 ? '#111114' : '#a7a7ad',
            borderRadius: item.balance >= 0 ? [0, 6, 6, 0] : [6, 0, 0, 6],
          },
        })),
        barMaxWidth: 22,
      },
    ],
  }

  return <ReactEChartsCore echarts={echarts} option={option} style={{ height: 270 }} />
}
