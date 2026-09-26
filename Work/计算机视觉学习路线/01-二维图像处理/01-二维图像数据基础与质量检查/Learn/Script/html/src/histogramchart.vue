<template>
<div class="histogram_chart">
    <v-chart class="chart" :option="chartOption" autoresize />
</div>

</template>
<script setup>
    import { computed,ref,onMounted,watch } from 'vue'
    import VChart from 'vue-echarts'
    import { use } from 'echarts/core'
    import { CanvasRenderer } from 'echarts/renderers'
    import { LineChart } from 'echarts/charts'
    import { GridComponent } from 'echarts/components'
    use([CanvasRenderer, LineChart, GridComponent])
    const props = defineProps({
        imageDatas: {
            type:Array,
            default:[]
        }
    })
    const chartOption  = computed(()=>{
        return {
            grid: {
                left: '0%',      // 图表距离容器左侧的距离
                right: '15%',     // 图表距离容器右侧的距离
                bottom: '0%',   // 图表距离容器底部的距离
                top: '7%',      // 图表距离容器顶部的距离
                containLabel: true // 坐标轴标签是否自动包含在 grid 区域内
            },
            xAxis: {
                type: 'category',      // 1. 轴类型：类别轴（适用于时间、标签等离散数据）
                 min: 0,               // 最小值 0
                 max: 255,             // 最大值 255（8位图）
                 name: '像素值',
                 boundaryGap: false,   // 数值轴通常不需要，但可保留
                 interval: 1           // 可选：每个刻度间隔 1
            },
            yAxis: {
                type: 'value',         // 1. 轴类型：数值轴（适用于连续数据）
                name: '像素数量',         // 2. 轴名称：显示在轴左侧的文字
            },
            series:[
                {
                    name: '直方图统计',
                    type: 'line',//折线图
                    smooth: true,//曲线平滑
                    symbol: 'circle',//数据点标记为圆形
                    symbolSize: 5,//圆点像素大小
                    data: props.imageDatas,//Y轴数据
                    lineStyle: {
                    width: 3,
                    color: '#5EAAF9' //线条样式
                    },
                    itemStyle: {
                    color: '#409EFF' //数据点样式
                    },
                    areaStyle: {
                    color: 'rgba(64, 158, 255, 0.15)' //数据中心填充色
                    }

                }
            ],
             animationDurationUpdate: 0   // 全局关掉更新动画
        }
    })

</script>

<style scoped>
.histogram_chart {
    width: 700px;
    height: 500px;
}
</style>