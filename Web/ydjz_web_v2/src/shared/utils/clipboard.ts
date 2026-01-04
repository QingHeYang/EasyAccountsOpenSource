/**
 * 剪贴板工具
 * 兼容 HTTP 和 HTTPS 环境
 */

/**
 * 复制文本到剪贴板
 * 优先使用 Clipboard API，失败时降级到 execCommand
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // 方案1：使用现代 Clipboard API（需要 HTTPS 或 localhost）
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // 继续尝试降级方案
    }
  }

  // 方案2：降级到 execCommand（兼容 HTTP）
  try {
    const textArea = document.createElement('textarea')
    textArea.value = text

    // 防止滚动
    textArea.style.position = 'fixed'
    textArea.style.top = '0'
    textArea.style.left = '0'
    textArea.style.width = '2em'
    textArea.style.height = '2em'
    textArea.style.padding = '0'
    textArea.style.border = 'none'
    textArea.style.outline = 'none'
    textArea.style.boxShadow = 'none'
    textArea.style.background = 'transparent'
    // 移出可视区域
    textArea.style.opacity = '0'
    textArea.style.pointerEvents = 'none'

    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    const success = document.execCommand('copy')
    document.body.removeChild(textArea)

    return success
  } catch {
    return false
  }
}
