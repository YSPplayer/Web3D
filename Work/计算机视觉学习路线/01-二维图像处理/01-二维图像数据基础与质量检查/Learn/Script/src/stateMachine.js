const Type_AffineTransform = 0
const Type_Gamma = 1
const stateMachine = {
    //默认状态的顺序：对比度/亮度——伽马亮度
    statesDefault:[Type_AffineTransform,Type_Gamma],
    //非默认的实时状态顺序，由用户的建立的先后顺序决定
    states:[],
    /**
     * 增加状态机
     * @param {number} state 
     * @returns 
     */
    pushState(state) {
        if(stateMachine.states.includes(state)) return
        stateMachine.states.push(state)
    },
    /**
     * 重置状态机
     */
    resetState() {
        states = []
    },
    /**
     * 返回排序后的状态机
     * @returns Array
     */
    getState() {
      const setStates= new Set(stateMachine.states) 
      const statesDefaultFilter = stateMachine.statesDefault.filter(item => !setStates.has(item))  //过滤掉states中的元素
      return  [...setStates, ...statesDefaultFilter]
    }


}