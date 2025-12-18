/**
 * 金额处理工具函数
 * 解决JavaScript浮点数精度问题
 */

/**
 * 格式化金额为2位小数
 * @param {number|string} money 金额
 * @returns {string} 格式化后的金额字符串
 */
export function formatMoney(money) {
  const num = parseFloat(money || 0)
  if (isNaN(num)) {
    return '0.00'
  }
  return num.toFixed(2)
}

/**
 * 金额相加（避免精度问题）
 * @param {...(number|string)} moneys 多个金额
 * @returns {string} 总金额（2位小数）
 */
export function addMoney(...moneys) {
  // 转换为分（整数）进行计算
  const totalCents = moneys.reduce((sum, money) => {
    const cents = Math.round(parseFloat(money || 0) * 100)
    return sum + cents
  }, 0)
  
  // 转回元并格式化
  return (totalCents / 100).toFixed(2)
}

/**
 * 金额相减（避免精度问题）
 * @param {number|string} money1 被减数
 * @param {number|string} money2 减数
 * @returns {string} 差额（2位小数）
 */
export function subtractMoney(money1, money2) {
  const cents1 = Math.round(parseFloat(money1 || 0) * 100)
  const cents2 = Math.round(parseFloat(money2 || 0) * 100)
  return ((cents1 - cents2) / 100).toFixed(2)
}

/**
 * 验证金额格式是否有效
 * @param {string} money 金额字符串
 * @returns {boolean} 是否有效
 */
export function isValidMoney(money) {
  if (!money || money === '') {
    return false
  }
  
  const num = parseFloat(money)
  if (isNaN(num) || num < 0) {
    return false
  }
  
  // 检查小数位数不超过2位
  const parts = money.toString().split('.')
  if (parts.length > 1 && parts[1].length > 2) {
    return false
  }
  
  return true
}

/**
 * 金额转换为分（整数）
 * @param {number|string} money 金额（元）
 * @returns {number} 金额（分）
 */
export function toCents(money) {
  return Math.round(parseFloat(money || 0) * 100)
}

/**
 * 分转换为金额（元）
 * @param {number} cents 金额（分）
 * @returns {string} 金额（元，2位小数）
 */
export function fromCents(cents) {
  return (cents / 100).toFixed(2)
}