import { BarChart, LineChart } from 'echarts/charts'
import {
  AriaComponent,
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
  AriaComponent,
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
import { formatCompetence, formatNumber, formatRate } from '../lib/format'

const axisLabelColor = '#686870'
const categoryLabelColor = '#44444b'
const gridLineColor = '#ececf0'
const axisLineColor = '#d9d9de'

const numberTooltip = {
  trigger: 'axis',
  confine: true,
  valueFormatter: (value: number) => formatNumber(value),
}

const valueAxis = {
  type: 'value',
  axisLabel: {
    color: axisLabelColor,
    formatter: (value: number) => formatNumber(value),
  },
  splitLine: { lineStyle: { color: gridLineColor } },
}

export function UfChart({ items }: { items: UfItem[] }) {
  const top = items.slice(0, 10)
  const option = {
    animationDuration: 450,
    aria: { show: true },
    grid: { left: 54, right: 14, top: 18, bottom: 34, containLabel: true },
    tooltip: {
      ...numberTooltip,
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      type: 'category',
      data: top.map((item) => item.uf),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisLabel: { color: categoryLabelColor },
    },
    yAxis: valueAxis,
    series: [
      {
        name: 'Admissões',
        type: 'bar',
        data: top.map((item) => item.admissions),
        itemStyle: { color: '#111114', borderRadius: [5, 5, 0, 0] },
        barMaxWidth: 30,
      },
    ],
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 8, right: 8, top: 18, bottom: 28, containLabel: true },
          xAxis: { axisLabel: { fontSize: 10, interval: 0 } },
          yAxis: { axisLabel: { fontSize: 10 } },
          series: [{ barMaxWidth: 22 }],
        },
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 310 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export function OccupationChart({ items }: { items: OccupationItem[] }) {
  const top = items.slice(0, 8).reverse()
  const option = {
    animationDuration: 450,
    aria: { show: true },
    grid: { left: 92, right: 14, top: 8, bottom: 22, containLabel: true },
    tooltip: {
      ...numberTooltip,
      axisPointer: { type: 'shadow' },
    },
    xAxis: valueAxis,
    yAxis: {
      type: 'category',
      data: top.map((item) => item.cbo_codigo),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: categoryLabelColor },
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
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 6, right: 8, top: 8, bottom: 18, containLabel: true },
          xAxis: { axisLabel: { fontSize: 10 } },
          yAxis: { axisLabel: { fontSize: 10 } },
        },
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 310 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export function MunicipalityChart({
  items,
  metric = 'admissions',
}: {
  items: MunicipalityItem[]
  metric?: 'admissions' | 'admissions_per_100k'
}) {
  const normalized = metric === 'admissions_per_100k'
  const top = items.slice(0, 12).reverse()
  const labels = top.map((item) => {
    const name = item.municipio_nome ?? item.municipio_codigo_caged
    return item.uf ? `${name} / ${item.uf}` : name
  })
  const values = top.map((item) =>
    normalized ? (item.admissions_per_100k ?? 0) : item.admissions,
  )
  const formatter = (value: number) =>
    normalized ? formatRate(value) : formatNumber(value)

  const option = {
    animationDuration: 450,
    aria: { show: true },
    grid: { left: 150, right: 16, top: 12, bottom: 24, containLabel: true },
    tooltip: {
      trigger: 'axis',
      confine: true,
      valueFormatter: formatter,
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      ...valueAxis,
      axisLabel: {
        color: axisLabelColor,
        formatter,
      },
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: categoryLabelColor,
        width: 128,
        overflow: 'truncate',
      },
    },
    series: [
      {
        name: normalized ? 'Admissões por 100 mil' : 'Admissões',
        type: 'bar',
        data: values,
        itemStyle: {
          color: normalized ? '#2459ff' : '#242428',
          borderRadius: [0, 5, 5, 0],
        },
        barMaxWidth: 18,
      },
    ],
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 6, right: 8, top: 12, bottom: 20, containLabel: true },
          xAxis: { axisLabel: { fontSize: 10, formatter } },
          yAxis: {
            axisLabel: {
              width: 92,
              fontSize: 10,
              overflow: 'truncate',
            },
          },
        },
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 350 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export function TrendChart({ items }: { items: TrendItem[] }) {
  const ordered = [...items].sort((a, b) =>
    a.competence.localeCompare(b.competence),
  )
  const option = {
    animationDuration: 500,
    aria: { show: true },
    grid: { left: 52, right: 18, top: 42, bottom: 40, containLabel: true },
    tooltip: {
      ...numberTooltip,
      axisPointer: { type: 'line' },
    },
    legend: {
      top: 0,
      data: ['Admissões', 'Desligamentos', 'Saldo'],
      itemWidth: 14,
      itemHeight: 8,
      textStyle: { color: '#67676f', fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: ordered.map((item) => formatCompetence(item.competence)),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisLabel: { color: categoryLabelColor },
    },
    yAxis: valueAxis,
    series: [
      {
        name: 'Admissões',
        type: 'line',
        smooth: true,
        showSymbol: ordered.length < 18,
        symbolSize: 6,
        data: ordered.map((item) => item.admissions),
        lineStyle: { width: 2 },
        emphasis: { focus: 'series' },
      },
      {
        name: 'Desligamentos',
        type: 'line',
        smooth: true,
        showSymbol: ordered.length < 18,
        symbolSize: 6,
        data: ordered.map((item) => item.dismissals),
        lineStyle: { width: 2 },
        emphasis: { focus: 'series' },
      },
      {
        name: 'Saldo',
        type: 'bar',
        data: ordered.map((item) => item.balance),
        barMaxWidth: 16,
        emphasis: { focus: 'series' },
      },
    ],
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 6, right: 8, top: 58, bottom: 28, containLabel: true },
          legend: {
            top: 0,
            left: 0,
            right: 0,
            itemGap: 10,
            textStyle: { fontSize: 10 },
          },
          xAxis: { axisLabel: { fontSize: 10 } },
          yAxis: { axisLabel: { fontSize: 10 } },
        },
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 350 }}
      opts={{ renderer: 'canvas' }}
    />
  )
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
    animationDuration: 450,
    aria: { show: true },
    grid: { left: 96, right: 16, top: 18, bottom: 20, containLabel: true },
    tooltip: {
      ...numberTooltip,
      axisPointer: { type: 'shadow' },
    },
    xAxis: valueAxis,
    yAxis: {
      type: 'category',
      data: ordered.map((item) => item.region),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: categoryLabelColor },
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
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 6, right: 8, top: 16, bottom: 16, containLabel: true },
          xAxis: { axisLabel: { fontSize: 10 } },
          yAxis: { axisLabel: { fontSize: 10 } },
        },
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 270 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}
