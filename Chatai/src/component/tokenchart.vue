<template>
<div class="flex_colum token_count" style="gap: 1rem;">
    <span class="center_span span_count">Token 使用量统计</span>
    <div class="flex_row" style="gap: 1rem;">
        <span class="center_span" style="font-weight: bold;margin-left: auto;">日用总量 {{Util.formatTokenCount(props.tokenCount)}}</span>
          <el-date-picker
        v-model="localDate"
        type="date"
        placeholder="选择日期"
        @change="handleDateChange"
        :disabled-date="disabledDate"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD">
        </el-date-picker>
    </div>
<div class="token_chart">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
  </div>
</template>
<script setup>
    import { computed,ref,onMounted,watch } from 'vue'
    import VChart from 'vue-echarts'
    import { CanvasRenderer } from 'echarts/renderers'
    import { LineChart } from 'echarts/charts'
    import { use } from 'echarts/core'
    import { Util } from '@/shared/util'
    import {
        GridComponent,
        TooltipComponent,
        TitleComponent,
        LegendComponent
        } from 'echarts/components'
    use([
    CanvasRenderer,
    LineChart,
    GridComponent,
    TooltipComponent,
    TitleComponent,
    LegendComponent
    ])
    const emits = defineEmits(['updateUserTokens'])
    const props = defineProps({
        tokenData: {
            type:Array,
            default:[]
        },
        tokenCount: {
            type:Number,
            default:0
        },
        tokenDate:{
            type:String,
            default:''
        }
    })
    const disabledDate = (time) => {
        return time.getTime() > Date.now()
    }
    const localDate = ref('')
    watch(() => props.tokenDate, (tokenDate) => {
       localDate.value = tokenDate
    }, { immediate: true })
    onMounted(()=> {
        localDate.value = props.tokenDate
        emits('updateUserTokens',Util.getToday())
    })
    const handleDateChange = (value) => {
        emits('updateUserTokens',
        Util.formatDateWithHour(value)) //更新选中日期的统计量
    }
    const chartOption  = computed(()=>{
        return {
             tooltip: {
                trigger: 'axis',// 触发方式：当鼠标移动到坐标轴（X轴）上时触发
                formatter(params) {  // 自定义提示框的内容
                    const item = params[0] // 取第一个数据项（当只有一个数据系列时）
                    return `
                        时间：${item.axisValue}<br/>
                        Token：${Util.formatTokenCount(item.data)}
                    `
                }
            },
            grid: {
                left: '0%',      // 图表距离容器左侧的距离
                right: '6%',     // 图表距离容器右侧的距离
                bottom: '0%',   // 图表距离容器底部的距离
                top: '7%',      // 图表距离容器顶部的距离
                containLabel: true // 坐标轴标签是否自动包含在 grid 区域内
            },
            xAxis: {
                type: 'category',      // 1. 轴类型：类别轴（适用于时间、标签等离散数据）
                boundaryGap: false,    // 2. 边界间隙：从原点开始绘制，不留白
                name: '时间',          // 3. 轴名称：显示在轴下方的文字
                data: props.tokenData.map(item => item.time)  // 4. 轴数据：从原始数据中提取时间字段
            },
            yAxis: {
                type: 'value',         // 1. 轴类型：数值轴（适用于连续数据）
                name: 'Token',         // 2. 轴名称：显示在轴左侧的文字
                axisLabel: {
                    formatter: (value) => Util.formatTokenCount(value)
                }
            },
             series: [
                {
                    name: 'Token 使用量',
                    type: 'line',//折线图
                    smooth: true,//曲线平滑
                    symbol: 'circle',//数据点标记为圆形
                    symbolSize: 5,//圆点像素大小
                    data: props.tokenData.map(item => item.tokens),//Y轴数据
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
            ]
        }
    })
</script>
<style scoped>
.token_count .span_count {
     font-size: 16px;
     font-weight: 600
}
.token_count {
    width: 100%;
    height: 400px;
}

.token_chart {
    width: 100%;
    height: 360px;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>
